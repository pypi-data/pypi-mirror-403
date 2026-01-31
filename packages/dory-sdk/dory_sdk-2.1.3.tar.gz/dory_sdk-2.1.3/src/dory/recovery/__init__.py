"""Recovery and fault handling modules."""

from dory.recovery.restart_detector import RestartDetector, RestartInfo
from dory.recovery.state_validator import StateValidator
from dory.recovery.golden_image import GoldenImageManager, ResetLevel, ResetResult, CacheResetManager
from dory.recovery.recovery_decision import RecoveryDecisionMaker, RecoveryDecision
from dory.recovery.golden_snapshot import (
    GoldenSnapshotManager,
    Snapshot,
    SnapshotMetadata,
    SnapshotStorageError,
    SnapshotValidationError,
    SnapshotFormat,
)
from dory.recovery.golden_validator import (
    GoldenValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from dory.recovery.partial_recovery import (
    PartialRecoveryManager,
    RecoveryResult as PartialRecoveryResult,
    FieldRecovery,
    FieldStatus,
    numeric_recovery_strategy,
    string_recovery_strategy,
    list_recovery_strategy,
    dict_recovery_strategy,
)

__all__ = [
    "RestartDetector",
    "RestartInfo",
    "StateValidator",
    "GoldenImageManager",
    "ResetLevel",
    "ResetResult",
    "CacheResetManager",
    "RecoveryDecisionMaker",
    "RecoveryDecision",
    "GoldenSnapshotManager",
    "Snapshot",
    "SnapshotMetadata",
    "SnapshotStorageError",
    "SnapshotValidationError",
    "SnapshotFormat",
    "GoldenValidator",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    "PartialRecoveryManager",
    "PartialRecoveryResult",
    "FieldRecovery",
    "FieldStatus",
    "numeric_recovery_strategy",
    "string_recovery_strategy",
    "list_recovery_strategy",
    "dict_recovery_strategy",
]
