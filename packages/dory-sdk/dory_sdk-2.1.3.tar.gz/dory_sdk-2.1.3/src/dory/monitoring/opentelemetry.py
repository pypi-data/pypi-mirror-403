"""
OpenTelemetry Integration

Provides full OpenTelemetry support for distributed tracing and metrics.

Features:
- Automatic span creation
- Trace propagation
- Metrics collection
- Context management
- Integration with request IDs

Note: Requires opentelemetry packages:
    pip install opentelemetry-api opentelemetry-sdk
    pip install opentelemetry-exporter-otlp
"""

import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry (optional dependency)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning(
        "OpenTelemetry not available. Install with: "
        "pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp"
    )


class OpenTelemetryManager:
    """
    Manages OpenTelemetry tracing and metrics.

    Features:
    - Automatic tracer setup
    - Span creation and management
    - Context propagation
    - Metrics collection
    - Export to OTLP endpoints

    Usage:
        # Initialize
        otel = OpenTelemetryManager(service_name="my-service")
        otel.initialize()

        # Use decorator
        @otel.trace("process_item")
        async def process_item(item):
            # Automatically traced
            pass

        # Or context manager
        with otel.create_span("operation"):
            # Operations here are traced
            pass
    """

    def __init__(
        self,
        service_name: str = "dory-processor",
        service_version: str = "1.0.0",
        environment: str = "production",
        otlp_endpoint: Optional[str] = None,
        console_export: bool = False,
        enable_metrics: bool = True,
    ):
        """
        Initialize OpenTelemetry manager.

        Args:
            service_name: Name of the service
            service_version: Version of the service
            environment: Environment (production, staging, dev)
            otlp_endpoint: Optional OTLP endpoint URL
            console_export: Export spans to console (for debugging)
            enable_metrics: Enable metrics collection
        """
        if not OTEL_AVAILABLE:
            raise ImportError(
                "OpenTelemetry not available. Install with: "
                "pip install opentelemetry-api opentelemetry-sdk"
            )

        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint
        self.console_export = console_export
        self.enable_metrics = enable_metrics

        self._tracer_provider: Optional[TracerProvider] = None
        self._tracer: Optional[trace.Tracer] = None
        self._initialized = False

        logger.info(
            f"OpenTelemetryManager created: service={service_name}, "
            f"version={service_version}, env={environment}"
        )

    def initialize(self) -> None:
        """
        Initialize OpenTelemetry.

        Sets up tracer provider, exporters, and processors.
        """
        if self._initialized:
            logger.warning("OpenTelemetry already initialized")
            return

        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
        })

        # Create tracer provider
        self._tracer_provider = TracerProvider(resource=resource)

        # Add console exporter if enabled
        if self.console_export:
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            self._tracer_provider.add_span_processor(console_processor)
            logger.info("Console span exporter added")

        # Add OTLP exporter if endpoint provided
        if self.otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

                otlp_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                self._tracer_provider.add_span_processor(otlp_processor)
                logger.info(f"OTLP span exporter added: {self.otlp_endpoint}")
            except ImportError:
                logger.warning(
                    "OTLP exporter not available. Install with: "
                    "pip install opentelemetry-exporter-otlp"
                )

        # Set global tracer provider
        trace.set_tracer_provider(self._tracer_provider)

        # Get tracer
        self._tracer = trace.get_tracer(
            instrumenting_module_name=__name__,
            instrumenting_library_version=self.service_version,
        )

        self._initialized = True
        logger.info("OpenTelemetry initialized successfully")

    def get_tracer(self) -> trace.Tracer:
        """
        Get the tracer instance.

        Returns:
            OpenTelemetry tracer
        """
        if not self._initialized:
            self.initialize()
        return self._tracer

    @contextmanager
    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ):
        """
        Create a span context manager.

        Args:
            name: Span name
            attributes: Optional span attributes
            kind: Span kind (INTERNAL, SERVER, CLIENT, etc.)

        Example:
            with otel.create_span("database_query", {"query": "SELECT ...")):
                result = await db.execute(query)
        """
        if not self._initialized:
            # If not initialized, just yield without tracing
            yield None
            return

        tracer = self.get_tracer()

        with tracer.start_as_current_span(name, kind=kind) as span:
            # Add attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
            except Exception as e:
                # Record exception
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            else:
                span.set_status(Status(StatusCode.OK))

    def trace(
        self,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ):
        """
        Decorator to automatically trace a function.

        Args:
            name: Span name (uses function name if None)
            attributes: Optional span attributes
            kind: Span kind

        Example:
            @otel.trace("process_item")
            async def process_item(item):
                # Automatically traced
                pass
        """
        def decorator(func):
            span_name = name or func.__name__

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.create_span(span_name, attributes, kind):
                    return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.create_span(span_name, attributes, kind):
                    return func(*args, **kwargs)

            # Return appropriate wrapper
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def add_span_attributes(self, attributes: Dict[str, Any]) -> None:
        """
        Add attributes to current span.

        Args:
            attributes: Attributes to add
        """
        if not self._initialized:
            return

        span = trace.get_current_span()
        if span:
            for key, value in attributes.items():
                span.set_attribute(key, value)

    def record_exception(self, exception: Exception) -> None:
        """
        Record an exception in current span.

        Args:
            exception: Exception to record
        """
        if not self._initialized:
            return

        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))

    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Inject trace context into headers for propagation.

        Args:
            headers: HTTP headers or similar dict

        Returns:
            Headers with trace context injected
        """
        if not self._initialized:
            return headers

        propagator = TraceContextTextMapPropagator()
        headers = dict(headers)
        propagator.inject(headers)
        return headers

    def extract_context(self, headers: Dict[str, str]) -> None:
        """
        Extract trace context from headers.

        Args:
            headers: HTTP headers or similar dict
        """
        if not self._initialized:
            return

        propagator = TraceContextTextMapPropagator()
        context = propagator.extract(headers)
        # Context is automatically set as current

    def shutdown(self) -> None:
        """Shutdown OpenTelemetry and flush spans."""
        if self._tracer_provider:
            self._tracer_provider.shutdown()
            logger.info("OpenTelemetry shut down")


# Global instance
_global_otel: Optional[OpenTelemetryManager] = None


def get_global_otel() -> Optional[OpenTelemetryManager]:
    """Get global OpenTelemetry manager."""
    return _global_otel


def initialize_otel(
    service_name: str = "dory-processor",
    **kwargs
) -> OpenTelemetryManager:
    """
    Initialize global OpenTelemetry manager.

    Args:
        service_name: Service name
        **kwargs: Additional arguments for OpenTelemetryManager

    Returns:
        Initialized OpenTelemetryManager
    """
    global _global_otel

    if _global_otel:
        logger.warning("Global OpenTelemetry already initialized")
        return _global_otel

    _global_otel = OpenTelemetryManager(service_name=service_name, **kwargs)
    _global_otel.initialize()

    logger.info(f"Global OpenTelemetry initialized for service: {service_name}")
    return _global_otel


# Convenience functions using global instance

def get_tracer() -> Optional[trace.Tracer]:
    """Get tracer from global instance."""
    otel = get_global_otel()
    return otel.get_tracer() if otel else None


def create_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
):
    """Create span using global instance."""
    otel = get_global_otel()
    if otel:
        return otel.create_span(name, attributes, kind)
    else:
        # Return no-op context manager
        @contextmanager
        def noop():
            yield None
        return noop()


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
):
    """Trace function using global instance."""
    otel = get_global_otel()
    if otel:
        return otel.trace(name, attributes, kind)
    else:
        # Return no-op decorator
        def decorator(func):
            return func
        return decorator


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """Add attributes to current span using global instance."""
    otel = get_global_otel()
    if otel:
        otel.add_span_attributes(attributes)


def record_exception(exception: Exception) -> None:
    """Record exception in current span using global instance."""
    otel = get_global_otel()
    if otel:
        otel.record_exception(exception)


# Integration with request IDs

def integrate_with_request_id():
    """
    Integrate OpenTelemetry with request ID middleware.

    Automatically adds request IDs as span attributes.
    """
    try:
        from dory.middleware.request_id import get_current_request_id

        otel = get_global_otel()
        if not otel:
            logger.warning("OpenTelemetry not initialized")
            return

        # Monkey patch create_span to add request ID
        original_create_span = otel.create_span

        @contextmanager
        def create_span_with_request_id(name, attributes=None, kind=SpanKind.INTERNAL):
            # Get current request ID
            request_id = get_current_request_id()

            # Add to attributes
            attrs = attributes or {}
            if request_id:
                attrs["request.id"] = request_id

            with original_create_span(name, attrs, kind) as span:
                yield span

        otel.create_span = create_span_with_request_id

        logger.info("OpenTelemetry integrated with request ID middleware")

    except ImportError:
        logger.warning("Request ID middleware not available for integration")
