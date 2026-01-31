"""
Error classification and handling for Dory SDK.

Provides intelligent error classification to determine appropriate recovery strategies.

Error types:
- TRANSIENT: Temporary failures (network, timeout) - retry
- PERMANENT: Logic errors (validation, not found) - don't retry
- RESOURCE: Resource exhaustion (memory, disk) - backoff + scale
- EXTERNAL: External dependency failures - circuit breaker
- LOGIC: Application logic errors - fix code

Usage:
    from dory.errors import ErrorClassifier, ErrorType

    classifier = ErrorClassifier()
    error_type = classifier.classify(exception)

    if error_type == ErrorType.TRANSIENT:
        # Retry the operation
        await retry_operation()
    elif error_type == ErrorType.EXTERNAL:
        # Use circuit breaker
        await circuit_breaker.call(operation)
"""

from .classification import (
    ErrorType,
    ErrorClassifier,
    ClassificationResult,
    RecoveryAction,
    register_error_type,
)
from .codes import (
    ErrorCode,
    ErrorDomain,
    ErrorCodeRegistry,
    DoryError,
    # Retry errors
    E_RET_001,
    E_RET_002,
    E_RET_003,
    # Circuit breaker errors
    E_CBR_001,
    E_CBR_002,
    E_CBR_003,
    # Error classification errors
    E_ECL_001,
    E_ECL_002,
    # Golden image errors
    E_GLD_001,
    E_GLD_002,
    E_GLD_003,
    E_GLD_004,
    E_GLD_005,
    # Validation errors
    E_VAL_001,
    E_VAL_002,
    E_VAL_003,
    # Processing mode errors
    E_MOD_001,
    E_MOD_002,
    E_MOD_003,
    # Request tracking errors
    E_REQ_001,
    E_REQ_002,
    # Connection errors
    E_CON_001,
    E_CON_002,
    E_CON_003,
    # State management errors
    E_STA_001,
    E_STA_002,
    E_STA_003,
)

__all__ = [
    # Classification
    "ErrorType",
    "ErrorClassifier",
    "ClassificationResult",
    "RecoveryAction",
    "register_error_type",
    # Error codes
    "ErrorCode",
    "ErrorDomain",
    "ErrorCodeRegistry",
    "DoryError",
    # Specific error codes
    "E_RET_001",
    "E_RET_002",
    "E_RET_003",
    "E_CBR_001",
    "E_CBR_002",
    "E_CBR_003",
    "E_ECL_001",
    "E_ECL_002",
    "E_GLD_001",
    "E_GLD_002",
    "E_GLD_003",
    "E_GLD_004",
    "E_GLD_005",
    "E_VAL_001",
    "E_VAL_002",
    "E_VAL_003",
    "E_MOD_001",
    "E_MOD_002",
    "E_MOD_003",
    "E_REQ_001",
    "E_REQ_002",
    "E_CON_001",
    "E_CON_002",
    "E_CON_003",
    "E_STA_001",
    "E_STA_002",
    "E_STA_003",
]
