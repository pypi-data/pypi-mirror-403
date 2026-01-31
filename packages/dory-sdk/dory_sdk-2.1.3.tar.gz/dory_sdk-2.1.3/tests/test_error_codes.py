"""
Tests for error code system.
"""

import pytest

from dory.errors import (
    ErrorCode,
    ErrorDomain,
    ErrorCodeRegistry,
    DoryError,
    E_RET_001,
    E_CBR_001,
    E_GLD_001,
    E_GLD_003,
)


class TestErrorCode:
    """Test ErrorCode functionality."""

    def test_error_code_formatting(self):
        """Test error code formatting."""
        assert E_RET_001.code == "E-RET-001"
        assert E_CBR_001.code == "E-CBR-001"
        assert E_GLD_001.code == "E-GLD-001"

    def test_error_code_string(self):
        """Test error code string representation."""
        error_str = str(E_RET_001)
        assert "E-RET-001" in error_str
        assert "Retry budget exhausted" in error_str

    def test_error_code_full_format(self):
        """Test full error code formatting."""
        full = E_RET_001.format_full()
        assert "E-RET-001" in full
        assert "Retry budget exhausted" in full
        assert "Wait for budget to replenish" in full
        assert "ERROR" in full

    def test_error_code_immutability(self):
        """Test that error codes are immutable."""
        with pytest.raises(Exception):  # FrozenInstanceError
            E_RET_001.message = "New message"  # type: ignore


class TestErrorCodeRegistry:
    """Test ErrorCodeRegistry functionality."""

    def test_registry_get(self):
        """Test getting error codes from registry."""
        code = ErrorCodeRegistry.get("E-RET-001")
        assert code is not None
        assert code.code == "E-RET-001"
        assert code.message == "Retry budget exhausted"

    def test_registry_get_nonexistent(self):
        """Test getting nonexistent error code."""
        code = ErrorCodeRegistry.get("E-XXX-999")
        assert code is None

    def test_registry_search(self):
        """Test searching error codes."""
        # Search by message
        results = ErrorCodeRegistry.search("retry")
        assert len(results) > 0
        assert any("retry" in r.message.lower() for r in results)

        # Search by description
        results = ErrorCodeRegistry.search("budget")
        assert len(results) > 0

    def test_registry_list_by_domain(self):
        """Test listing error codes by domain."""
        retry_codes = ErrorCodeRegistry.list_by_domain(ErrorDomain.RETRY)
        assert len(retry_codes) >= 3
        assert all(code.domain == ErrorDomain.RETRY for code in retry_codes)

        cbr_codes = ErrorCodeRegistry.list_by_domain(ErrorDomain.CIRCUIT_BREAKER)
        assert len(cbr_codes) >= 3
        assert all(code.domain == ErrorDomain.CIRCUIT_BREAKER for code in cbr_codes)

    def test_registry_all(self):
        """Test getting all error codes."""
        all_codes = ErrorCodeRegistry.all()
        assert len(all_codes) > 0
        # Verify sorted by code
        codes_list = [c.code for c in all_codes]
        assert codes_list == sorted(codes_list)


class TestDoryError:
    """Test DoryError exception."""

    def test_basic_error(self):
        """Test basic DoryError creation."""
        error = DoryError(E_RET_001)
        assert error.error_code == E_RET_001
        assert "E-RET-001" in str(error)
        assert "Retry budget exhausted" in str(error)

    def test_error_with_details(self):
        """Test DoryError with additional details."""
        error = DoryError(E_RET_001, details="Current budget: 0/100")
        assert "Current budget: 0/100" in str(error)

    def test_error_with_cause(self):
        """Test DoryError with cause exception."""
        cause = ValueError("Original error")
        error = DoryError(E_RET_001, cause=cause)
        assert error.cause == cause
        assert "Original error" in str(error)

    def test_error_with_all_fields(self):
        """Test DoryError with all fields."""
        cause = ValueError("Original error")
        error = DoryError(
            E_RET_001, details="Additional context", cause=cause
        )
        assert error.error_code == E_RET_001
        assert error.details == "Additional context"
        assert error.cause == cause

    def test_error_full_format(self):
        """Test full error formatting."""
        cause = ValueError("Original error")
        error = DoryError(
            E_RET_001, details="Additional context", cause=cause
        )
        full = error.format_full()
        assert "E-RET-001" in full
        assert "Retry budget exhausted" in full
        assert "Additional context" in full
        assert "Original error" in full

    def test_error_can_be_raised(self):
        """Test that DoryError can be raised and caught."""
        with pytest.raises(DoryError) as exc_info:
            raise DoryError(E_RET_001)

        assert exc_info.value.error_code == E_RET_001


class TestErrorDomains:
    """Test error domain definitions."""

    def test_all_domains_defined(self):
        """Test that all expected domains are defined."""
        expected_domains = [
            "COR",  # Core
            "STA",  # State
            "MIG",  # Migration
            "RET",  # Retry
            "CBR",  # Circuit Breaker
            "ECL",  # Error Classification
            "GLD",  # Golden Image
            "REC",  # Recovery
            "VAL",  # Validation
            "PRC",  # Processor
            "MOD",  # Mode
            "QUE",  # Queue
            "MET",  # Metrics
            "HLT",  # Health
            "TEL",  # Telemetry
            "K8S",  # Kubernetes
            "STO",  # Storage
            "NET",  # Network
            "REQ",  # Request
            "CON",  # Connection
            "SES",  # Session
        ]

        domain_values = [d.value for d in ErrorDomain]
        for expected in expected_domains:
            assert expected in domain_values

    def test_domain_uniqueness(self):
        """Test that all domain codes are unique."""
        domain_values = [d.value for d in ErrorDomain]
        assert len(domain_values) == len(set(domain_values))


class TestSpecificErrorCodes:
    """Test specific error code definitions."""

    def test_retry_errors(self):
        """Test retry error codes."""
        assert E_RET_001.domain == ErrorDomain.RETRY
        assert E_RET_001.number == 1
        assert "budget" in E_RET_001.message.lower()

    def test_circuit_breaker_errors(self):
        """Test circuit breaker error codes."""
        assert E_CBR_001.domain == ErrorDomain.CIRCUIT_BREAKER
        assert E_CBR_001.number == 1
        assert "open" in E_CBR_001.message.lower()
        assert E_CBR_001.severity == "WARNING"

    def test_golden_image_errors(self):
        """Test golden image error codes."""
        assert E_GLD_001.domain == ErrorDomain.GOLDEN_IMAGE
        assert E_GLD_001.number == 1
        assert "capture" in E_GLD_001.message.lower()

    def test_error_severity_levels(self):
        """Test that errors have appropriate severity levels."""
        # Critical errors
        assert E_GLD_003.severity == "CRITICAL"  # Checksum mismatch

        # Errors
        assert E_RET_001.severity == "ERROR"  # Budget exhausted

        # Warnings
        assert E_CBR_001.severity == "WARNING"  # Circuit open


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
