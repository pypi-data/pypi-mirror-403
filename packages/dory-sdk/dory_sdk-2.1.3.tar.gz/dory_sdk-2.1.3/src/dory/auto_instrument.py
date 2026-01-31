"""
Auto-instrumentation decorator for handlers.

Automatically applies:
- Request ID generation
- Request tracking
- OpenTelemetry span creation
- Error classification
- Attribute injection

No manual decorators needed!
"""

import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def auto_instrument(func: Callable) -> Callable:
    """
    Auto-instrument async function with all SDK features.

    Automatically handles:
    - Request ID generation
    - Request tracking with timeout
    - OpenTelemetry span creation
    - Span attributes injection
    - Error classification and logging

    Usage:
        @auto_instrument
        async def handler(self, request):
            # All instrumentation is automatic!
            return {"status": "ok"}

    Or with metaclass (no decorator needed):
        class MyProcessor(BaseProcessor):
            # All handle_* methods automatically instrumented!
            async def handle_request(self, request):
                return {"status": "ok"}

    Args:
        func: Async function to instrument

    Returns:
        Instrumented async function
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Extract request if present (first arg or keyword arg)
        request = None
        if args:
            request = args[0]
        elif "request" in kwargs:
            request = kwargs["request"]

        # Get processor components (auto-initialized by BaseProcessor)
        request_id_middleware = getattr(self, "request_id_middleware", None)
        request_tracker = getattr(self, "request_tracker", None)
        otel = getattr(self, "otel", None)
        error_classifier = getattr(self, "error_classifier", None)

        # 1. Generate request ID
        request_id = None
        if request_id_middleware:
            request_id = request_id_middleware.generate_id()
            # Store in request for retrieval
            if request is not None and hasattr(request, "__setitem__"):
                request["request_id"] = request_id
            elif request is not None and hasattr(request, "__dict__"):
                request.request_id = request_id
            logger.debug(f"Generated request ID: {request_id}")

        # 2. Track request
        request_tracker_ctx = None
        if request_tracker:
            request_tracker_ctx = request_tracker.track_request(request_id)
            await request_tracker_ctx.__aenter__()
            logger.debug(f"Started tracking request: {request_id}")

        # 3. Create OpenTelemetry span
        span_ctx = None
        if otel:
            span_name = f"{self.__class__.__name__}.{func.__name__}"
            attributes = {
                "function": func.__name__,
                "class": self.__class__.__name__,
            }
            if request_id:
                attributes["request.id"] = request_id
            if request is not None and hasattr(request, "path"):
                attributes["endpoint"] = str(request.path)
            if request is not None and hasattr(request, "method"):
                attributes["http.method"] = str(request.method)

            span_ctx = otel.create_span(span_name, attributes=attributes)
            span_ctx.__enter__()
            logger.debug(f"Created span: {span_name}")

        try:
            # Execute handler
            result = await func(self, *args, **kwargs)

            # Mark request as successful
            if request_tracker_ctx:
                await request_tracker_ctx.__aexit__(None, None, None)
                logger.debug(f"Request completed successfully: {request_id}")

            if span_ctx:
                span_ctx.__exit__(None, None, None)

            return result

        except Exception as e:
            # Classify error
            if error_classifier:
                error_info = error_classifier.classify(e)
                logger.warning(
                    f"Handler error: {error_info.error_type.value} - {e}",
                    extra={
                        "request_id": request_id,
                        "error_type": error_info.error_type.value,
                        "is_transient": error_info.is_transient,
                    },
                )
            else:
                logger.warning(f"Handler error: {e}", extra={"request_id": request_id})

            # Mark request as failed
            if request_tracker_ctx:
                await request_tracker_ctx.__aexit__(type(e), e, None)

            # Record exception in span
            if span_ctx:
                span_ctx.__exit__(type(e), e, None)

            raise

    return wrapper
