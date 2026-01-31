"""
Health and metrics HTTP server.

Provides endpoints for:
- /healthz - Liveness probe
- /ready - Readiness probe (matches Kubernetes convention)
- /metrics - Prometheus metrics
- /state - State transfer (GET/POST) for pod migration
- /prestop - PreStop hook handler for graceful shutdown
"""

import logging
import os
import secrets
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Callable, Awaitable

from aiohttp import web

from dory.health.probes import LivenessProbe, ReadinessProbe
from dory.utils.errors import DoryHealthError
from dory.config.defaults import (
    DEFAULT_RATE_LIMIT_RPS,
    DEFAULT_MAX_STATE_SIZE,
    DEFAULT_HEALTH_HOST,
)

if TYPE_CHECKING:
    from dory.metrics.collector import MetricsCollector

logger = logging.getLogger(__name__)

# Type aliases for callbacks
StateGetter = Callable[[], dict]
StateRestorer = Callable[[dict], Awaitable[None]]
PreStopHandler = Callable[[], Awaitable[None]]


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    Tracks requests per client IP and rejects requests that exceed
    the configured rate limit.
    """

    def __init__(self, requests_per_second: int = DEFAULT_RATE_LIMIT_RPS):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests allowed per second per client.
                                 Set to 0 to disable rate limiting.
        """
        self._rps = requests_per_second
        self._requests: dict[str, list[float]] = defaultdict(list)

    @property
    def enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self._rps > 0

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if a request from the client IP is allowed.

        Args:
            client_ip: The client's IP address

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        if not self.enabled:
            return True

        now = time.time()

        # Clean old entries (older than 1 second)
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < 1.0
        ]

        # Check if under limit
        if len(self._requests[client_ip]) >= self._rps:
            return False

        # Record this request
        self._requests[client_ip].append(now)
        return True

    def get_request_count(self, client_ip: str) -> int:
        """Get current request count for a client (for metrics/debugging)."""
        now = time.time()
        return len([t for t in self._requests[client_ip] if now - t < 1.0])


class HealthServer:
    """
    HTTP server for health probes, metrics, and state transfer.

    Runs on a separate port from the main application.
    Provides endpoints required by Dory Orchestrator for:
    - Health probes (liveness/readiness)
    - Prometheus metrics
    - State transfer during pod migration
    - PreStop hook for graceful shutdown
    """

    # Default host binding (imported from config.defaults)
    DEFAULT_HOST = DEFAULT_HEALTH_HOST

    def __init__(
        self,
        port: int = 8080,
        host: str | None = None,
        health_path: str = "/healthz",
        ready_path: str = "/ready",  # Changed from /readyz to match Orchestrator
        metrics_path: str = "/metrics",
        metrics_collector: "MetricsCollector | None" = None,
        state_getter: StateGetter | None = None,
        state_restorer: StateRestorer | None = None,
        prestop_handler: PreStopHandler | None = None,
    ):
        """
        Initialize health server.

        Args:
            port: Port to listen on
            host: Host address to bind to (default: 0.0.0.0, configurable via DORY_HEALTH_HOST)
            health_path: Path for liveness probe
            ready_path: Path for readiness probe
            metrics_path: Path for Prometheus metrics
            metrics_collector: Optional metrics collector for /metrics endpoint
            state_getter: Callback to get processor state for /state GET
            state_restorer: Callback to restore processor state for /state POST
            prestop_handler: Callback for /prestop PreStop hook
        """
        self._port = port
        self._host = host or os.getenv("DORY_HEALTH_HOST", self.DEFAULT_HOST)
        self._health_path = health_path
        self._ready_path = ready_path
        self._metrics_path = metrics_path
        self._metrics_collector = metrics_collector
        self._state_getter = state_getter
        self._state_restorer = state_restorer
        self._prestop_handler = prestop_handler

        # State endpoint authentication token (optional, for security)
        # If not set, state endpoints are open (backward compatibility)
        self._state_token = os.getenv("DORY_STATE_TOKEN")

        # Rate limiting configuration
        # Set DORY_RATE_LIMIT=0 to disable rate limiting
        rate_limit = int(os.getenv("DORY_RATE_LIMIT", str(DEFAULT_RATE_LIMIT_RPS)))
        self._rate_limiter = RateLimiter(requests_per_second=rate_limit)

        # Request size limit for state transfers (in bytes)
        self._max_request_size = int(
            os.getenv("DORY_MAX_STATE_SIZE", str(DEFAULT_MAX_STATE_SIZE))
        )

        self._liveness = LivenessProbe()
        self._readiness = ReadinessProbe()

        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    @property
    def liveness_probe(self) -> LivenessProbe:
        """Get liveness probe for adding custom checks."""
        return self._liveness

    @property
    def readiness_probe(self) -> ReadinessProbe:
        """Get readiness probe for adding custom checks."""
        return self._readiness

    def mark_ready(self) -> None:
        """Mark the application as ready to receive traffic."""
        self._readiness.mark_ready()

    def mark_not_ready(self) -> None:
        """Mark the application as not ready."""
        self._readiness.mark_not_ready()

    def set_state_getter(self, getter: StateGetter) -> None:
        """Set the callback for getting processor state."""
        self._state_getter = getter

    def set_state_restorer(self, restorer: StateRestorer) -> None:
        """Set the callback for restoring processor state."""
        self._state_restorer = restorer

    def set_prestop_handler(self, handler: PreStopHandler) -> None:
        """Set the callback for PreStop hook."""
        self._prestop_handler = handler

    @web.middleware
    async def _rate_limit_middleware(
        self, request: web.Request, handler: Callable
    ) -> web.Response:
        """
        Middleware to enforce rate limiting.

        Returns 429 Too Many Requests if rate limit is exceeded.
        """
        client_ip = request.remote or "unknown"

        if not self._rate_limiter.is_allowed(client_ip):
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={"client_ip": client_ip}
            )
            return web.json_response(
                {"error": "Rate limit exceeded"},
                status=429,
                headers={"Retry-After": "1"}
            )

        return await handler(request)

    async def start(self) -> None:
        """
        Start the health server.

        Raises:
            DoryHealthError: If server fails to start
        """
        try:
            # Create app with request size limit and rate limiting middleware
            middlewares = []
            if self._rate_limiter.enabled:
                middlewares.append(self._rate_limit_middleware)

            self._app = web.Application(
                client_max_size=self._max_request_size,
                middlewares=middlewares,
            )
            self._setup_routes()

            self._runner = web.AppRunner(self._app)
            await self._runner.setup()

            self._site = web.TCPSite(
                self._runner,
                host=self._host,
                port=self._port,
            )
            await self._site.start()

            rate_limit_status = (
                f"{self._rate_limiter._rps} req/s"
                if self._rate_limiter.enabled
                else "disabled"
            )
            logger.info(
                f"Health server started on {self._host}:{self._port} "
                f"(rate_limit={rate_limit_status}, max_size={self._max_request_size})"
            )

        except Exception as e:
            raise DoryHealthError(f"Failed to start health server: {e}", cause=e)

    async def stop(self) -> None:
        """Stop the health server."""
        if self._runner:
            await self._runner.cleanup()
            logger.info("Health server stopped")

    def _setup_routes(self) -> None:
        """Configure HTTP routes."""
        self._app.router.add_get(self._health_path, self._handle_health)
        self._app.router.add_get(self._ready_path, self._handle_ready)
        self._app.router.add_get(self._metrics_path, self._handle_metrics)

        # State transfer endpoints (required by Dory Orchestrator)
        self._app.router.add_get("/state", self._handle_state_get)
        self._app.router.add_post("/state", self._handle_state_post)

        # PreStop hook endpoint (required by Dory Orchestrator)
        self._app.router.add_get("/prestop", self._handle_prestop)

        # Root endpoint for basic info
        self._app.router.add_get("/", self._handle_root)

    async def _handle_root(self, request: web.Request) -> web.Response:
        """Handle root endpoint."""
        return web.json_response({
            "service": "dory-processor",
            "endpoints": [
                self._health_path,
                self._ready_path,
                self._metrics_path,
                "/state",
                "/prestop",
            ],
        })

    async def _handle_health(self, request: web.Request) -> web.Response:
        """
        Handle liveness probe.

        Returns 200 if alive, 503 if unhealthy.
        """
        result = await self._liveness.check()

        status = 200 if result.healthy else 503
        return web.json_response(result.to_dict(), status=status)

    async def _handle_ready(self, request: web.Request) -> web.Response:
        """
        Handle readiness probe.

        Returns 200 if ready, 503 if not ready.
        """
        result = await self._readiness.check()

        status = 200 if result.healthy else 503
        return web.json_response(result.to_dict(), status=status)

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        """
        Handle Prometheus metrics endpoint.

        Returns metrics in Prometheus text format.
        """
        if self._metrics_collector is None:
            return web.Response(
                text="# No metrics collector configured\n",
                content_type="text/plain",
            )

        try:
            metrics_text = self._metrics_collector.export_prometheus()
            return web.Response(
                text=metrics_text,
                content_type="text/plain; version=0.0.4",
                charset="utf-8",
            )
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return web.Response(
                text=f"# Error exporting metrics: {e}\n",
                content_type="text/plain",
                status=500,
            )

    def _validate_state_token(self, request: web.Request) -> bool:
        """
        Validate state transfer token from Authorization header.

        Uses timing-safe comparison to prevent timing attacks.

        Args:
            request: The incoming HTTP request

        Returns:
            True if token is valid or no token is configured (backward compat)
        """
        if not self._state_token:
            # No token configured = allow all requests (backward compatibility)
            return True

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return secrets.compare_digest(token, self._state_token)

        return False

    async def _handle_state_get(self, request: web.Request) -> web.Response:
        """
        Handle GET /state for state capture during migration.

        Called by Dory Orchestrator to capture state from old pod
        before transferring to new pod.

        Returns:
            JSON response with processor state
        """
        if not self._validate_state_token(request):
            logger.warning("Unauthorized state GET request")
            return web.json_response({"error": "Unauthorized"}, status=401)

        if self._state_getter is None:
            logger.warning("State getter not configured, returning empty state")
            return web.json_response({
                "error": "state_getter not configured",
                "data": {},
            }, status=503)

        try:
            state = self._state_getter()
            logger.info("State captured for transfer", extra={"state_keys": list(state.keys())})
            return web.json_response(state)
        except Exception as e:
            logger.error(f"Failed to capture state: {e}")
            return web.json_response(
                {"error": f"Failed to capture state: {e}"},
                status=500,
            )

    async def _handle_state_post(self, request: web.Request) -> web.Response:
        """
        Handle POST /state for state restoration during migration.

        Called by Dory Orchestrator to restore state to new pod
        after capturing from old pod.

        Returns:
            JSON response confirming state restoration
        """
        if not self._validate_state_token(request):
            logger.warning("Unauthorized state POST request")
            return web.json_response({"error": "Unauthorized"}, status=401)

        if self._state_restorer is None:
            logger.warning("State restorer not configured")
            return web.json_response({
                "error": "state_restorer not configured",
            }, status=503)

        # Validate content length before reading
        content_length = request.content_length
        if content_length is not None and content_length > self._max_request_size:
            logger.warning(
                f"State payload too large: {content_length} bytes "
                f"(max: {self._max_request_size})"
            )
            return web.json_response(
                {"error": f"Payload too large (max: {self._max_request_size} bytes)"},
                status=413,
            )

        try:
            state = await request.json()

            # Validate state is a dictionary
            if not isinstance(state, dict):
                logger.warning(f"Invalid state type: {type(state).__name__}")
                return web.json_response(
                    {"error": "State must be a JSON object"},
                    status=400,
                )

            logger.info("Restoring state from transfer", extra={"state_keys": list(state.keys())})
            await self._state_restorer(state)
            logger.info("State restored successfully")
            return web.json_response({"status": "ok", "message": "State restored"})

        except ValueError as e:
            # JSON decode error
            logger.warning(f"Invalid JSON in state payload: {e}")
            return web.json_response(
                {"error": "Invalid JSON payload"},
                status=400,
            )
        except Exception as e:
            logger.error(f"Failed to restore state: {e}")
            return web.json_response(
                {"error": f"Failed to restore state: {e}"},
                status=500,
            )

    async def _handle_prestop(self, request: web.Request) -> web.Response:
        """
        Handle GET /prestop for PreStop hook.

        Called by Kubernetes PreStop hook before pod termination.
        Allows the application to prepare for graceful shutdown.

        Returns:
            JSON response confirming prestop handling
        """
        logger.info("PreStop hook invoked - preparing for shutdown")

        # Mark as not ready to stop receiving new traffic
        self._readiness.mark_not_ready()

        if self._prestop_handler:
            try:
                await self._prestop_handler()
                logger.info("PreStop handler completed")
            except Exception as e:
                logger.error(f"PreStop handler error: {e}")
                # Continue anyway - don't block shutdown

        return web.json_response({
            "status": "ok",
            "message": "PreStop hook processed, ready for termination",
        })
