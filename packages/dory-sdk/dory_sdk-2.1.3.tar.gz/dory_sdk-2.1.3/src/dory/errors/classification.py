"""
Error classification system for intelligent recovery strategies.

Classifies exceptions into categories and recommends appropriate recovery actions.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Type

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error classification types."""

    TRANSIENT = "transient"  # Temporary, retry likely to succeed
    PERMANENT = "permanent"  # Logic error, retry won't help
    RESOURCE = "resource"  # Resource exhaustion
    EXTERNAL = "external"  # External dependency failure
    LOGIC = "logic"  # Application logic error
    UNKNOWN = "unknown"  # Unclassified


class RecoveryAction(Enum):
    """Recommended recovery actions for error types."""

    RETRY = "retry"  # Retry with backoff
    CIRCUIT_BREAKER = "circuit_breaker"  # Use circuit breaker
    BACKOFF = "backoff"  # Exponential backoff
    SCALE = "scale"  # Scale resources
    GOLDEN_RESET = "golden_reset"  # Reset to golden image
    DEGRADE = "degrade"  # Enter degraded mode
    ALERT = "alert"  # Alert operator
    FAIL = "fail"  # Fail immediately
    LOG = "log"  # Log and continue


@dataclass
class ClassificationResult:
    """
    Result of error classification.

    Attributes:
        error_type: Classified error type
        recommended_action: Suggested recovery action
        retryable: Whether error should be retried
        severity: Error severity (low, medium, high, critical)
        details: Additional classification details
    """

    error_type: ErrorType
    recommended_action: RecoveryAction
    retryable: bool
    severity: str  # "low", "medium", "high", "critical"
    details: Optional[Dict] = None

    def __str__(self) -> str:
        return (
            f"Error: {self.error_type.value} | "
            f"Action: {self.recommended_action.value} | "
            f"Retryable: {self.retryable} | "
            f"Severity: {self.severity}"
        )


# Global error type registry
_ERROR_TYPE_REGISTRY: Dict[Type[Exception], ErrorType] = {}


def register_error_type(exception_class: Type[Exception], error_type: ErrorType):
    """
    Register custom exception type mapping.

    Example:
        register_error_type(MyCustomTimeout, ErrorType.TRANSIENT)
    """
    _ERROR_TYPE_REGISTRY[exception_class] = error_type
    logger.debug(f"Registered {exception_class.__name__} as {error_type.value}")


def clear_error_type_registry():
    """
    Clear all custom error type registrations.

    Useful for testing or resetting to default behavior.
    """
    _ERROR_TYPE_REGISTRY.clear()
    logger.debug("Cleared error type registry")


class ErrorClassifier:
    """
    Intelligent error classifier.

    Analyzes exceptions and recommends recovery strategies based on error type.

    Example:
        classifier = ErrorClassifier()

        try:
            await risky_operation()
        except Exception as e:
            result = classifier.classify(e)
            logger.info(f"Classification: {result}")

            if result.retryable:
                await retry_operation()
            elif result.recommended_action == RecoveryAction.CIRCUIT_BREAKER:
                await circuit_breaker.call(operation)
    """

    def __init__(self):
        # Initialize built-in error mappings
        self._initialize_builtin_mappings()

    def _initialize_builtin_mappings(self):
        """Initialize common Python exception mappings."""

        # Transient errors (network, timeouts)
        transient_errors = [
            "ConnectionError",
            "TimeoutError",
            "asyncio.TimeoutError",
            "aiohttp.ClientConnectionError",
            "aiohttp.ServerTimeoutError",
            "urllib3.exceptions.ConnectionError",
            "requests.exceptions.ConnectionError",
            "requests.exceptions.Timeout",
        ]

        # Permanent errors (logic, validation)
        permanent_errors = [
            "ValueError",
            "TypeError",
            "KeyError",
            "AttributeError",
            "NotImplementedError",
            "AssertionError",
        ]

        # Resource errors (memory, disk)
        resource_errors = [
            "MemoryError",
            "OSError",
            "IOError",
            "FileNotFoundError",
            "PermissionError",
        ]

        # External dependency errors
        external_errors = [
            "aiohttp.ClientError",
            "requests.exceptions.HTTPError",
            "kubernetes.client.exceptions.ApiException",
        ]

        # These are just strings for documentation
        # Actual classification happens in classify() method

    def classify(self, error: Exception) -> ClassificationResult:
        """
        Classify an exception and recommend recovery strategy.

        Args:
            error: The exception to classify

        Returns:
            ClassificationResult with error type and recovery action
        """
        error_type = self._determine_error_type(error)
        recommended_action = self._recommend_action(error_type, error)
        retryable = self._is_retryable(error_type)
        severity = self._determine_severity(error_type, error)

        result = ClassificationResult(
            error_type=error_type,
            recommended_action=recommended_action,
            retryable=retryable,
            severity=severity,
            details={
                "exception_type": type(error).__name__,
                "message": str(error),
            },
        )

        logger.debug(f"Classified {type(error).__name__}: {result}")
        return result

    def _determine_error_type(self, error: Exception) -> ErrorType:
        """Determine error type from exception."""

        # Check custom registry first
        error_class = type(error)
        if error_class in _ERROR_TYPE_REGISTRY:
            return _ERROR_TYPE_REGISTRY[error_class]

        error_name = error_class.__name__
        error_str = str(error).lower()

        # Transient errors (network, timeout)
        if any(
            pattern in error_name.lower()
            for pattern in ["timeout", "connection", "network"]
        ):
            return ErrorType.TRANSIENT

        if any(pattern in error_str for pattern in ["timeout", "connection refused"]):
            return ErrorType.TRANSIENT

        # Resource errors
        if any(
            pattern in error_name.lower()
            for pattern in ["memory", "resource", "disk", "quota"]
        ):
            return ErrorType.RESOURCE

        if any(
            pattern in error_str
            for pattern in ["out of memory", "disk full", "quota exceeded"]
        ):
            return ErrorType.RESOURCE

        # External dependency errors
        if any(
            pattern in error_name.lower()
            for pattern in ["http", "api", "client", "server"]
        ):
            # Check status codes for transient vs permanent
            if any(
                pattern in error_str
                for pattern in ["500", "502", "503", "504", "429"]
            ):
                return ErrorType.EXTERNAL  # Server errors - use circuit breaker

            if any(pattern in error_str for pattern in ["400", "401", "403", "404"]):
                return ErrorType.PERMANENT  # Client errors - don't retry

            return ErrorType.EXTERNAL

        # Logic errors (validation, type errors)
        if any(
            pattern in error_name.lower()
            for pattern in [
                "value",
                "type",
                "key",
                "attribute",
                "assertion",
                "notimplemented",
            ]
        ):
            return ErrorType.LOGIC

        # Permanent errors (state corruption, etc.)
        if any(
            pattern in error_str for pattern in ["corrupt", "invalid state", "integrity"]
        ):
            return ErrorType.PERMANENT

        return ErrorType.UNKNOWN

    def _recommend_action(
        self, error_type: ErrorType, error: Exception
    ) -> RecoveryAction:
        """Recommend recovery action based on error type."""

        action_map = {
            ErrorType.TRANSIENT: RecoveryAction.RETRY,
            ErrorType.EXTERNAL: RecoveryAction.CIRCUIT_BREAKER,
            ErrorType.RESOURCE: RecoveryAction.BACKOFF,
            ErrorType.LOGIC: RecoveryAction.ALERT,
            ErrorType.PERMANENT: RecoveryAction.GOLDEN_RESET,
            ErrorType.UNKNOWN: RecoveryAction.LOG,
        }

        return action_map.get(error_type, RecoveryAction.LOG)

    def _is_retryable(self, error_type: ErrorType) -> bool:
        """Determine if error should be retried."""

        retryable_types = {
            ErrorType.TRANSIENT,
            ErrorType.EXTERNAL,
            ErrorType.RESOURCE,
        }

        return error_type in retryable_types

    def _determine_severity(self, error_type: ErrorType, error: Exception) -> str:
        """Determine error severity."""

        severity_map = {
            ErrorType.TRANSIENT: "low",
            ErrorType.EXTERNAL: "medium",
            ErrorType.RESOURCE: "high",
            ErrorType.LOGIC: "high",
            ErrorType.PERMANENT: "critical",
            ErrorType.UNKNOWN: "medium",
        }

        return severity_map.get(error_type, "medium")

    def classify_and_handle(self, error: Exception) -> ClassificationResult:
        """
        Classify error and automatically log appropriate message.

        Args:
            error: The exception to classify

        Returns:
            ClassificationResult
        """
        result = self.classify(error)

        # Log based on severity
        log_message = f"{result.error_type.value.upper()} error: {type(error).__name__}: {error}"

        if result.severity == "critical":
            logger.error(log_message)
        elif result.severity == "high":
            logger.warning(log_message)
        elif result.severity == "medium":
            logger.info(log_message)
        else:
            logger.debug(log_message)

        logger.info(f"Recommended action: {result.recommended_action.value}")

        return result


# Global classifier instance
_global_classifier = ErrorClassifier()


def classify_error(error: Exception) -> ClassificationResult:
    """
    Convenience function for global error classification.

    Args:
        error: Exception to classify

    Returns:
        ClassificationResult
    """
    return _global_classifier.classify(error)


def is_retryable(error: Exception) -> bool:
    """
    Quick check if error is retryable.

    Args:
        error: Exception to check

    Returns:
        True if error should be retried
    """
    result = classify_error(error)
    return result.retryable
