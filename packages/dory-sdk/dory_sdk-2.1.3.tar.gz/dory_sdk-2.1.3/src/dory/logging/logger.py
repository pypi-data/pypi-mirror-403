"""
Structured logging for Dory SDK.

Provides JSON-formatted logging suitable for Kubernetes
and log aggregation systems.
"""

import json
import logging
import sys
import time
from typing import Any

from dory.types import LogFormat


class JsonFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Output format:
    {
        "timestamp": "2024-01-15T10:30:45.123456Z",
        "level": "INFO",
        "logger": "dory.core.app",
        "message": "Processor starting",
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_dict = {
            "timestamp": self._format_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        extra = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info", "exc_text",
                "stack_info", "lineno", "funcName", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "msecs", "taskName",
            ):
                extra[key] = self._serialize_value(value)

        if extra:
            log_dict["extra"] = extra

        return json.dumps(log_dict)

    def _format_timestamp(self, created: float) -> str:
        """Format timestamp as ISO 8601."""
        return time.strftime(
            "%Y-%m-%dT%H:%M:%S",
            time.gmtime(created)
        ) + f".{int((created % 1) * 1000000):06d}Z"

    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        return str(value)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter.

    Output format:
    2024-01-15 10:30:45.123 [INFO] dory.core.app: Processor starting
    """

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class DoryLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to all log messages.

    Usage:
        logger = DoryLoggerAdapter(
            logging.getLogger(__name__),
            {"processor_id": "my-processor", "pod": "my-pod-abc123"}
        )
        logger.info("Processing started")
        # Output includes processor_id and pod in extra fields
    """

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Add extra context to log kwargs."""
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    format: str | LogFormat = LogFormat.JSON,
) -> None:
    """
    Setup logging configuration for Dory SDK.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Log format (json or text)
    """
    # Convert enum to string if needed
    if isinstance(format, LogFormat):
        format = format.value

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Set formatter based on format
    if format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Set levels for noisy libraries
    logging.getLogger("kubernetes").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(
    name: str,
    extra: dict[str, Any] | None = None,
) -> logging.Logger | DoryLoggerAdapter:
    """
    Get a logger with optional extra context.

    Args:
        name: Logger name (usually __name__)
        extra: Optional extra context to include in all logs

    Returns:
        Logger or LoggerAdapter
    """
    logger = logging.getLogger(name)

    if extra:
        return DoryLoggerAdapter(logger, extra)

    return logger
