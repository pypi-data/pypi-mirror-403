"""
Recovery decision maker.

Determines the appropriate recovery strategy based on
restart count, failure type, and migration status.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from dory.types import RecoveryStrategy, FaultType

logger = logging.getLogger(__name__)


class DecisionReason(Enum):
    """Reasons for recovery decisions."""
    FIRST_START = "first_start"
    MIGRATION = "migration"
    NORMAL_RESTART = "normal_restart"
    RAPID_RESTART = "rapid_restart"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    STATE_CORRUPTION = "state_corruption"
    CRASH_LOOP = "crash_loop"


@dataclass
class RecoveryDecision:
    """Result of recovery decision making."""
    strategy: RecoveryStrategy
    reason: DecisionReason
    should_restore_state: bool
    should_clear_caches: bool
    backoff_seconds: int = 0
    message: str = ""

    @property
    def name(self) -> str:
        """Get strategy name for logging."""
        return self.strategy.value


class RecoveryDecisionMaker:
    """
    Decides recovery strategy based on context.

    Strategies:
    1. RESTORE_STATE - Normal recovery, restore from checkpoint
    2. GOLDEN_IMAGE - Full reset, start fresh
    3. GOLDEN_WITH_BACKOFF - Reset with delay to prevent rapid cycling
    """

    def __init__(
        self,
        golden_image_threshold: int = 3,
        rapid_restart_window_sec: int = 60,
        max_backoff_sec: int = 300,
    ):
        """
        Initialize decision maker.

        Args:
            golden_image_threshold: Restart count triggering golden image
            rapid_restart_window_sec: Window for detecting rapid restarts
            max_backoff_sec: Maximum backoff delay
        """
        self._golden_threshold = golden_image_threshold
        self._rapid_window = rapid_restart_window_sec
        self._max_backoff = max_backoff_sec

    def decide(
        self,
        restart_count: int,
        is_migrating: bool = False,
        fault_type: FaultType | None = None,
        state_valid: bool = True,
        state_exists: bool = False,
    ) -> RecoveryDecision:
        """
        Decide recovery strategy.

        Args:
            restart_count: Current restart count
            is_migrating: Whether this is a migration restart
            fault_type: Type of fault that caused restart
            state_valid: Whether existing state is valid
            state_exists: Whether saved state exists (e.g., in ConfigMap)

        Returns:
            RecoveryDecision with strategy and details
        """
        # First start - but if state exists, it means this is a pod replacement
        # (orchestrator created a new pod after deleting the old one)
        if restart_count == 0:
            if state_exists:
                # State exists from previous pod - treat as migration/replacement
                return RecoveryDecision(
                    strategy=RecoveryStrategy.RESTORE_STATE,
                    reason=DecisionReason.MIGRATION,
                    should_restore_state=True,
                    should_clear_caches=False,
                    message="Pod replacement detected (state exists), restoring state",
                )
            # Truly first start with no prior state
            return RecoveryDecision(
                strategy=RecoveryStrategy.RESTORE_STATE,
                reason=DecisionReason.FIRST_START,
                should_restore_state=False,
                should_clear_caches=False,
                message="First start, no state to restore",
            )

        # Migration - always restore state
        if is_migrating:
            return RecoveryDecision(
                strategy=RecoveryStrategy.RESTORE_STATE,
                reason=DecisionReason.MIGRATION,
                should_restore_state=True,
                should_clear_caches=False,
                message="Migration restart, restoring state",
            )

        # State corruption - golden image reset
        if not state_valid or fault_type == FaultType.STATE_CORRUPTION:
            return RecoveryDecision(
                strategy=RecoveryStrategy.GOLDEN_IMAGE,
                reason=DecisionReason.STATE_CORRUPTION,
                should_restore_state=False,
                should_clear_caches=True,
                message="State corruption detected, performing golden image reset",
            )

        # Threshold exceeded - golden image with backoff
        if restart_count >= self._golden_threshold:
            backoff = self._calculate_backoff(restart_count)
            return RecoveryDecision(
                strategy=RecoveryStrategy.GOLDEN_WITH_BACKOFF,
                reason=DecisionReason.THRESHOLD_EXCEEDED,
                should_restore_state=False,
                should_clear_caches=True,
                backoff_seconds=backoff,
                message=f"Restart threshold exceeded ({restart_count} >= {self._golden_threshold}), "
                        f"golden image reset with {backoff}s backoff",
            )

        # Normal restart - try to restore state
        return RecoveryDecision(
            strategy=RecoveryStrategy.RESTORE_STATE,
            reason=DecisionReason.NORMAL_RESTART,
            should_restore_state=True,
            should_clear_caches=True,
            message=f"Normal restart (attempt {restart_count + 1}), restoring state",
        )

    def _calculate_backoff(self, restart_count: int) -> int:
        """
        Calculate backoff delay based on restart count.

        Uses exponential backoff with jitter.
        """
        base_backoff = 10  # seconds
        # Exponential: 10, 20, 40, 80, 160, ... capped at max
        backoff = min(
            base_backoff * (2 ** (restart_count - self._golden_threshold)),
            self._max_backoff,
        )
        return int(backoff)

    def should_trigger_alert(self, restart_count: int) -> bool:
        """
        Check if restart count should trigger alerting.

        Args:
            restart_count: Current restart count

        Returns:
            True if alert should be triggered
        """
        # Alert on first golden image reset and every N restarts after
        if restart_count == self._golden_threshold:
            return True
        if restart_count > self._golden_threshold and restart_count % 3 == 0:
            return True
        return False


class RecoveryExecutor:
    """
    Executes recovery decisions.

    Coordinates the actual recovery steps based on decision.
    """

    def __init__(self, state_manager, golden_image_manager):
        """
        Initialize recovery executor.

        Args:
            state_manager: State manager for state operations
            golden_image_manager: Golden image manager for resets
        """
        self._state_manager = state_manager
        self._golden_manager = golden_image_manager

    async def execute(
        self,
        decision: RecoveryDecision,
        processor_id: str,
    ) -> dict | None:
        """
        Execute recovery decision.

        Args:
            decision: Recovery decision to execute
            processor_id: Processor ID

        Returns:
            Restored state dict, or None if golden image reset
        """
        logger.info(f"Executing recovery: {decision.strategy.value} - {decision.message}")

        # Apply backoff if needed
        if decision.backoff_seconds > 0:
            logger.info(f"Applying backoff: {decision.backoff_seconds}s")
            import asyncio
            await asyncio.sleep(decision.backoff_seconds)

        # Golden image reset
        if decision.strategy in (
            RecoveryStrategy.GOLDEN_IMAGE,
            RecoveryStrategy.GOLDEN_WITH_BACKOFF,
        ):
            await self._golden_manager.reset(processor_id)
            return None

        # Restore state
        if decision.should_restore_state:
            state = await self._state_manager.load_state(processor_id)
            return state

        return None
