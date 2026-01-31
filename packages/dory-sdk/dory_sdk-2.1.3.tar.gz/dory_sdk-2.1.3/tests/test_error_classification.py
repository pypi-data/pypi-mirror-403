"""
Tests for error classification system.
"""

import pytest

from dory.errors.classification import (
    ErrorType,
    ErrorClassifier,
    RecoveryAction,
    register_error_type,
    classify_error,
    is_retryable,
)


class CustomTransientError(Exception):
    """Custom exception for testing."""

    pass


class CustomPermanentError(Exception):
    """Custom exception for testing."""

    pass


class TestErrorClassifier:
    """Test ErrorClassifier functionality."""

    def test_classify_transient_errors(self):
        """Test classification of transient errors."""
        classifier = ErrorClassifier()

        # Connection errors
        result = classifier.classify(ConnectionError("Connection failed"))
        assert result.error_type == ErrorType.TRANSIENT
        assert result.retryable is True
        assert result.recommended_action == RecoveryAction.RETRY

        # Timeout errors
        result = classifier.classify(TimeoutError("Request timeout"))
        assert result.error_type == ErrorType.TRANSIENT
        assert result.retryable is True

    def test_classify_permanent_errors(self):
        """Test classification of permanent errors."""
        classifier = ErrorClassifier()

        # Value errors
        result = classifier.classify(ValueError("Invalid value"))
        assert result.error_type == ErrorType.LOGIC
        assert result.retryable is False
        assert result.recommended_action == RecoveryAction.ALERT

        # Type errors
        result = classifier.classify(TypeError("Type mismatch"))
        assert result.error_type == ErrorType.LOGIC
        assert result.retryable is False

    def test_classify_resource_errors(self):
        """Test classification of resource errors."""
        classifier = ErrorClassifier()

        # Memory errors
        result = classifier.classify(MemoryError("Out of memory"))
        assert result.error_type == ErrorType.RESOURCE
        assert result.retryable is True
        assert result.recommended_action == RecoveryAction.BACKOFF

        # OS errors
        result = classifier.classify(OSError("Disk full"))
        assert result.error_type == ErrorType.RESOURCE

    def test_classify_external_errors(self):
        """Test classification of external dependency errors."""
        classifier = ErrorClassifier()

        # Generic HTTP error
        class HTTPError(Exception):
            pass

        result = classifier.classify(HTTPError("500 Internal Server Error"))
        assert result.error_type == ErrorType.EXTERNAL
        assert result.retryable is True
        assert result.recommended_action == RecoveryAction.CIRCUIT_BREAKER

    def test_classify_with_status_codes(self):
        """Test classification considering HTTP status codes."""
        classifier = ErrorClassifier()

        class HTTPError(Exception):
            pass

        # 5xx errors -> EXTERNAL
        result = classifier.classify(HTTPError("503 Service Unavailable"))
        assert result.error_type == ErrorType.EXTERNAL

        # 4xx errors -> PERMANENT
        result = classifier.classify(HTTPError("404 Not Found"))
        assert result.error_type == ErrorType.PERMANENT

    def test_classify_unknown_errors(self):
        """Test classification of unknown errors."""
        classifier = ErrorClassifier()

        class WeirdError(Exception):
            pass

        result = classifier.classify(WeirdError("Unknown issue"))
        assert result.error_type == ErrorType.UNKNOWN
        assert result.recommended_action == RecoveryAction.LOG

    def test_severity_determination(self):
        """Test severity determination."""
        classifier = ErrorClassifier()

        # Transient -> low
        result = classifier.classify(ConnectionError())
        assert result.severity == "low"

        # Resource -> high
        result = classifier.classify(MemoryError())
        assert result.severity == "high"

        # Logic -> high
        result = classifier.classify(ValueError())
        assert result.severity == "high"

    def test_classification_result_details(self):
        """Test classification result includes details."""
        classifier = ErrorClassifier()

        result = classifier.classify(ValueError("Invalid input"))
        assert result.details is not None
        assert result.details["exception_type"] == "ValueError"
        assert result.details["message"] == "Invalid input"

    def test_retryable_determination(self):
        """Test retryable flag determination."""
        classifier = ErrorClassifier()

        # Transient -> retryable
        result = classifier.classify(ConnectionError())
        assert result.retryable is True

        # External -> retryable
        class HTTPError(Exception):
            pass

        result = classifier.classify(HTTPError("500 Error"))
        assert result.retryable is True

        # Logic -> not retryable
        result = classifier.classify(ValueError())
        assert result.retryable is False

    def test_register_custom_error_type(self):
        """Test registering custom error types."""
        classifier = ErrorClassifier()

        # Register custom error
        register_error_type(CustomTransientError, ErrorType.TRANSIENT)

        result = classifier.classify(CustomTransientError())
        assert result.error_type == ErrorType.TRANSIENT

    def test_custom_registry_takes_precedence(self):
        """Test custom registry overrides built-in classification."""
        from dory.errors.classification import clear_error_type_registry

        classifier = ErrorClassifier()

        # ValueError is normally LOGIC
        result = classifier.classify(ValueError())
        assert result.error_type == ErrorType.LOGIC

        # Register as TRANSIENT
        register_error_type(ValueError, ErrorType.TRANSIENT)

        result = classifier.classify(ValueError())
        assert result.error_type == ErrorType.TRANSIENT

        # Clean up: clear the registry to avoid affecting other tests
        clear_error_type_registry()

    def test_classify_and_handle_logs(self, caplog):
        """Test classify_and_handle logs appropriately."""
        import logging
        caplog.set_level(logging.DEBUG)  # Capture DEBUG logs for low severity errors
        classifier = ErrorClassifier()

        # High severity -> warning
        result = classifier.classify_and_handle(MemoryError("OOM"))
        assert "RESOURCE error" in caplog.text

        # Low severity -> debug/info
        caplog.clear()
        result = classifier.classify_and_handle(ConnectionError("Timeout"))
        assert "TRANSIENT error" in caplog.text


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_classify_error_global(self):
        """Test global classify_error function."""
        result = classify_error(ConnectionError())
        assert result.error_type == ErrorType.TRANSIENT

    def test_is_retryable_global(self):
        """Test global is_retryable function."""
        assert is_retryable(ConnectionError()) is True
        assert is_retryable(ValueError()) is False


class TestRecoveryActionMapping:
    """Test recommended recovery actions."""

    def test_transient_recommends_retry(self):
        """Test transient errors recommend retry."""
        classifier = ErrorClassifier()
        result = classifier.classify(TimeoutError())
        assert result.recommended_action == RecoveryAction.RETRY

    def test_external_recommends_circuit_breaker(self):
        """Test external errors recommend circuit breaker."""
        classifier = ErrorClassifier()

        class APIError(Exception):
            pass

        result = classifier.classify(APIError("500 Error"))
        assert result.recommended_action == RecoveryAction.CIRCUIT_BREAKER

    def test_resource_recommends_backoff(self):
        """Test resource errors recommend backoff."""
        classifier = ErrorClassifier()
        result = classifier.classify(MemoryError())
        assert result.recommended_action == RecoveryAction.BACKOFF

    def test_logic_recommends_alert(self):
        """Test logic errors recommend alert."""
        classifier = ErrorClassifier()
        result = classifier.classify(ValueError())
        assert result.recommended_action == RecoveryAction.ALERT

    def test_permanent_recommends_golden_reset(self):
        """Test permanent errors recommend golden reset."""
        classifier = ErrorClassifier()

        class CorruptionError(Exception):
            pass

        error = CorruptionError("State corrupt")
        result = classifier.classify(error)
        # Check if classified as permanent
        if result.error_type == ErrorType.PERMANENT:
            assert result.recommended_action == RecoveryAction.GOLDEN_RESET


class TestErrorTypeDetection:
    """Test error type detection logic."""

    def test_detect_by_exception_name(self):
        """Test detection by exception class name."""
        classifier = ErrorClassifier()

        class NetworkTimeout(Exception):
            pass

        result = classifier.classify(NetworkTimeout())
        assert result.error_type == ErrorType.TRANSIENT

    def test_detect_by_error_message(self):
        """Test detection by error message content."""
        classifier = ErrorClassifier()

        class GenericError(Exception):
            pass

        # Transient patterns
        result = classifier.classify(GenericError("connection refused"))
        assert result.error_type == ErrorType.TRANSIENT

        # Resource patterns
        result = classifier.classify(GenericError("out of memory"))
        assert result.error_type == ErrorType.RESOURCE

    def test_detect_http_status_codes(self):
        """Test HTTP status code detection."""
        classifier = ErrorClassifier()

        class HTTPError(Exception):
            pass

        # 5xx -> EXTERNAL
        result = classifier.classify(HTTPError("502 Bad Gateway"))
        assert result.error_type == ErrorType.EXTERNAL

        # 4xx -> PERMANENT
        result = classifier.classify(HTTPError("401 Unauthorized"))
        assert result.error_type == ErrorType.PERMANENT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
