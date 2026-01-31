"""
BaseProcessor - Abstract base class for processor implementations.

Developers implement this class to create their processor applications.
The SDK handles all lifecycle, state management, and health concerns.

SDK v2.1 Auto-Features:
1. Auto-Initialization - All components created from config:
   - Circuit breakers (self.circuit_breakers)
   - Error classifier (self.error_classifier)
   - OpenTelemetry (self.otel)
   - Request tracker (self.request_tracker)
   - Request ID middleware (self.request_id_middleware)
   - Connection tracker (self.connection_tracker)

2. Auto-Instrumentation - All handler methods automatically get:
   - Request ID generation
   - Request tracking
   - OpenTelemetry spans
   - Error classification
   - No decorators needed!
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncIterator, Dict, Any, Optional

from dory.decorators import get_stateful_vars, set_stateful_vars
from dory.core.meta import AutoInstrumentMeta

if TYPE_CHECKING:
    from dory.core.context import ExecutionContext

logger = logging.getLogger(__name__)


class BaseProcessor(ABC, metaclass=AutoInstrumentMeta):
    """
    Abstract base class for processor implementations.

    Required method:
    - run(): Main processing loop

    Optional methods (have sensible defaults):
    - startup(): Initialize resources (default: no-op)
    - shutdown(): Cleanup resources (default: no-op)
    - get_state(): Return state dict (default: returns @stateful vars or {})
    - restore_state(): Restore state (default: restores @stateful vars)

    Optional fault handling hooks:
    - on_state_restore_failed(): Handle state restore errors
    - on_rapid_restart_detected(): Handle restart loop
    - on_health_check_failed(): Handle health check errors
    - reset_caches(): Clean caches during golden image reset

    Usage:
        # Minimal implementation (just run method)
        class MyProcessor(BaseProcessor):
            counter = stateful(0)

            async def run(self):
                async for _ in self.run_loop(interval=1):
                    self.counter += 1

        # Full implementation
        class MyProcessor(BaseProcessor):
            async def startup(self):
                self.model = load_model()

            async def run(self):
                while not self.context.is_shutdown_requested():
                    process()

            async def shutdown(self):
                self.model.close()

            def get_state(self):
                return {"processed": self.count}

            async def restore_state(self, state):
                self.count = state.get("processed", 0)
    """

    # Optional: Define state schema for validation
    # Schema example: {'processed_count': int, 'last_frame_id': int}
    state_schema: dict[str, type] | None = None

    # Context is auto-injected by DoryApp (no need to accept in __init__)
    context: "ExecutionContext"

    def __init__(self, context: "ExecutionContext | None" = None):
        """
        Initialize processor with auto-initialization of SDK components.

        Args:
            context: ExecutionContext (optional - will be auto-injected if not provided)

        Auto-Initialized Components (SDK v2.1):
            - self.error_classifier: Automatic error classification
            - self.circuit_breakers: Dict of circuit breakers (database, external_api, cache)
            - self.otel: OpenTelemetry manager (if enabled in config)
            - self.request_tracker: Request tracking middleware (if enabled)
            - self.request_id_middleware: Request ID generation (if enabled)
            - self.connection_tracker: Connection lifecycle tracking (if enabled)

        Note:
            You can override __init__ and call super().__init__(context) to get
            auto-initialization, or skip super() call to manually initialize.
        """
        if context is not None:
            self.context = context

            # Auto-initialize SDK components if context is available
            self._auto_initialize_components()

    # =========================================================================
    # Required Method
    # =========================================================================

    @abstractmethod
    async def run(self) -> None:
        """
        Main processing loop.

        Called after startup() and restore_state(). Must check
        context.is_shutdown_requested() periodically to exit gracefully.

        You can use self.run_loop() helper for cleaner code:

            async def run(self):
                async for _ in self.run_loop(interval=1):
                    self.counter += 1

        Or traditional while loop:

            async def run(self):
                while not self.context.is_shutdown_requested():
                    self.counter += 1
                    await asyncio.sleep(1)

        Raises:
            Any exception will cause pod crash
        """
        raise NotImplementedError

    # =========================================================================
    # Optional Lifecycle Methods (Override if needed)
    # =========================================================================

    async def startup(self) -> None:
        """
        Initialize processor resources (optional).

        Called once at pod startup after __init__ but before run().
        Override to load models, open connections, etc.

        Default: No-op
        """
        pass

    async def shutdown(self) -> None:
        """
        Cleanup processor resources (optional).

        Called on graceful shutdown (SIGTERM). Has max timeout
        (configurable via DORY_SHUTDOWN_TIMEOUT_SEC, default 30s).
        Override to close connections, flush buffers, etc.

        Default: No-op
        """
        pass

    def get_state(self) -> dict:
        """
        Return state to migrate to next pod (optional).

        Called during migration (must be fast, <1s). State must be
        JSON-serializable.

        Default: Returns all @stateful decorated attributes, or {} if none.

        Override for custom state:
            def get_state(self):
                return {"counter": self.counter, "data": self.data}
        """
        # Auto-collect @stateful decorated attributes
        stateful_state = get_stateful_vars(self)
        if stateful_state:
            return stateful_state
        return {}

    async def restore_state(self, state: dict) -> None:
        """
        Restore state from previous pod (optional).

        Called after startup() but before run() if state exists.

        Default: Restores all @stateful decorated attributes from state.

        Override for custom restoration:
            async def restore_state(self, state):
                self.counter = state.get("counter", 0)
        """
        # Auto-restore @stateful decorated attributes
        set_stateful_vars(self, state)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def run_loop(
        self,
        interval: float = 1.0,
        check_migration: bool = True,
    ) -> AsyncIterator[int]:
        """
        Async iterator that yields until shutdown is requested.

        Simplifies the common pattern of checking shutdown in a loop.

        Args:
            interval: Sleep interval between iterations (seconds)
            check_migration: If True, also yields when migration is imminent

        Yields:
            Iteration count (0, 1, 2, ...)

        Usage:
            async def run(self):
                async for i in self.run_loop(interval=1):
                    self.counter += 1
                    print(f"Iteration {i}")

            # Equivalent to:
            async def run(self):
                i = 0
                while not self.context.is_shutdown_requested():
                    self.counter += 1
                    print(f"Iteration {i}")
                    i += 1
                    await asyncio.sleep(1)
        """
        iteration = 0
        while not self.context.is_shutdown_requested():
            yield iteration
            iteration += 1

            # Check if migration is imminent
            if check_migration and self.context.is_migration_imminent():
                self.context.logger().info(
                    f"Migration imminent, completing iteration {iteration}"
                )

            await asyncio.sleep(interval)

    def is_shutting_down(self) -> bool:
        """
        Convenience method to check if shutdown is requested.

        Returns:
            True if shutdown has been requested
        """
        return self.context.is_shutdown_requested()

    # =========================================================================
    # Optional Fault Handling Hooks
    # =========================================================================

    async def on_state_restore_failed(self, error: Exception) -> bool:
        """
        Called if state restore fails.

        Override to attempt recovery (e.g., fetch from external backup).
        Return True to start with golden image, False to exit and crash.

        Args:
            error: Exception from restore_state() or validation

        Returns:
            True to continue with golden image, False to exit
        """
        return True  # Default: continue with golden image

    async def on_rapid_restart_detected(self, restart_count: int) -> bool:
        """
        Called if restart loop detected (3+ restarts in 5 minutes).

        Override to attempt recovery (e.g., reinitialize state, reset
        connections). Return True to continue, False to trigger golden reset.

        Args:
            restart_count: Number of restarts detected

        Returns:
            True to continue, False to force golden reset
        """
        return True  # Default: continue (SDK will start golden)

    async def on_health_check_failed(self, error: Exception) -> bool:
        """
        Called if health check fails.

        Override to attempt recovery (e.g., reconnect to external services).
        Return True to retry health check, False to fail.

        Args:
            error: Exception from health check

        Returns:
            True to retry, False to fail
        """
        return False  # Default: fail health check

    def reset_caches(self) -> None:
        """
        Called during golden image reset.

        Override to clear any in-memory caches, buffers, or temporary
        state that should not persist through a golden reset.
        """
        pass  # Default: no caches to reset

    # =========================================================================
    # Auto-Initialization (SDK v2.1)
    # =========================================================================

    def _auto_initialize_components(self) -> None:
        """
        Auto-initialize SDK components from configuration.

        This method is called automatically during __init__ if context is available.
        Components are only initialized if enabled in configuration.

        Initialized components:
        - error_classifier: Always available
        - circuit_breakers: Dict of circuit breakers
        - otel: OpenTelemetry (if enabled)
        - request_tracker: Request tracking (if enabled)
        - request_id_middleware: Request ID generation (if enabled)
        - connection_tracker: Connection tracking (if enabled)
        """
        if not hasattr(self, "context") or self.context is None:
            logger.debug("Context not available, skipping auto-initialization")
            return

        config = self.context.config

        # 1. Error Classifier (always available)
        self._init_error_classifier()

        # 2. Circuit Breakers (auto-created from config)
        self._init_circuit_breakers(config)

        # 3. OpenTelemetry (auto-initialized if enabled)
        self._init_opentelemetry(config)

        # 4. Request Tracking (auto-initialized if enabled)
        self._init_request_tracking(config)

        # 5. Request ID Middleware (auto-initialized if enabled)
        self._init_request_id(config)

        # 6. Connection Tracker (auto-initialized if enabled)
        self._init_connection_tracking(config)

        logger.debug("Auto-initialization complete")

    def _init_error_classifier(self) -> None:
        """Initialize error classifier (always available)."""
        try:
            from dory.errors import ErrorClassifier

            self.error_classifier = ErrorClassifier()
            logger.debug("Initialized error classifier")
        except ImportError:
            logger.debug("Error classifier not available (dory.errors not installed)")
            self.error_classifier = None

    def _init_circuit_breakers(self, config: Any) -> None:
        """Auto-initialize circuit breakers from configuration."""
        self.circuit_breakers: Dict[str, Any] = {}

        try:
            from dory.resilience import CircuitBreaker
        except ImportError:
            logger.debug("Circuit breakers not available (dory.resilience not installed)")
            return

        # Get circuit breaker config
        cb_config_dict = {}
        if hasattr(config, "__dict__"):
            config_dict = config.__dict__
        elif hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        else:
            config_dict = {}

        # Try to get from nested config structure
        if "circuit_breaker" in config_dict:
            cb_config_dict = config_dict["circuit_breaker"]
        elif hasattr(config, "get"):
            cb_config_dict = config.get("circuit_breaker", {})

        # Check if circuit breakers are enabled
        if isinstance(cb_config_dict, dict) and not cb_config_dict.get("enabled", True):
            logger.info("Circuit breakers disabled in configuration")
            return

        # Get default parameters
        if isinstance(cb_config_dict, dict):
            failure_threshold = cb_config_dict.get("failure_threshold", 5)
            success_threshold = cb_config_dict.get("success_threshold", 2)
            timeout_seconds = cb_config_dict.get("timeout", 30.0)
            half_open_max_calls = cb_config_dict.get("half_open_max_calls", 3)
        else:
            failure_threshold = 5
            success_threshold = 2
            timeout_seconds = 30.0
            half_open_max_calls = 3

        # Create default circuit breakers for common services
        common_names = ["database", "external_api", "cache"]
        for name in common_names:
            self.circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds,
                half_open_max_calls=half_open_max_calls,
            )
            logger.debug(f"Created circuit breaker: {name}")

        # Create custom circuit breakers from config
        if isinstance(cb_config_dict, dict) and "breakers" in cb_config_dict:
            custom_breakers = cb_config_dict["breakers"]
            for name, breaker_config in custom_breakers.items():
                self.circuit_breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=breaker_config.get("failure_threshold", failure_threshold),
                    success_threshold=breaker_config.get("success_threshold", success_threshold),
                    timeout_seconds=breaker_config.get("timeout", timeout_seconds),
                    half_open_max_calls=breaker_config.get("half_open_max_calls", half_open_max_calls),
                )
                logger.debug(f"Created custom circuit breaker: {name}")

        logger.info(f"Initialized {len(self.circuit_breakers)} circuit breakers")

    def _init_opentelemetry(self, config: Any) -> None:
        """Auto-initialize OpenTelemetry if enabled."""
        self.otel: Optional[Any] = None

        # Get config dict
        if hasattr(config, "__dict__"):
            config_dict = config.__dict__
        elif hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        else:
            config_dict = {}

        # Get OpenTelemetry config
        otel_config = {}
        if "opentelemetry" in config_dict:
            otel_config = config_dict["opentelemetry"]
        elif hasattr(config, "get"):
            otel_config = config.get("opentelemetry", {})

        # Check if OpenTelemetry is enabled
        if isinstance(otel_config, dict) and not otel_config.get("enabled", True):
            logger.info("OpenTelemetry disabled in configuration")
            return

        try:
            from dory.monitoring import OpenTelemetryManager

            # Get app config for service name/version
            app_config = {}
            if "app" in config_dict:
                app_config = config_dict["app"]
            elif hasattr(config, "get"):
                app_config = config.get("app", {})

            # Initialize OpenTelemetry
            if isinstance(otel_config, dict):
                self.otel = OpenTelemetryManager(
                    service_name=otel_config.get("service_name", app_config.get("name", "dory-app")),
                    service_version=otel_config.get(
                        "service_version", app_config.get("version", "1.0.0")
                    ),
                    environment=otel_config.get("environment", app_config.get("environment", "production")),
                    console_export=otel_config.get("otlp", {}).get("console_export", True),
                    otlp_endpoint=otel_config.get("otlp", {}).get("endpoint"),
                )
            else:
                self.otel = OpenTelemetryManager(
                    service_name=app_config.get("name", "dory-app"),
                    service_version=app_config.get("version", "1.0.0"),
                    environment=app_config.get("environment", "production"),
                )

            self.otel.initialize()
            logger.info("OpenTelemetry initialized")

        except ImportError:
            logger.debug(
                "OpenTelemetry not available. Install with: pip install dory-sdk[tracing]"
            )
            self.otel = None
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")
            self.otel = None

    def _init_request_tracking(self, config: Any) -> None:
        """Auto-initialize request tracking if enabled."""
        self.request_tracker: Optional[Any] = None

        # Get config dict
        if hasattr(config, "__dict__"):
            config_dict = config.__dict__
        elif hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        else:
            config_dict = {}

        # Get bookkeeping config
        bookkeeping_config = {}
        if "bookkeeping" in config_dict:
            bookkeeping_config = config_dict["bookkeeping"]
        elif hasattr(config, "get"):
            bookkeeping_config = config.get("bookkeeping", {})

        # Get request tracking config
        if isinstance(bookkeeping_config, dict):
            tracking_config = bookkeeping_config.get("request_tracking", {})
        else:
            tracking_config = {}

        # Check if request tracking is enabled
        if isinstance(tracking_config, dict) and not tracking_config.get("enabled", True):
            logger.info("Request tracking disabled in configuration")
            return

        try:
            from dory.middleware import RequestTracker

            if isinstance(tracking_config, dict):
                self.request_tracker = RequestTracker(
                    max_concurrent=tracking_config.get("max_concurrent", 100),
                    timeout=tracking_config.get("timeout", 30.0),
                )
            else:
                self.request_tracker = RequestTracker()

            logger.info("Request tracking initialized")

        except ImportError:
            logger.debug("Request tracking not available (dory.middleware not installed)")
            self.request_tracker = None
        except Exception as e:
            logger.warning(f"Failed to initialize request tracking: {e}")
            self.request_tracker = None

    def _init_request_id(self, config: Any) -> None:
        """Auto-initialize request ID middleware if enabled."""
        self.request_id_middleware: Optional[Any] = None

        # Get config dict
        if hasattr(config, "__dict__"):
            config_dict = config.__dict__
        elif hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        else:
            config_dict = {}

        # Get bookkeeping config
        bookkeeping_config = {}
        if "bookkeeping" in config_dict:
            bookkeeping_config = config_dict["bookkeeping"]
        elif hasattr(config, "get"):
            bookkeeping_config = config.get("bookkeeping", {})

        # Get request ID config
        if isinstance(bookkeeping_config, dict):
            request_id_config = bookkeeping_config.get("request_id", {})
        else:
            request_id_config = {}

        # Check if request ID is enabled
        if isinstance(request_id_config, dict) and not request_id_config.get("enabled", True):
            logger.info("Request ID generation disabled in configuration")
            return

        try:
            from dory.middleware import RequestIdMiddleware

            if isinstance(request_id_config, dict):
                self.request_id_middleware = RequestIdMiddleware(
                    format=request_id_config.get("format", "uuid4"),
                    add_to_response=request_id_config.get("add_to_response", True),
                )
            else:
                self.request_id_middleware = RequestIdMiddleware()

            logger.info("Request ID middleware initialized")

        except ImportError:
            logger.debug("Request ID middleware not available (dory.middleware not installed)")
            self.request_id_middleware = None
        except Exception as e:
            logger.warning(f"Failed to initialize request ID middleware: {e}")
            self.request_id_middleware = None

    def _init_connection_tracking(self, config: Any) -> None:
        """Auto-initialize connection tracking if enabled."""
        self.connection_tracker: Optional[Any] = None

        # Get config dict
        if hasattr(config, "__dict__"):
            config_dict = config.__dict__
        elif hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        else:
            config_dict = {}

        # Get bookkeeping config
        bookkeeping_config = {}
        if "bookkeeping" in config_dict:
            bookkeeping_config = config_dict["bookkeeping"]
        elif hasattr(config, "get"):
            bookkeeping_config = config.get("bookkeeping", {})

        # Get connection tracking config
        if isinstance(bookkeeping_config, dict):
            connection_config = bookkeeping_config.get("connection_tracking", {})
        else:
            connection_config = {}

        # Check if connection tracking is enabled
        if isinstance(connection_config, dict) and not connection_config.get("enabled", True):
            logger.info("Connection tracking disabled in configuration")
            return

        try:
            from dory.middleware import ConnectionTracker

            self.connection_tracker = ConnectionTracker()
            logger.info("Connection tracking initialized")

        except ImportError:
            logger.debug("Connection tracking not available (dory.middleware not installed)")
            self.connection_tracker = None
        except Exception as e:
            logger.warning(f"Failed to initialize connection tracking: {e}")
            self.connection_tracker = None
