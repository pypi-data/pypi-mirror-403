"""
Request ID Middleware

Automatically generates and propagates request IDs for tracing and correlation.
Eliminates manual request ID management.

Features:
- Automatic request ID generation
- Context propagation
- Log integration
- Correlation across services
"""

import asyncio
import logging
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

# Context variable for current request ID
_request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    """
    Generate a unique request ID.

    Returns:
        UUID-based request ID
    """
    return str(uuid.uuid4())


def get_current_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Current request ID or None if not set
    """
    return _request_id_context.get()


def set_request_id(request_id: str) -> None:
    """
    Set the request ID in context.

    Args:
        request_id: Request ID to set
    """
    _request_id_context.set(request_id)


class RequestIdMiddleware:
    """
    Middleware for automatic request ID management.

    Features:
    - Generates request IDs
    - Propagates through context
    - Integrates with logging
    - Supports custom ID generation

    Usage:
        middleware = RequestIdMiddleware()

        # Use context manager
        async with middleware.with_request_id():
            # All operations have access to request ID
            request_id = get_current_request_id()
            logger.info(f"Processing with request_id={request_id}")

        # Or use decorator
        @middleware.with_request_id_decorator()
        async def process_item(item):
            request_id = get_current_request_id()
            # Process with request ID
    """

    def __init__(
        self,
        id_generator: Optional[Callable[[], str]] = None,
        header_name: str = "X-Request-ID",
        log_request_id: bool = True,
    ):
        """
        Initialize request ID middleware.

        Args:
            id_generator: Optional custom ID generator function
            header_name: Header name for request ID
            log_request_id: Whether to add request ID to logs
        """
        self.id_generator = id_generator or generate_request_id
        self.header_name = header_name
        self.log_request_id = log_request_id

        logger.info(
            f"RequestIdMiddleware initialized: header={header_name}, "
            f"log_enabled={log_request_id}"
        )

    async def with_request_id(
        self,
        request_id: Optional[str] = None,
    ):
        """
        Context manager that sets request ID for the scope.

        Args:
            request_id: Optional existing request ID (generates new if None)

        Example:
            async with middleware.with_request_id():
                # Operations here have access to request ID
                request_id = get_current_request_id()
        """
        # Generate or use provided request ID
        if request_id is None:
            request_id = self.id_generator()

        # Set in context
        token = _request_id_context.set(request_id)

        # Add to logs if enabled
        if self.log_request_id:
            log_filter = RequestIdLogFilter(request_id)
            logging.getLogger().addFilter(log_filter)

        try:
            yield request_id
        finally:
            # Reset context
            _request_id_context.reset(token)

            # Remove log filter
            if self.log_request_id:
                logging.getLogger().removeFilter(log_filter)

    def with_request_id_decorator(
        self,
        request_id_arg: Optional[str] = None,
    ):
        """
        Decorator that automatically manages request ID.

        Args:
            request_id_arg: Optional argument name containing request ID

        Example:
            @middleware.with_request_id_decorator()
            async def process_item(item):
                request_id = get_current_request_id()
                logger.info(f"Processing {item}")
                # Log will include request_id

            # Or extract from argument
            @middleware.with_request_id_decorator(request_id_arg="headers")
            async def handle_request(headers):
                # Uses headers.get("X-Request-ID") if present
                pass
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Try to extract request ID from arguments if specified
                extracted_id = None
                if request_id_arg:
                    # Check kwargs
                    if request_id_arg in kwargs:
                        arg_value = kwargs[request_id_arg]
                        if isinstance(arg_value, dict):
                            extracted_id = arg_value.get(self.header_name)
                        else:
                            extracted_id = arg_value

                # Use extracted or generate new
                request_id = extracted_id or self.id_generator()

                async with self.with_request_id(request_id):
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def extract_request_id(self, headers: dict) -> Optional[str]:
        """
        Extract request ID from headers.

        Args:
            headers: HTTP headers or similar dict

        Returns:
            Request ID if present, None otherwise
        """
        return headers.get(self.header_name)

    def inject_request_id(self, headers: dict, request_id: Optional[str] = None) -> dict:
        """
        Inject request ID into headers.

        Args:
            headers: HTTP headers or similar dict
            request_id: Optional request ID (uses current context if None)

        Returns:
            Headers with request ID injected
        """
        if request_id is None:
            request_id = get_current_request_id()

        if request_id:
            headers = dict(headers)
            headers[self.header_name] = request_id

        return headers


class RequestIdLogFilter(logging.Filter):
    """
    Log filter that adds request ID to log records.
    """

    def __init__(self, request_id: str):
        """
        Initialize log filter.

        Args:
            request_id: Request ID to add to logs
        """
        super().__init__()
        self.request_id = request_id

    def filter(self, record):
        """Add request ID to log record."""
        record.request_id = self.request_id
        return True


# Convenience decorator using global middleware instance
_global_middleware: Optional[RequestIdMiddleware] = None


def get_global_middleware() -> RequestIdMiddleware:
    """Get or create global middleware instance."""
    global _global_middleware
    if _global_middleware is None:
        _global_middleware = RequestIdMiddleware()
    return _global_middleware


def with_request_id(func: Optional[Callable] = None, request_id: Optional[str] = None):
    """
    Convenience decorator using global middleware.

    Args:
        func: Function to decorate
        request_id: Optional request ID

    Example:
        @with_request_id
        async def process_item(item):
            request_id = get_current_request_id()
            logger.info(f"Processing {item}")  # Log includes request_id
    """
    middleware = get_global_middleware()

    if func is None:
        # Used as @with_request_id()
        return middleware.with_request_id_decorator()

    # Used as @with_request_id
    return middleware.with_request_id_decorator()(func)


# Example log format with request ID
RECOMMENDED_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s"


def configure_logging_with_request_id(
    level: int = logging.INFO,
    format_string: str = RECOMMENDED_LOG_FORMAT,
) -> None:
    """
    Configure logging to include request IDs.

    Args:
        level: Logging level
        format_string: Format string (should include %(request_id)s)

    Example:
        configure_logging_with_request_id()

        @with_request_id
        async def my_function():
            logger.info("Hello")  # [INFO] [<request-id>] module: Hello
    """
    # Add default value for request_id if not in context
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        if not hasattr(record, "request_id"):
            request_id = get_current_request_id()
            record.request_id = request_id or "no-request-id"
        return record

    logging.setLogRecordFactory(record_factory)

    # Configure basic logging
    logging.basicConfig(
        level=level,
        format=format_string,
        force=True,
    )

    logger.info("Logging configured with request ID support")
