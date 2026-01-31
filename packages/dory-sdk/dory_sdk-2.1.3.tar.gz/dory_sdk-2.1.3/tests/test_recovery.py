"""Tests for recovery and fault handling."""

import pytest

from dory.recovery.restart_detector import RestartDetector, RestartInfo
from dory.recovery.state_validator import StateValidator, StateVersionChecker
from dory.recovery.recovery_decision import (
    RecoveryDecisionMaker,
    RecoveryDecision,
    DecisionReason,
)
from dory.types import RecoveryStrategy, FaultType
from dory.utils.errors import DoryValidationError


class TestRestartDetector:
    """Tests for RestartDetector."""

    @pytest.mark.asyncio
    async def test_first_start(self, tmp_path):
        """Test detection on first start."""
        marker_path = tmp_path / "marker"
        detector = RestartDetector(marker_path=str(marker_path))

        info = await detector.detect()

        assert info.restart_count == 0
        assert info.is_restart is False
        assert info.is_first_start is True

    @pytest.mark.asyncio
    async def test_restart_detection(self, tmp_path):
        """Test restart detection with existing marker."""
        marker_path = tmp_path / "marker"
        marker_path.write_text("2")

        detector = RestartDetector(marker_path=str(marker_path))
        info = await detector.detect()

        assert info.restart_count == 2
        assert info.is_restart is True

    @pytest.mark.asyncio
    async def test_env_var_detection(self, tmp_path, monkeypatch):
        """Test restart count from environment variable."""
        monkeypatch.setenv("RESTART_COUNT", "5")

        detector = RestartDetector(marker_path=str(tmp_path / "marker"))
        info = await detector.detect()

        assert info.restart_count == 5

    def test_reset(self, tmp_path):
        """Test resetting the restart marker."""
        marker_path = tmp_path / "marker"
        marker_path.write_text("3")

        detector = RestartDetector(marker_path=str(marker_path))
        detector.reset()

        assert not marker_path.exists()


class TestStateValidator:
    """Tests for StateValidator."""

    def test_validate_valid_state(self):
        """Test validation of valid state."""
        schema = {"counter": int, "name": str}
        validator = StateValidator(schema=schema)

        state = {"counter": 42, "name": "test"}
        assert validator.validate(state) is True

    def test_validate_missing_field(self):
        """Test validation fails for missing field."""
        schema = {"counter": int, "name": str}
        validator = StateValidator(schema=schema)

        state = {"counter": 42}  # Missing 'name'

        with pytest.raises(DoryValidationError) as exc_info:
            validator.validate(state)

        assert "missing" in str(exc_info.value).lower()

    def test_validate_wrong_type(self):
        """Test validation fails for wrong type."""
        schema = {"counter": int}
        validator = StateValidator(schema=schema)

        state = {"counter": "not an int"}

        with pytest.raises(DoryValidationError) as exc_info:
            validator.validate(state)

        assert "wrong type" in str(exc_info.value).lower()

    def test_validate_allows_none(self):
        """Test validation allows None values."""
        schema = {"counter": int}
        validator = StateValidator(schema=schema)

        state = {"counter": None}
        assert validator.validate(state) is True

    def test_validate_no_schema(self):
        """Test validation passes without schema."""
        validator = StateValidator()
        state = {"anything": "goes"}
        assert validator.validate(state) is True


class TestStateVersionChecker:
    """Tests for StateVersionChecker."""

    def test_compatible_version(self):
        """Test compatible version check."""
        checker = StateVersionChecker("1.2.3")
        state = {"_version": "1.0.0", "data": "value"}

        assert checker.check_compatible(state) is True

    def test_incompatible_version(self):
        """Test incompatible version raises error."""
        checker = StateVersionChecker("2.0.0")
        state = {"_version": "1.0.0", "data": "value"}

        with pytest.raises(DoryValidationError):
            checker.check_compatible(state)

    def test_no_version_field(self):
        """Test state without version field is compatible."""
        checker = StateVersionChecker("1.0.0")
        state = {"data": "value"}  # No _version field

        assert checker.check_compatible(state) is True


class TestRecoveryDecisionMaker:
    """Tests for RecoveryDecisionMaker."""

    def test_first_start(self):
        """Test decision for first start."""
        maker = RecoveryDecisionMaker()
        decision = maker.decide(restart_count=0)

        assert decision.strategy == RecoveryStrategy.RESTORE_STATE
        assert decision.reason == DecisionReason.FIRST_START
        assert decision.should_restore_state is False

    def test_first_start_with_existing_state(self):
        """Test decision for pod replacement (restart_count=0 but state exists).

        This scenario happens when:
        1. Old pod is deleted (PreStop saves state to ConfigMap)
        2. Orchestrator creates a new pod with restart_count=0
        3. ConfigMap state exists from previous pod

        The SDK should detect this as a pod replacement and restore state.
        """
        maker = RecoveryDecisionMaker()
        decision = maker.decide(restart_count=0, state_exists=True)

        assert decision.strategy == RecoveryStrategy.RESTORE_STATE
        assert decision.reason == DecisionReason.MIGRATION
        assert decision.should_restore_state is True
        assert "replacement" in decision.message.lower()

    def test_migration_restart(self):
        """Test decision for migration restart."""
        maker = RecoveryDecisionMaker()
        decision = maker.decide(restart_count=1, is_migrating=True)

        assert decision.strategy == RecoveryStrategy.RESTORE_STATE
        assert decision.reason == DecisionReason.MIGRATION
        assert decision.should_restore_state is True

    def test_normal_restart(self):
        """Test decision for normal restart."""
        maker = RecoveryDecisionMaker()
        decision = maker.decide(restart_count=1)

        assert decision.strategy == RecoveryStrategy.RESTORE_STATE
        assert decision.reason == DecisionReason.NORMAL_RESTART
        assert decision.should_restore_state is True
        assert decision.should_clear_caches is True

    def test_threshold_exceeded(self):
        """Test decision when threshold exceeded."""
        maker = RecoveryDecisionMaker(golden_image_threshold=3)
        decision = maker.decide(restart_count=3)

        assert decision.strategy == RecoveryStrategy.GOLDEN_WITH_BACKOFF
        assert decision.reason == DecisionReason.THRESHOLD_EXCEEDED
        assert decision.should_restore_state is False
        assert decision.backoff_seconds > 0

    def test_state_corruption(self):
        """Test decision for state corruption."""
        maker = RecoveryDecisionMaker()
        decision = maker.decide(
            restart_count=1,
            fault_type=FaultType.STATE_CORRUPTION,
        )

        assert decision.strategy == RecoveryStrategy.GOLDEN_IMAGE
        assert decision.reason == DecisionReason.STATE_CORRUPTION

    def test_backoff_calculation(self):
        """Test exponential backoff calculation."""
        maker = RecoveryDecisionMaker(golden_image_threshold=3, max_backoff_sec=100)

        # At threshold
        decision = maker.decide(restart_count=3)
        backoff1 = decision.backoff_seconds

        # Above threshold
        decision = maker.decide(restart_count=4)
        backoff2 = decision.backoff_seconds

        assert backoff2 > backoff1  # Exponential increase

    def test_alert_trigger(self):
        """Test alert triggering."""
        maker = RecoveryDecisionMaker(golden_image_threshold=3)

        assert maker.should_trigger_alert(2) is False
        assert maker.should_trigger_alert(3) is True
        assert maker.should_trigger_alert(6) is True  # Every 3 after threshold
