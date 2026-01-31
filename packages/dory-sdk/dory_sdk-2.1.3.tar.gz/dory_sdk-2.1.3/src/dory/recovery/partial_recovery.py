"""
Partial State Recovery

Implements field-level state recovery to minimize data loss during recovery.
Instead of losing all state, recovers what can be recovered and fills in
defaults for corrupted or missing fields.

Features:
- Field-level validation
- Smart default values
- Partial recovery strategies
- Recovery statistics
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable, Set
from enum import Enum

logger = logging.getLogger(__name__)


class FieldStatus(Enum):
    """Status of a field after recovery attempt."""
    VALID = "valid"           # Field is valid, no recovery needed
    RECOVERED = "recovered"   # Field was recovered from snapshot
    DEFAULTED = "defaulted"   # Field was set to default value
    MISSING = "missing"       # Field is missing and has no default
    CORRUPTED = "corrupted"   # Field is corrupted and cannot be recovered


@dataclass
class FieldRecovery:
    """
    Represents recovery information for a single field.
    """
    field_name: str
    status: FieldStatus
    original_value: Optional[Any] = None
    recovered_value: Optional[Any] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field_name": self.field_name,
            "status": self.status.value,
            "original_value": str(self.original_value) if self.original_value is not None else None,
            "recovered_value": str(self.recovered_value) if self.recovered_value is not None else None,
            "error_message": self.error_message,
        }


@dataclass
class RecoveryResult:
    """
    Result of a partial recovery operation.
    """
    success: bool
    recovered_state: Dict[str, Any]
    field_recoveries: List[FieldRecovery] = field(default_factory=list)
    valid_count: int = 0
    recovered_count: int = 0
    defaulted_count: int = 0
    missing_count: int = 0
    corrupted_count: int = 0

    def get_recovery_rate(self) -> float:
        """
        Calculate recovery rate (percentage of fields recovered).

        Returns:
            Recovery rate from 0.0 to 1.0
        """
        total = len(self.field_recoveries)
        if total == 0:
            return 1.0

        recovered = self.valid_count + self.recovered_count + self.defaulted_count
        return recovered / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "recovered_state": self.recovered_state,
            "field_recoveries": [fr.to_dict() for fr in self.field_recoveries],
            "valid_count": self.valid_count,
            "recovered_count": self.recovered_count,
            "defaulted_count": self.defaulted_count,
            "missing_count": self.missing_count,
            "corrupted_count": self.corrupted_count,
            "recovery_rate": self.get_recovery_rate(),
        }


class PartialRecoveryManager:
    """
    Manages partial recovery of state data.

    Features:
    - Field-level validation and recovery
    - Default value provision
    - Custom recovery strategies
    - Recovery statistics

    Usage:
        manager = PartialRecoveryManager()

        # Define field defaults
        manager.set_field_default("counter", 0)
        manager.set_field_default("status", "initialized")

        # Add field validator
        manager.add_field_validator(
            "counter",
            lambda value: isinstance(value, int) and value >= 0
        )

        # Recover state
        result = await manager.recover_state(
            corrupted_state={"counter": "invalid", "status": "active"},
            snapshot_state={"counter": 42},
        )

        # Check result
        print(f"Recovery rate: {result.get_recovery_rate() * 100}%")
        print(f"Recovered state: {result.recovered_state}")
    """

    def __init__(
        self,
        strict_validation: bool = False,
        allow_partial: bool = True,
    ):
        """
        Initialize partial recovery manager.

        Args:
            strict_validation: Fail if any field cannot be recovered
            allow_partial: Allow partial recovery (True) or all-or-nothing (False)
        """
        self.strict_validation = strict_validation
        self.allow_partial = allow_partial

        # Field defaults
        self._field_defaults: Dict[str, Any] = {}

        # Field validators
        self._field_validators: Dict[str, Callable[[Any], bool]] = {}

        # Required fields
        self._required_fields: Set[str] = set()

        # Recovery strategies
        self._recovery_strategies: Dict[str, Callable] = {}

        # Statistics
        self._recovery_count = 0
        self._total_fields_recovered = 0

        logger.info(
            f"PartialRecoveryManager initialized: strict={strict_validation}, "
            f"allow_partial={allow_partial}"
        )

    def set_field_default(self, field_name: str, default_value: Any) -> None:
        """
        Set default value for a field.

        Args:
            field_name: Field name
            default_value: Default value to use if field is missing/corrupted
        """
        self._field_defaults[field_name] = default_value
        logger.debug(f"Field default set: {field_name} = {default_value}")

    def add_field_validator(
        self,
        field_name: str,
        validator: Callable[[Any], bool],
    ) -> None:
        """
        Add a validator for a field.

        Args:
            field_name: Field name
            validator: Function that returns True if value is valid
        """
        self._field_validators[field_name] = validator
        logger.debug(f"Field validator added: {field_name}")

    def set_required_field(self, field_name: str) -> None:
        """
        Mark a field as required.

        Args:
            field_name: Field name
        """
        self._required_fields.add(field_name)
        logger.debug(f"Required field set: {field_name}")

    def add_recovery_strategy(
        self,
        field_name: str,
        strategy: Callable[[Any, Optional[Any]], Any],
    ) -> None:
        """
        Add a custom recovery strategy for a field.

        Args:
            field_name: Field name
            strategy: Function(corrupted_value, snapshot_value) -> recovered_value
        """
        self._recovery_strategies[field_name] = strategy
        logger.debug(f"Recovery strategy added: {field_name}")

    async def recover_state(
        self,
        corrupted_state: Dict[str, Any],
        snapshot_state: Optional[Dict[str, Any]] = None,
        field_names: Optional[List[str]] = None,
    ) -> RecoveryResult:
        """
        Recover state data using partial recovery.

        Args:
            corrupted_state: State that needs recovery
            snapshot_state: Optional snapshot to recover from
            field_names: Optional list of field names to recover (all if None)

        Returns:
            RecoveryResult with recovered state and statistics
        """
        logger.info("Starting partial state recovery")

        snapshot_state = snapshot_state or {}
        recovered_state = {}
        field_recoveries = []

        # Determine fields to process
        if field_names is None:
            all_fields = set(corrupted_state.keys()) | set(snapshot_state.keys()) | set(self._field_defaults.keys())
        else:
            all_fields = set(field_names)

        # Process each field
        for field_name in all_fields:
            recovery = await self._recover_field(
                field_name=field_name,
                corrupted_value=corrupted_state.get(field_name),
                snapshot_value=snapshot_state.get(field_name),
            )

            field_recoveries.append(recovery)

            # Add to recovered state if successful
            if recovery.status in [FieldStatus.VALID, FieldStatus.RECOVERED, FieldStatus.DEFAULTED]:
                recovered_state[field_name] = recovery.recovered_value

        # Count by status
        valid_count = sum(1 for fr in field_recoveries if fr.status == FieldStatus.VALID)
        recovered_count = sum(1 for fr in field_recoveries if fr.status == FieldStatus.RECOVERED)
        defaulted_count = sum(1 for fr in field_recoveries if fr.status == FieldStatus.DEFAULTED)
        missing_count = sum(1 for fr in field_recoveries if fr.status == FieldStatus.MISSING)
        corrupted_count = sum(1 for fr in field_recoveries if fr.status == FieldStatus.CORRUPTED)

        # Determine success
        if self.strict_validation:
            success = missing_count == 0 and corrupted_count == 0
        else:
            success = not self.allow_partial or (
                # At least some fields recovered
                (valid_count + recovered_count + defaulted_count) > 0 and
                # All required fields present
                all(field in recovered_state for field in self._required_fields)
            )

        # Update statistics
        self._recovery_count += 1
        self._total_fields_recovered += valid_count + recovered_count + defaulted_count

        result = RecoveryResult(
            success=success,
            recovered_state=recovered_state,
            field_recoveries=field_recoveries,
            valid_count=valid_count,
            recovered_count=recovered_count,
            defaulted_count=defaulted_count,
            missing_count=missing_count,
            corrupted_count=corrupted_count,
        )

        logger.info(
            f"Partial recovery complete: {result.get_recovery_rate() * 100:.1f}% recovered "
            f"({valid_count} valid, {recovered_count} recovered, {defaulted_count} defaulted)"
        )

        return result

    async def _recover_field(
        self,
        field_name: str,
        corrupted_value: Optional[Any],
        snapshot_value: Optional[Any],
    ) -> FieldRecovery:
        """
        Recover a single field.

        Args:
            field_name: Field name
            corrupted_value: Current (possibly corrupted) value
            snapshot_value: Value from snapshot (if available)

        Returns:
            FieldRecovery result
        """
        # Try to validate corrupted value first
        if corrupted_value is not None and self._validate_field(field_name, corrupted_value):
            return FieldRecovery(
                field_name=field_name,
                status=FieldStatus.VALID,
                original_value=corrupted_value,
                recovered_value=corrupted_value,
            )

        # Try custom recovery strategy
        if field_name in self._recovery_strategies:
            try:
                strategy = self._recovery_strategies[field_name]
                recovered_value = strategy(corrupted_value, snapshot_value)
                if self._validate_field(field_name, recovered_value):
                    return FieldRecovery(
                        field_name=field_name,
                        status=FieldStatus.RECOVERED,
                        original_value=corrupted_value,
                        recovered_value=recovered_value,
                    )
            except Exception as e:
                logger.error(f"Recovery strategy failed for {field_name}: {e}")

        # Try to recover from snapshot
        if snapshot_value is not None and self._validate_field(field_name, snapshot_value):
            return FieldRecovery(
                field_name=field_name,
                status=FieldStatus.RECOVERED,
                original_value=corrupted_value,
                recovered_value=snapshot_value,
            )

        # Use default value
        if field_name in self._field_defaults:
            default_value = self._field_defaults[field_name]
            return FieldRecovery(
                field_name=field_name,
                status=FieldStatus.DEFAULTED,
                original_value=corrupted_value,
                recovered_value=default_value,
            )

        # Cannot recover
        if corrupted_value is None and snapshot_value is None:
            return FieldRecovery(
                field_name=field_name,
                status=FieldStatus.MISSING,
                original_value=corrupted_value,
                recovered_value=None,
                error_message="Field is missing and has no default",
            )
        else:
            return FieldRecovery(
                field_name=field_name,
                status=FieldStatus.CORRUPTED,
                original_value=corrupted_value,
                recovered_value=None,
                error_message="Field is corrupted and cannot be recovered",
            )

    def _validate_field(self, field_name: str, value: Any) -> bool:
        """
        Validate a field value.

        Args:
            field_name: Field name
            value: Value to validate

        Returns:
            True if valid
        """
        # Check if validator exists
        if field_name not in self._field_validators:
            # No validator, assume valid if not None
            return value is not None

        # Run validator
        try:
            validator = self._field_validators[field_name]
            return validator(value)
        except Exception as e:
            logger.error(f"Field validator failed for {field_name}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get recovery statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "recovery_count": self._recovery_count,
            "total_fields_recovered": self._total_fields_recovered,
            "field_defaults_count": len(self._field_defaults),
            "field_validators_count": len(self._field_validators),
            "required_fields_count": len(self._required_fields),
            "recovery_strategies_count": len(self._recovery_strategies),
        }


# Helper function for common recovery strategies

def numeric_recovery_strategy(corrupted_value: Any, snapshot_value: Optional[Any]) -> int:
    """
    Recovery strategy for numeric fields.

    Tries to convert corrupted value to int, falls back to snapshot or 0.
    """
    if snapshot_value is not None and isinstance(snapshot_value, (int, float)):
        return int(snapshot_value)

    try:
        return int(corrupted_value)
    except (TypeError, ValueError):
        return 0


def string_recovery_strategy(corrupted_value: Any, snapshot_value: Optional[Any]) -> str:
    """
    Recovery strategy for string fields.

    Tries to convert corrupted value to str, falls back to snapshot or empty string.
    """
    if snapshot_value is not None and isinstance(snapshot_value, str):
        return snapshot_value

    try:
        return str(corrupted_value) if corrupted_value is not None else ""
    except Exception:
        return ""


def list_recovery_strategy(corrupted_value: Any, snapshot_value: Optional[Any]) -> List:
    """
    Recovery strategy for list fields.

    Falls back to snapshot or empty list.
    """
    if isinstance(corrupted_value, list):
        return corrupted_value

    if snapshot_value is not None and isinstance(snapshot_value, list):
        return snapshot_value

    return []


def dict_recovery_strategy(corrupted_value: Any, snapshot_value: Optional[Any]) -> Dict:
    """
    Recovery strategy for dict fields.

    Falls back to snapshot or empty dict.
    """
    if isinstance(corrupted_value, dict):
        return corrupted_value

    if snapshot_value is not None and isinstance(snapshot_value, dict):
        return snapshot_value

    return {}
