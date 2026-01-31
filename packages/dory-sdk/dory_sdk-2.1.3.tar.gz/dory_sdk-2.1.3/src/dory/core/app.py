"""
DoryApp - Main entry point for processor applications.

Orchestrates the entire processor lifecycle including:
- Configuration loading
- Health server startup
- Signal handling
- State restoration
- Processor lifecycle management
- Graceful shutdown
"""

import asyncio
import logging
import sys
from typing import Type

from dory.core.processor import BaseProcessor
from dory.core.context import ExecutionContext
from dory.core.lifecycle import LifecycleManager
from dory.core.signals import SignalHandler
from dory.config.loader import ConfigLoader
from dory.config.schema import DoryConfig
from dory.health.server import HealthServer
from dory.migration.state_manager import StateManager
from dory.recovery.recovery_decision import RecoveryDecisionMaker
from dory.recovery.restart_detector import RestartDetector
from dory.logging.logger import setup_logging
from dory.metrics.collector import MetricsCollector
from dory.utils.errors import DoryStartupError, DoryStateError

logger = logging.getLogger(__name__)


class DoryApp:
    """
    Main entry point for Dory processor applications.

    Usage:
        from dory import DoryApp, BaseProcessor

        class MyProcessor(BaseProcessor):
            ...

        if __name__ == '__main__':
            DoryApp().run(MyProcessor)
    """

    def __init__(
        self,
        config_file: str | None = None,
        log_level: str | None = None,
    ):
        """
        Initialize DoryApp.

        Args:
            config_file: Optional path to YAML config file
            log_level: Optional log level override
        """
        self._config_file = config_file
        self._log_level_override = log_level

        # Components (initialized in _initialize)
        self._config: DoryConfig | None = None
        self._context: ExecutionContext | None = None
        self._processor: BaseProcessor | None = None
        self._lifecycle: LifecycleManager | None = None
        self._signals: SignalHandler | None = None
        self._health_server: HealthServer | None = None
        self._state_manager: StateManager | None = None
        self._metrics: MetricsCollector | None = None
        self._restart_detector: RestartDetector | None = None
        self._recovery_decision: RecoveryDecisionMaker | None = None

    def run(self, processor_class: Type[BaseProcessor]) -> None:
        """
        Run the processor application.

        This is the main entry point that blocks until shutdown.

        Args:
            processor_class: Class implementing BaseProcessor
        """
        try:
            asyncio.run(self._run_async(processor_class))
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)

    async def _run_async(self, processor_class: Type[BaseProcessor]) -> None:
        """
        Async implementation of the run loop.

        Args:
            processor_class: Class implementing BaseProcessor
        """
        exit_code = 0

        try:
            # Phase 1: Initialize SDK components
            await self._initialize(processor_class)

            # Phase 2: Start health server
            await self._start_health_server()

            # Phase 3: Run processor lifecycle
            await self._run_processor_lifecycle()

        except DoryStartupError as e:
            logger.error(f"Startup failed: {e}")
            exit_code = 1
            raise

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            exit_code = 1
            raise

        finally:
            # Phase 4: Cleanup
            await self._cleanup()
            logger.info(f"DoryApp exiting with code {exit_code}")

    async def _initialize(self, processor_class: Type[BaseProcessor]) -> None:
        """Initialize all SDK components."""
        logger.debug("Initializing DoryApp components")

        # Load configuration
        config_loader = ConfigLoader(config_file=self._config_file)
        self._config = config_loader.load()

        # Apply log level override if provided
        if self._log_level_override:
            self._config.log_level = self._log_level_override

        # Setup logging
        setup_logging(
            level=self._config.log_level,
            format=self._config.log_format,
        )

        logger.info("Dory SDK initializing", extra={
            "version": "1.0.0",
            "config": self._config.model_dump(),
        })

        # Create execution context from environment
        self._context = ExecutionContext.from_environment()

        # Initialize components
        self._lifecycle = LifecycleManager()
        self._signals = SignalHandler()
        self._state_manager = StateManager(
            backend=self._config.state_backend,
            config=self._config,
        )
        self._metrics = MetricsCollector()
        self._restart_detector = RestartDetector()
        self._recovery_decision = RecoveryDecisionMaker()

        # Detect restart count
        restart_info = await self._restart_detector.detect()
        self._context.set_attempt_number(restart_info.restart_count)

        logger.info(
            f"Execution context: pod={self._context.pod_name}, "
            f"processor_id={self._context.processor_id}, "
            f"attempt={self._context.attempt_number}, "
            f"is_migrating={self._context.is_migrating}"
        )

        # Create processor instance
        self._processor = processor_class(self._context)

        # Setup signal handlers
        self._signals.setup(
            shutdown_callback=self._trigger_shutdown,
            snapshot_callback=self._trigger_snapshot,
        )

        # Record startup metric
        self._metrics.record_startup_started()

    async def _start_health_server(self) -> None:
        """Start the health/metrics HTTP server."""
        self._health_server = HealthServer(
            port=self._config.health_port,
            metrics_collector=self._metrics,
            state_getter=self._get_processor_state,
            state_restorer=self._restore_processor_state,
            prestop_handler=self._handle_prestop,
        )
        await self._health_server.start()
        logger.info(f"Health server started on port {self._config.health_port}")

    def _get_processor_state(self) -> dict:
        """Get processor state for /state GET endpoint (state capture)."""
        if self._processor is None:
            logger.warning("Processor not initialized, returning empty state")
            return {}

        try:
            import os
            import time
            state = self._processor.get_state()

            # Wrap state in ApplicationState format expected by Orchestrator
            return {
                "pod_name": self._context.pod_name if self._context else "unknown",
                "app_name": os.environ.get("APP_NAME", "dory-processor"),
                "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "state_version": "1.0",
                "data": state,
                "metrics": {},
                "connections": [],
                "active_sessions": 0,
                "session_data": {},
                "uptime_seconds": self._metrics.get_uptime_seconds() if self._metrics else 0.0,
                "request_count": self._metrics.get_request_count() if self._metrics else 0,
                "last_health_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        except Exception as e:
            logger.error(f"Failed to get processor state: {e}")
            return {"error": str(e)}

    async def _restore_processor_state(self, state: dict) -> None:
        """Restore processor state from /state POST endpoint (state transfer)."""
        if self._processor is None:
            raise RuntimeError("Processor not initialized, cannot restore state")

        # Extract processor data from ApplicationState format
        processor_data = state.get("data", state)

        logger.info(f"Restoring state from transfer", extra={
            "pod_name": state.get("pod_name", "unknown"),
            "state_version": state.get("state_version", "unknown"),
        })

        await self._processor.restore_state(processor_data)

    async def _handle_prestop(self) -> None:
        """Handle PreStop hook - prepare for graceful shutdown."""
        logger.info("PreStop hook: initiating graceful shutdown preparation")

        # Signal context that shutdown is coming
        if self._context:
            self._context.request_shutdown()

        # Mark health server as not ready to stop receiving traffic
        if self._health_server:
            self._health_server.mark_not_ready()

        # Save state before pod terminates - this is critical because
        # SIGTERM may arrive after the app has already started exiting
        if self._processor and self._state_manager and self._context:
            try:
                state = self._processor.get_state()
                await self._state_manager.save_state(
                    processor_id=self._context.processor_id,
                    state=state,
                )
                logger.info("State snapshot saved during PreStop")
            except Exception as e:
                logger.error(f"Failed to save state during PreStop: {e}")

    async def _run_processor_lifecycle(self) -> None:
        """Run the complete processor lifecycle."""
        # Check if saved state exists before deciding recovery strategy
        # This is important for detecting pod replacement (new pod, existing state)
        state_exists = False
        try:
            existing_state = await self._state_manager.load_state(
                processor_id=self._context.processor_id,
            )
            state_exists = existing_state is not None
            if state_exists:
                logger.info("Existing state found in checkpoint")
        except Exception as e:
            logger.debug(f"No existing state found: {e}")

        # Determine recovery strategy
        strategy = self._recovery_decision.decide(
            restart_count=self._context.attempt_number,
            is_migrating=self._context.is_migrating,
            state_exists=state_exists,
        )

        logger.info(f"Recovery strategy: {strategy.name}")

        # Load state if needed (may already have it from check above)
        state = None
        if strategy.should_restore_state:
            try:
                if state_exists and existing_state:
                    state = existing_state
                else:
                    state = await self._state_manager.load_state(
                        processor_id=self._context.processor_id,
                    )
                if state:
                    logger.info("State loaded from checkpoint")
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                state = None

        # Run startup
        await self._lifecycle.run_startup(
            processor=self._processor,
            timeout=self._config.startup_timeout_sec,
        )

        # Restore state if available
        if state:
            try:
                await self._processor.restore_state(state)
                logger.info("State restored successfully")
            except Exception as e:
                logger.error(f"State restore failed: {e}")
                should_continue = await self._processor.on_state_restore_failed(e)
                if not should_continue:
                    raise DoryStateError("State restore failed and recovery declined", cause=e)

        # Mark as ready
        self._health_server.mark_ready()
        self._metrics.record_startup_completed()
        logger.info("Processor ready")

        # Run main loop
        try:
            await self._lifecycle.run_main_loop(
                processor=self._processor,
                context=self._context,
            )
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")

    async def _trigger_shutdown(self) -> None:
        """Trigger graceful shutdown sequence."""
        logger.info("Shutdown triggered")

        # Signal context
        self._context.request_shutdown()

        # Mark health server as not ready
        if self._health_server:
            self._health_server.mark_not_ready()

        # Wait briefly for run() to exit
        await asyncio.sleep(0.5)

        # Run shutdown
        await self._lifecycle.run_shutdown(
            processor=self._processor,
            timeout=self._config.shutdown_timeout_sec,
        )

        # Snapshot state
        try:
            state = self._processor.get_state()
            await self._state_manager.save_state(
                processor_id=self._context.processor_id,
                state=state,
            )
            logger.info("State snapshot saved")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

        self._metrics.record_shutdown_completed()

    async def _trigger_snapshot(self) -> None:
        """Trigger state snapshot (SIGUSR1 handler)."""
        logger.info("State snapshot triggered")
        try:
            state = self._processor.get_state()
            await self._state_manager.save_state(
                processor_id=self._context.processor_id,
                state=state,
            )
            logger.info("State snapshot saved (debug)")
        except Exception as e:
            logger.error(f"Failed to save state snapshot: {e}")

    async def _cleanup(self) -> None:
        """Cleanup all components."""
        logger.debug("Cleaning up DoryApp components")

        # Remove signal handlers
        if self._signals:
            self._signals.remove_handlers()

        # Stop health server
        if self._health_server:
            await self._health_server.stop()

        # Flush metrics
        if self._metrics:
            self._metrics.flush()

        # Flush logs
        logging.shutdown()
