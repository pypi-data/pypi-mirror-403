"""
Golden Snapshot Validator

Validates snapshots and state before/after capture and restoration.
Implements:
- Schema validation
- Dependency checks
- State integrity verification
- Reset validation
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity level of validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found during validation.
    """
    field: str
    severity: ValidationSeverity
    message: str
    code: str
    value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "severity": self.severity.value,
            "message": self.message,
            "code": self.code,
            "value": str(self.value) if self.value is not None else None,
        }


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    """
    passed: bool
    issues: List[ValidationIssue]
    warnings_count: int = 0
    errors_count: int = 0
    critical_count: int = 0

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return self.errors_count > 0 or self.critical_count > 0

    def has_critical(self) -> bool:
        """Check if there are critical issues."""
        return self.critical_count > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "critical_count": self.critical_count,
        }


class GoldenValidator:
    """
    Validates golden snapshots and state data.

    Features:
    - Schema validation (required fields, types)
    - Dependency checking (required dependencies present)
    - State integrity (checksums, consistency)
    - Reset verification (pre/post reset validation)
    - Custom validators

    Usage:
        validator = GoldenValidator()

        # Define schema
        validator.define_schema({
            "required_fields": ["processor_id", "state_version"],
            "field_types": {
                "processor_id": str,
                "counter": int,
            }
        })

        # Validate state
        result = await validator.validate_state(state_data)
        if not result.passed:
            print(f"Validation failed: {result.errors_count} errors")
    """

    def __init__(
        self,
        strict_mode: bool = False,
        allow_unknown_fields: bool = True,
    ):
        """
        Initialize validator.

        Args:
            strict_mode: Fail on warnings
            allow_unknown_fields: Allow fields not in schema
        """
        self.strict_mode = strict_mode
        self.allow_unknown_fields = allow_unknown_fields

        # Schema definition
        self._required_fields: Set[str] = set()
        self._field_types: Dict[str, type] = {}
        self._field_validators: Dict[str, List[Callable]] = {}
        self._dependencies: Dict[str, List[str]] = {}

        # Custom validators
        self._custom_validators: List[Callable] = []

        logger.info(
            f"GoldenValidator initialized: strict_mode={strict_mode}, "
            f"allow_unknown_fields={allow_unknown_fields}"
        )

    def define_schema(
        self,
        schema: Dict[str, Any],
    ) -> None:
        """
        Define validation schema.

        Args:
            schema: Schema definition containing:
                - required_fields: List of required field names
                - field_types: Dict of field_name -> type
                - dependencies: Dict of field_name -> list of dependent fields

        Example:
            validator.define_schema({
                "required_fields": ["processor_id", "state_version"],
                "field_types": {
                    "processor_id": str,
                    "counter": int,
                    "data": dict,
                },
                "dependencies": {
                    "session_id": ["session_state"],  # If session_id present, session_state required
                }
            })
        """
        self._required_fields = set(schema.get("required_fields", []))
        self._field_types = schema.get("field_types", {})
        self._dependencies = schema.get("dependencies", {})

        logger.info(
            f"Schema defined: {len(self._required_fields)} required fields, "
            f"{len(self._field_types)} typed fields, "
            f"{len(self._dependencies)} dependencies"
        )

    def add_field_validator(
        self,
        field: str,
        validator: Callable[[Any], bool],
    ) -> None:
        """
        Add a custom validator for a specific field.

        Args:
            field: Field name
            validator: Function that returns True if valid

        Example:
            validator.add_field_validator(
                "counter",
                lambda value: value >= 0
            )
        """
        if field not in self._field_validators:
            self._field_validators[field] = []
        self._field_validators[field].append(validator)

    def add_custom_validator(
        self,
        validator: Callable[[Dict[str, Any]], bool],
    ) -> None:
        """
        Add a custom validator for the entire state.

        Args:
            validator: Function that receives state dict and returns True if valid

        Example:
            validator.add_custom_validator(
                lambda state: state.get("counter", 0) < state.get("max_value", 100)
            )
        """
        self._custom_validators.append(validator)

    async def validate_state(
        self,
        state_data: Dict[str, Any],
        context: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate state data against schema.

        Args:
            state_data: State data to validate
            context: Context for validation (e.g., "pre_capture", "post_restore")

        Returns:
            ValidationResult with issues found
        """
        issues: List[ValidationIssue] = []

        # Check required fields
        for field in self._required_fields:
            if field not in state_data:
                issues.append(ValidationIssue(
                    field=field,
                    severity=ValidationSeverity.ERROR,
                    message=f"Required field '{field}' is missing",
                    code="MISSING_REQUIRED_FIELD",
                ))

        # Check field types
        for field, expected_type in self._field_types.items():
            if field in state_data:
                value = state_data[field]
                if not isinstance(value, expected_type):
                    issues.append(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Field '{field}' has wrong type: expected {expected_type.__name__}, got {type(value).__name__}",
                        code="WRONG_TYPE",
                        value=value,
                    ))

        # Check dependencies
        for field, deps in self._dependencies.items():
            if field in state_data:
                for dep in deps:
                    if dep not in state_data:
                        issues.append(ValidationIssue(
                            field=dep,
                            severity=ValidationSeverity.WARNING,
                            message=f"Field '{field}' requires '{dep}' but it's missing",
                            code="MISSING_DEPENDENCY",
                        ))

        # Check unknown fields
        if not self.allow_unknown_fields:
            known_fields = set(self._required_fields) | set(self._field_types.keys())
            for field in state_data.keys():
                if field not in known_fields:
                    issues.append(ValidationIssue(
                        field=field,
                        severity=ValidationSeverity.WARNING,
                        message=f"Unknown field '{field}' found",
                        code="UNKNOWN_FIELD",
                    ))

        # Run field validators
        for field, validators in self._field_validators.items():
            if field in state_data:
                value = state_data[field]
                for validator_fn in validators:
                    try:
                        if not validator_fn(value):
                            issues.append(ValidationIssue(
                                field=field,
                                severity=ValidationSeverity.ERROR,
                                message=f"Field '{field}' failed custom validation",
                                code="CUSTOM_VALIDATION_FAILED",
                                value=value,
                            ))
                    except Exception as e:
                        issues.append(ValidationIssue(
                            field=field,
                            severity=ValidationSeverity.ERROR,
                            message=f"Field '{field}' validation raised exception: {e}",
                            code="VALIDATION_EXCEPTION",
                            value=value,
                        ))

        # Run custom validators
        for validator_fn in self._custom_validators:
            try:
                if not validator_fn(state_data):
                    issues.append(ValidationIssue(
                        field="__global__",
                        severity=ValidationSeverity.ERROR,
                        message="State failed custom validation",
                        code="CUSTOM_STATE_VALIDATION_FAILED",
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    field="__global__",
                    severity=ValidationSeverity.ERROR,
                    message=f"Custom validation raised exception: {e}",
                    code="VALIDATION_EXCEPTION",
                ))

        # Count issues by severity
        warnings_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        errors_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        critical_count = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)

        # Determine pass/fail
        if self.strict_mode:
            passed = len(issues) == 0
        else:
            passed = errors_count == 0 and critical_count == 0

        result = ValidationResult(
            passed=passed,
            issues=issues,
            warnings_count=warnings_count,
            errors_count=errors_count,
            critical_count=critical_count,
        )

        # Log result
        if not passed:
            logger.warning(
                f"Validation failed: {errors_count} errors, {critical_count} critical, "
                f"{warnings_count} warnings"
            )
            for issue in issues:
                if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    logger.error(f"  [{issue.severity.value}] {issue.field}: {issue.message}")
        else:
            logger.info(f"Validation passed ({warnings_count} warnings)")

        return result

    async def validate_pre_capture(
        self,
        state_data: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate state before capturing snapshot.

        Args:
            state_data: State data to capture

        Returns:
            ValidationResult
        """
        logger.info("Running pre-capture validation")
        return await self.validate_state(state_data, context="pre_capture")

    async def validate_post_capture(
        self,
        original_state: Dict[str, Any],
        restored_state: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate state after capturing and restoring snapshot (round-trip test).

        Args:
            original_state: Original state before capture
            restored_state: State restored from snapshot

        Returns:
            ValidationResult
        """
        logger.info("Running post-capture validation (round-trip)")
        issues: List[ValidationIssue] = []

        # Check if all keys are preserved
        original_keys = set(original_state.keys())
        restored_keys = set(restored_state.keys())

        missing_keys = original_keys - restored_keys
        extra_keys = restored_keys - original_keys

        for key in missing_keys:
            issues.append(ValidationIssue(
                field=key,
                severity=ValidationSeverity.ERROR,
                message=f"Key '{key}' was lost during snapshot round-trip",
                code="MISSING_KEY",
            ))

        for key in extra_keys:
            issues.append(ValidationIssue(
                field=key,
                severity=ValidationSeverity.WARNING,
                message=f"Extra key '{key}' appeared during snapshot round-trip",
                code="EXTRA_KEY",
            ))

        # Check if values match
        for key in original_keys & restored_keys:
            if original_state[key] != restored_state[key]:
                issues.append(ValidationIssue(
                    field=key,
                    severity=ValidationSeverity.ERROR,
                    message=f"Value for '{key}' changed during snapshot round-trip",
                    code="VALUE_MISMATCH",
                    value=f"{original_state[key]} -> {restored_state[key]}",
                ))

        # Count issues
        warnings_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        errors_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        critical_count = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)

        passed = errors_count == 0 and critical_count == 0

        return ValidationResult(
            passed=passed,
            issues=issues,
            warnings_count=warnings_count,
            errors_count=errors_count,
            critical_count=critical_count,
        )

    async def validate_pre_reset(
        self,
        processor_id: str,
        reset_level: str,
    ) -> ValidationResult:
        """
        Validate before performing reset.

        Args:
            processor_id: Processor ID to reset
            reset_level: Reset level (SOFT, MODERATE, FULL, FACTORY)

        Returns:
            ValidationResult
        """
        logger.info(f"Running pre-reset validation: processor={processor_id}, level={reset_level}")
        issues: List[ValidationIssue] = []

        # Basic validation
        if not processor_id:
            issues.append(ValidationIssue(
                field="processor_id",
                severity=ValidationSeverity.CRITICAL,
                message="Processor ID is empty",
                code="EMPTY_PROCESSOR_ID",
            ))

        valid_levels = ["SOFT", "MODERATE", "FULL", "FACTORY"]
        if reset_level not in valid_levels:
            issues.append(ValidationIssue(
                field="reset_level",
                severity=ValidationSeverity.ERROR,
                message=f"Invalid reset level: {reset_level}",
                code="INVALID_RESET_LEVEL",
                value=reset_level,
            ))

        passed = len([i for i in issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]) == 0

        return ValidationResult(
            passed=passed,
            issues=issues,
            warnings_count=sum(1 for i in issues if i.severity == ValidationSeverity.WARNING),
            errors_count=sum(1 for i in issues if i.severity == ValidationSeverity.ERROR),
            critical_count=sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL),
        )

    async def validate_post_reset(
        self,
        processor_id: str,
        reset_level: str,
        reset_successful: bool,
    ) -> ValidationResult:
        """
        Validate after performing reset.

        Args:
            processor_id: Processor ID that was reset
            reset_level: Reset level used
            reset_successful: Whether reset was successful

        Returns:
            ValidationResult
        """
        logger.info(f"Running post-reset validation: processor={processor_id}, success={reset_successful}")
        issues: List[ValidationIssue] = []

        if not reset_successful:
            issues.append(ValidationIssue(
                field="reset_result",
                severity=ValidationSeverity.CRITICAL,
                message="Reset operation failed",
                code="RESET_FAILED",
            ))

        passed = reset_successful

        return ValidationResult(
            passed=passed,
            issues=issues,
            warnings_count=0,
            errors_count=0 if reset_successful else 0,
            critical_count=0 if reset_successful else 1,
        )
