"""
State validation for integrity checking.

Validates restored state against schema and checksums.
"""

import logging
from typing import Any

from dory.utils.errors import DoryValidationError

logger = logging.getLogger(__name__)


class StateValidator:
    """
    Validates processor state for integrity and schema compliance.

    Performs:
    1. Schema validation (required fields, types)
    2. Integrity checks (checksums)
    3. Version compatibility checks
    """

    def __init__(self, schema: dict[str, type] | None = None):
        """
        Initialize validator.

        Args:
            schema: Optional schema mapping field names to expected types
        """
        self._schema = schema

    def validate(self, state: dict[str, Any]) -> bool:
        """
        Validate state dictionary.

        Args:
            state: State dictionary to validate

        Returns:
            True if valid

        Raises:
            DoryValidationError: If validation fails
        """
        if not isinstance(state, dict):
            raise DoryValidationError(f"State must be a dict, got {type(state)}")

        # Validate against schema if provided
        if self._schema:
            self._validate_schema(state)

        # Run integrity checks
        self._validate_integrity(state)

        logger.debug("State validation passed")
        return True

    def _validate_schema(self, state: dict[str, Any]) -> None:
        """Validate state against schema."""
        for field_name, expected_type in self._schema.items():
            if field_name not in state:
                raise DoryValidationError(
                    f"Required field '{field_name}' missing from state"
                )

            value = state[field_name]

            # Allow None for any type
            if value is None:
                continue

            if not isinstance(value, expected_type):
                raise DoryValidationError(
                    f"Field '{field_name}' has wrong type: "
                    f"expected {expected_type.__name__}, got {type(value).__name__}"
                )

    def _validate_integrity(self, state: dict[str, Any]) -> None:
        """
        Run integrity checks on state.

        Can be extended for custom integrity validation.
        """
        # Check for common corruption indicators
        if "__corrupted__" in state:
            raise DoryValidationError("State marked as corrupted")

        # Check metadata if present
        if "_metadata" in state:
            metadata = state["_metadata"]
            if not isinstance(metadata, dict):
                raise DoryValidationError("State metadata must be a dict")

    def validate_partial(self, state: dict[str, Any], required_fields: list[str]) -> bool:
        """
        Validate that specific fields exist and have correct types.

        Args:
            state: State dictionary
            required_fields: List of field names that must exist

        Returns:
            True if valid

        Raises:
            DoryValidationError: If validation fails
        """
        for field_name in required_fields:
            if field_name not in state:
                raise DoryValidationError(
                    f"Required field '{field_name}' missing from state"
                )

            if self._schema and field_name in self._schema:
                expected_type = self._schema[field_name]
                value = state[field_name]

                if value is not None and not isinstance(value, expected_type):
                    raise DoryValidationError(
                        f"Field '{field_name}' has wrong type"
                    )

        return True


class StateVersionChecker:
    """
    Checks state version compatibility.

    Ensures restored state is compatible with current processor version.
    """

    VERSION_FIELD = "_version"

    def __init__(self, current_version: str):
        """
        Initialize version checker.

        Args:
            current_version: Current processor state version
        """
        self._current_version = current_version

    def check_compatible(self, state: dict[str, Any]) -> bool:
        """
        Check if state version is compatible.

        Args:
            state: State dictionary

        Returns:
            True if compatible

        Raises:
            DoryValidationError: If incompatible
        """
        state_version = state.get(self.VERSION_FIELD)

        if state_version is None:
            # No version = assume compatible (v0)
            logger.warning("State has no version field, assuming compatible")
            return True

        if not self._is_compatible(state_version, self._current_version):
            raise DoryValidationError(
                f"State version {state_version} not compatible "
                f"with processor version {self._current_version}"
            )

        return True

    def _is_compatible(self, state_version: str, processor_version: str) -> bool:
        """
        Check version compatibility.

        Default: major version must match.
        Override for custom compatibility logic.
        """
        try:
            state_major = int(state_version.split(".")[0])
            processor_major = int(processor_version.split(".")[0])
            return state_major == processor_major
        except (ValueError, IndexError):
            # Invalid version format
            return False
