"""
Structured Error Code System for Dory SDK

This module defines a comprehensive error code system for the Dory SDK,
providing structured, searchable error codes for debugging and monitoring.

Error Code Format: E-<DOMAIN>-<NUMBER>
- DOMAIN: 3-letter code identifying the module/domain
- NUMBER: 3-digit unique identifier

Example: E-RET-001 (Retry domain, error #1)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ErrorDomain(str, Enum):
    """Error domains for categorizing errors."""

    # Core SDK
    CORE = "COR"  # Core SDK functionality
    STATE = "STA"  # State management
    MIGRATION = "MIG"  # Migration operations

    # Resilience
    RETRY = "RET"  # Retry logic
    CIRCUIT_BREAKER = "CBR"  # Circuit breaker
    ERROR_CLASS = "ECL"  # Error classification

    # Recovery
    GOLDEN_IMAGE = "GLD"  # Golden image/snapshots
    RECOVERY = "REC"  # Recovery operations
    VALIDATION = "VAL"  # Validation

    # Processing
    PROCESSOR = "PRC"  # Processor operations
    MODE = "MOD"  # Processing modes
    QUEUE = "QUE"  # Queue operations

    # Monitoring
    METRICS = "MET"  # Metrics collection
    HEALTH = "HLT"  # Health checks
    TELEMETRY = "TEL"  # OpenTelemetry

    # Infrastructure
    KUBERNETES = "K8S"  # Kubernetes operations
    STORAGE = "STO"  # Storage operations
    NETWORK = "NET"  # Network operations

    # Middleware
    REQUEST = "REQ"  # Request tracking
    CONNECTION = "CON"  # Connection management
    SESSION = "SES"  # Session management


@dataclass(frozen=True)
class ErrorCode:
    """Represents a structured error code."""

    domain: ErrorDomain
    number: int
    message: str
    description: str
    remediation: str
    severity: str = "ERROR"

    @property
    def code(self) -> str:
        """Get formatted error code (e.g., E-RET-001)."""
        return f"E-{self.domain.value}-{self.number:03d}"

    def __str__(self) -> str:
        """String representation of error code."""
        return f"[{self.code}] {self.message}"

    def format_full(self) -> str:
        """Get full formatted error message."""
        return f"""
Error Code: {self.code}
Severity: {self.severity}
Message: {self.message}
Description: {self.description}
Remediation: {self.remediation}
        """.strip()


# ============================================================================
# RETRY ERRORS (E-RET-xxx)
# ============================================================================

E_RET_001 = ErrorCode(
    domain=ErrorDomain.RETRY,
    number=1,
    message="Retry budget exhausted",
    description="The retry budget has been depleted. No more retries are allowed.",
    remediation="Wait for budget to replenish or increase max_retry_budget.",
    severity="ERROR",
)

E_RET_002 = ErrorCode(
    domain=ErrorDomain.RETRY,
    number=2,
    message="Max retry attempts exceeded",
    description="Operation failed after maximum retry attempts.",
    remediation="Check operation logic and increase max_attempts if appropriate.",
    severity="ERROR",
)

E_RET_003 = ErrorCode(
    domain=ErrorDomain.RETRY,
    number=3,
    message="Backoff timeout exceeded",
    description="Total backoff time exceeded max_backoff_time.",
    remediation="Increase max_backoff_time or reduce initial_delay/max_delay.",
    severity="ERROR",
)

# ============================================================================
# CIRCUIT BREAKER ERRORS (E-CBR-xxx)
# ============================================================================

E_CBR_001 = ErrorCode(
    domain=ErrorDomain.CIRCUIT_BREAKER,
    number=1,
    message="Circuit breaker is OPEN",
    description="Circuit breaker is open due to high failure rate. Requests are being rejected.",
    remediation="Wait for circuit breaker to enter HALF_OPEN state or manually reset.",
    severity="WARNING",
)

E_CBR_002 = ErrorCode(
    domain=ErrorDomain.CIRCUIT_BREAKER,
    number=2,
    message="Circuit breaker transition failed",
    description="Failed to transition circuit breaker state.",
    remediation="Check circuit breaker configuration and state consistency.",
    severity="ERROR",
)

E_CBR_003 = ErrorCode(
    domain=ErrorDomain.CIRCUIT_BREAKER,
    number=3,
    message="Failure threshold exceeded",
    description="Operation failures exceeded the circuit breaker threshold.",
    remediation="Investigate underlying failures and adjust failure_threshold if needed.",
    severity="WARNING",
)

# ============================================================================
# ERROR CLASSIFICATION ERRORS (E-ECL-xxx)
# ============================================================================

E_ECL_001 = ErrorCode(
    domain=ErrorDomain.ERROR_CLASS,
    number=1,
    message="Unable to classify error",
    description="Error classification failed - error type could not be determined.",
    remediation="Add error pattern to classifier or handle as UNKNOWN type.",
    severity="WARNING",
)

E_ECL_002 = ErrorCode(
    domain=ErrorDomain.ERROR_CLASS,
    number=2,
    message="Error classification confidence low",
    description="Error was classified but with low confidence score.",
    remediation="Review error patterns and improve classification rules.",
    severity="INFO",
)

# ============================================================================
# GOLDEN IMAGE ERRORS (E-GLD-xxx)
# ============================================================================

E_GLD_001 = ErrorCode(
    domain=ErrorDomain.GOLDEN_IMAGE,
    number=1,
    message="Golden snapshot capture failed",
    description="Failed to capture golden state snapshot.",
    remediation="Check storage permissions and available space.",
    severity="ERROR",
)

E_GLD_002 = ErrorCode(
    domain=ErrorDomain.GOLDEN_IMAGE,
    number=2,
    message="Golden snapshot restore failed",
    description="Failed to restore state from golden snapshot.",
    remediation="Verify snapshot integrity and compatibility with current version.",
    severity="ERROR",
)

E_GLD_003 = ErrorCode(
    domain=ErrorDomain.GOLDEN_IMAGE,
    number=3,
    message="Snapshot checksum mismatch",
    description="Snapshot checksum verification failed - data may be corrupted.",
    remediation="Recapture snapshot or restore from backup.",
    severity="CRITICAL",
)

E_GLD_004 = ErrorCode(
    domain=ErrorDomain.GOLDEN_IMAGE,
    number=4,
    message="Snapshot compression failed",
    description="Failed to compress snapshot data.",
    remediation="Check available memory and disk space.",
    severity="ERROR",
)

E_GLD_005 = ErrorCode(
    domain=ErrorDomain.GOLDEN_IMAGE,
    number=5,
    message="Graduated reset failed",
    description="All graduated reset levels failed to restore state.",
    remediation="Manual intervention required - check logs for specific failures.",
    severity="CRITICAL",
)

# ============================================================================
# VALIDATION ERRORS (E-VAL-xxx)
# ============================================================================

E_VAL_001 = ErrorCode(
    domain=ErrorDomain.VALIDATION,
    number=1,
    message="State validation failed",
    description="State validation found critical issues.",
    remediation="Review validation errors and fix state data.",
    severity="ERROR",
)

E_VAL_002 = ErrorCode(
    domain=ErrorDomain.VALIDATION,
    number=2,
    message="Schema validation failed",
    description="State does not match expected schema.",
    remediation="Update state to match schema or update schema definition.",
    severity="ERROR",
)

E_VAL_003 = ErrorCode(
    domain=ErrorDomain.VALIDATION,
    number=3,
    message="Dependency validation failed",
    description="Required dependencies are missing or invalid.",
    remediation="Ensure all required dependencies are present and valid.",
    severity="ERROR",
)

# ============================================================================
# PROCESSING MODE ERRORS (E-MOD-xxx)
# ============================================================================

E_MOD_001 = ErrorCode(
    domain=ErrorDomain.MODE,
    number=1,
    message="Mode transition failed",
    description="Failed to transition to target processing mode.",
    remediation="Check mode transition preconditions and system state.",
    severity="ERROR",
)

E_MOD_002 = ErrorCode(
    domain=ErrorDomain.MODE,
    number=2,
    message="Invalid mode for operation",
    description="Operation not available in current processing mode.",
    remediation="Wait for mode transition or use degraded operation variant.",
    severity="WARNING",
)

E_MOD_003 = ErrorCode(
    domain=ErrorDomain.MODE,
    number=3,
    message="Mode auto-recovery failed",
    description="Automatic mode recovery did not succeed.",
    remediation="Manual intervention required to restore normal mode.",
    severity="ERROR",
)

# ============================================================================
# REQUEST TRACKING ERRORS (E-REQ-xxx)
# ============================================================================

E_REQ_001 = ErrorCode(
    domain=ErrorDomain.REQUEST,
    number=1,
    message="Request tracking initialization failed",
    description="Failed to initialize request tracking.",
    remediation="Check RequestTracker configuration and retry.",
    severity="WARNING",
)

E_REQ_002 = ErrorCode(
    domain=ErrorDomain.REQUEST,
    number=2,
    message="Request timeout exceeded",
    description="Request exceeded configured timeout duration.",
    remediation="Increase timeout or optimize request processing.",
    severity="WARNING",
)

# ============================================================================
# CONNECTION ERRORS (E-CON-xxx)
# ============================================================================

E_CON_001 = ErrorCode(
    domain=ErrorDomain.CONNECTION,
    number=1,
    message="Connection health check failed",
    description="Connection failed health check.",
    remediation="Verify connection is alive and responsive.",
    severity="WARNING",
)

E_CON_002 = ErrorCode(
    domain=ErrorDomain.CONNECTION,
    number=2,
    message="Connection idle timeout",
    description="Connection closed due to idle timeout.",
    remediation="Increase idle_timeout or ensure connection is actively used.",
    severity="INFO",
)

E_CON_003 = ErrorCode(
    domain=ErrorDomain.CONNECTION,
    number=3,
    message="Connection registration failed",
    description="Failed to register connection with tracker.",
    remediation="Check connection is valid and tracker is initialized.",
    severity="ERROR",
)

# ============================================================================
# STATE MANAGEMENT ERRORS (E-STA-xxx)
# ============================================================================

E_STA_001 = ErrorCode(
    domain=ErrorDomain.STATE,
    number=1,
    message="State serialization failed",
    description="Failed to serialize state data.",
    remediation="Ensure state contains only serializable types.",
    severity="ERROR",
)

E_STA_002 = ErrorCode(
    domain=ErrorDomain.STATE,
    number=2,
    message="State deserialization failed",
    description="Failed to deserialize state data.",
    remediation="Verify state format and version compatibility.",
    severity="ERROR",
)

E_STA_003 = ErrorCode(
    domain=ErrorDomain.STATE,
    number=3,
    message="State corruption detected",
    description="State data appears to be corrupted.",
    remediation="Restore from golden snapshot or recapture state.",
    severity="CRITICAL",
)

# ============================================================================
# ERROR CODE REGISTRY
# ============================================================================


class ErrorCodeRegistry:
    """Registry for all error codes."""

    _codes: Dict[str, ErrorCode] = {}

    @classmethod
    def register(cls, error_code: ErrorCode) -> None:
        """Register an error code."""
        cls._codes[error_code.code] = error_code

    @classmethod
    def get(cls, code: str) -> Optional[ErrorCode]:
        """Get error code by code string."""
        return cls._codes.get(code)

    @classmethod
    def search(cls, query: str) -> list[ErrorCode]:
        """Search error codes by message or description."""
        query_lower = query.lower()
        return [
            code
            for code in cls._codes.values()
            if query_lower in code.message.lower()
            or query_lower in code.description.lower()
        ]

    @classmethod
    def list_by_domain(cls, domain: ErrorDomain) -> list[ErrorCode]:
        """List all error codes for a domain."""
        return [code for code in cls._codes.values() if code.domain == domain]

    @classmethod
    def all(cls) -> list[ErrorCode]:
        """Get all registered error codes."""
        return sorted(cls._codes.values(), key=lambda c: c.code)


# Auto-register all error codes defined in this module
_error_codes = [
    # Retry
    E_RET_001,
    E_RET_002,
    E_RET_003,
    # Circuit Breaker
    E_CBR_001,
    E_CBR_002,
    E_CBR_003,
    # Error Classification
    E_ECL_001,
    E_ECL_002,
    # Golden Image
    E_GLD_001,
    E_GLD_002,
    E_GLD_003,
    E_GLD_004,
    E_GLD_005,
    # Validation
    E_VAL_001,
    E_VAL_002,
    E_VAL_003,
    # Processing Mode
    E_MOD_001,
    E_MOD_002,
    E_MOD_003,
    # Request Tracking
    E_REQ_001,
    E_REQ_002,
    # Connection
    E_CON_001,
    E_CON_002,
    E_CON_003,
    # State Management
    E_STA_001,
    E_STA_002,
    E_STA_003,
]

for _code in _error_codes:
    ErrorCodeRegistry.register(_code)


# ============================================================================
# ERROR CODE EXCEPTIONS
# ============================================================================


class DoryError(Exception):
    """Base exception with error code support."""

    def __init__(
        self,
        error_code: ErrorCode,
        details: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize error with code.

        Args:
            error_code: The error code
            details: Additional context-specific details
            cause: Original exception that caused this error
        """
        self.error_code = error_code
        self.details = details
        self.cause = cause

        message = str(error_code)
        if details:
            message += f"\nDetails: {details}"
        if cause:
            message += f"\nCause: {cause}"

        super().__init__(message)

    def format_full(self) -> str:
        """Get full formatted error message."""
        msg = self.error_code.format_full()
        if self.details:
            msg += f"\n\nAdditional Details:\n{self.details}"
        if self.cause:
            msg += f"\n\nCaused by:\n{self.cause}"
        return msg
