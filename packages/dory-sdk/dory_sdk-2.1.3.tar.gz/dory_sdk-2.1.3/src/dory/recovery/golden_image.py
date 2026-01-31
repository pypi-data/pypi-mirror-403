"""
Golden image reset manager.

Handles state cleanup for fresh-start recovery after
repeated failures.

Implements graduated reset levels:
- SOFT: Clear caches only
- MODERATE: Clear session state, keep persistent data
- FULL: Delete all state
- FACTORY: Full reset + clear all metadata
"""

import logging
import time
from enum import Enum
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from dory.utils.errors import DoryStateError

if TYPE_CHECKING:
    from dory.migration.state_manager import StateManager

logger = logging.getLogger(__name__)


class ResetLevel(Enum):
    """
    Graduated reset levels from least to most destructive.
    """
    SOFT = "soft"           # Clear caches only, preserve all state
    MODERATE = "moderate"   # Clear session state, keep persistent data
    FULL = "full"          # Delete all persisted state
    FACTORY = "factory"    # Full reset + clear metadata, restart counts


@dataclass
class ResetResult:
    """
    Result of a reset operation.
    """
    success: bool
    level: ResetLevel
    processor_id: str
    items_cleared: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class GoldenImageManager:
    """
    Manages golden image reset operations with graduated reset levels.

    Reset Levels (in order of severity):
    1. SOFT: Clear caches only, preserve all state
    2. MODERATE: Clear session state, keep persistent data
    3. FULL: Delete all persisted state
    4. FACTORY: Full reset + clear metadata

    Golden image reset = delete all persisted state and restart fresh.
    Used when:
    1. State corruption is detected
    2. Restart count exceeds threshold
    3. Manual reset requested
    """

    def __init__(
        self,
        state_manager: "StateManager",
        reset_threshold: int = 3,
        soft_threshold: int = 1,
        moderate_threshold: int = 2,
        cache_manager: Optional["CacheResetManager"] = None,
        on_reset: Optional[Callable] = None,
        metrics_collector: Optional[Any] = None,
    ):
        """
        Initialize golden image manager.

        Args:
            state_manager: State manager for state deletion
            reset_threshold: Restart count that triggers FULL reset
            soft_threshold: Restart count that triggers SOFT reset
            moderate_threshold: Restart count that triggers MODERATE reset
            cache_manager: Optional cache manager for SOFT resets
            on_reset: Optional callback when reset occurs
            metrics_collector: Optional metrics collector for counter resets
        """
        self._state_manager = state_manager
        self._reset_threshold = reset_threshold
        self._soft_threshold = soft_threshold
        self._moderate_threshold = moderate_threshold
        self._cache_manager = cache_manager or CacheResetManager()
        self._on_reset = on_reset
        self._metrics_collector = metrics_collector

        # Recovery tracking
        self._restart_count = 0
        self._last_reset_time: Optional[float] = None
        self._session_data: Dict[str, Any] = {}
        self._active_connections: List[Any] = []

        # Metrics
        self._reset_counts = {
            ResetLevel.SOFT: 0,
            ResetLevel.MODERATE: 0,
            ResetLevel.FULL: 0,
            ResetLevel.FACTORY: 0,
        }

    def should_reset(self, restart_count: int) -> bool:
        """
        Check if golden image reset should be triggered.

        Args:
            restart_count: Current restart count

        Returns:
            True if reset should be triggered
        """
        if restart_count >= self._soft_threshold:
            logger.warning(
                f"Restart count {restart_count} >= threshold {self._soft_threshold}, "
                "recommending reset"
            )
            return True
        return False

    def determine_reset_level(
        self,
        restart_count: int,
        state_corrupted: bool = False,
        manual_factory: bool = False,
    ) -> ResetLevel:
        """
        Determine appropriate reset level based on conditions.

        Args:
            restart_count: Current restart count
            state_corrupted: Whether state corruption is detected
            manual_factory: Whether factory reset is manually requested

        Returns:
            Recommended reset level

        Logic:
        - Factory reset if manually requested
        - Full reset if state corrupted
        - Graduated by restart count: SOFT -> MODERATE -> FULL
        """
        # Manual factory reset
        if manual_factory:
            logger.info("Factory reset manually requested")
            return ResetLevel.FACTORY

        # State corruption detected -> FULL reset
        if state_corrupted:
            logger.warning("State corruption detected, recommending FULL reset")
            return ResetLevel.FULL

        # Graduated by restart count
        if restart_count >= self._reset_threshold:
            return ResetLevel.FULL
        elif restart_count >= self._moderate_threshold:
            return ResetLevel.MODERATE
        elif restart_count >= self._soft_threshold:
            return ResetLevel.SOFT
        else:
            # No reset needed
            return ResetLevel.SOFT  # Default to softest

    async def reset(
        self,
        processor_id: str,
        level: Optional[ResetLevel] = None,
        restart_count: int = 0,
    ) -> ResetResult:
        """
        Perform golden image reset with specified or auto-determined level.

        Args:
            processor_id: Processor ID to reset
            level: Reset level (auto-determined if None)
            restart_count: Current restart count (for auto-determination)

        Returns:
            ResetResult with success status and details
        """
        # Determine level if not specified
        if level is None:
            level = self.determine_reset_level(restart_count)

        logger.warning(
            f"Performing {level.value.upper()} reset for processor {processor_id}"
        )

        # Perform reset based on level
        if level == ResetLevel.SOFT:
            result = await self._soft_reset(processor_id)
        elif level == ResetLevel.MODERATE:
            result = await self._moderate_reset(processor_id)
        elif level == ResetLevel.FULL:
            result = await self._full_reset(processor_id)
        elif level == ResetLevel.FACTORY:
            result = await self._factory_reset(processor_id)
        else:
            logger.error(f"Unknown reset level: {level}")
            return ResetResult(
                success=False,
                level=level,
                processor_id=processor_id,
                errors=[f"Unknown reset level: {level}"],
            )

        # Update metrics
        if result.success:
            self._reset_counts[level] += 1

        # Call reset callback
        if self._on_reset and result.success:
            try:
                if asyncio.iscoroutinefunction(self._on_reset):
                    await self._on_reset(result)
                else:
                    self._on_reset(result)
            except Exception as e:
                logger.warning(f"Reset callback failed: {e}")

        return result

    async def _soft_reset(self, processor_id: str) -> ResetResult:
        """
        SOFT reset: Clear caches only, preserve all state.

        Args:
            processor_id: Processor ID

        Returns:
            ResetResult
        """
        logger.info(f"Performing SOFT reset for {processor_id} (cache clear only)")

        try:
            cleared_count = await self._cache_manager.clear_all_caches()

            return ResetResult(
                success=True,
                level=ResetLevel.SOFT,
                processor_id=processor_id,
                items_cleared=cleared_count,
            )

        except Exception as e:
            logger.error(f"SOFT reset failed: {e}")
            return ResetResult(
                success=False,
                level=ResetLevel.SOFT,
                processor_id=processor_id,
                errors=[str(e)],
            )

    async def _clear_session_state(self) -> int:
        """
        Clear session-level state for recovery.

        Clears:
        - In-memory session data
        - Active connection references
        - Temporary state not yet persisted

        Returns:
            Number of items cleared
        """
        items_cleared = 0

        # Clear session data
        if self._session_data:
            session_count = len(self._session_data)
            self._session_data.clear()
            items_cleared += session_count
            logger.debug(f"Cleared {session_count} session data entries")

        # Clear active connection references
        if self._active_connections:
            conn_count = len(self._active_connections)
            self._active_connections.clear()
            items_cleared += conn_count
            logger.debug(f"Cleared {conn_count} active connection references")

        logger.info(f"Session-level state cleared: {items_cleared} items")
        return items_cleared

    async def _moderate_reset(self, processor_id: str) -> ResetResult:
        """
        MODERATE reset: Clear session state, keep persistent data.

        Args:
            processor_id: Processor ID

        Returns:
            ResetResult
        """
        logger.info(f"Performing MODERATE reset for {processor_id}")

        errors = []
        items_cleared = 0

        try:
            # Clear caches
            cleared_count = await self._cache_manager.clear_all_caches()
            items_cleared += cleared_count

            # Clear session-level state
            session_cleared = await self._clear_session_state()
            items_cleared += session_cleared

            return ResetResult(
                success=True,
                level=ResetLevel.MODERATE,
                processor_id=processor_id,
                items_cleared=items_cleared,
            )

        except Exception as e:
            logger.error(f"MODERATE reset failed: {e}")
            errors.append(str(e))
            return ResetResult(
                success=False,
                level=ResetLevel.MODERATE,
                processor_id=processor_id,
                items_cleared=items_cleared,
                errors=errors,
            )

    async def _full_reset(self, processor_id: str) -> ResetResult:
        """
        FULL reset: Delete all persisted state.

        Args:
            processor_id: Processor ID

        Returns:
            ResetResult
        """
        logger.info(f"Performing FULL reset for {processor_id}")

        try:
            # Clear caches first
            await self._cache_manager.clear_all_caches()

            # Delete all state
            deleted = await self._state_manager.delete_state(processor_id)

            if deleted:
                logger.info(f"FULL reset complete for {processor_id}")
            else:
                logger.info(f"No state to delete for {processor_id}")

            return ResetResult(
                success=True,
                level=ResetLevel.FULL,
                processor_id=processor_id,
                items_cleared=1 if deleted else 0,
            )

        except DoryStateError as e:
            logger.error(f"FULL reset failed: {e}")
            return ResetResult(
                success=False,
                level=ResetLevel.FULL,
                processor_id=processor_id,
                errors=[str(e)],
            )

    def _reset_recovery_tracking(self) -> int:
        """
        Reset all recovery-related tracking to clean state.

        Clears:
        - Restart count
        - Last reset time
        - Reset level counts
        - Metrics counters (if available)

        Returns:
            Number of items reset
        """
        items_reset = 0

        # Reset restart count
        if self._restart_count > 0:
            self._restart_count = 0
            items_reset += 1
            logger.debug("Reset restart count to 0")

        # Reset last reset time
        self._last_reset_time = time.time()
        items_reset += 1

        # Reset level counts
        for level in self._reset_counts:
            if self._reset_counts[level] > 0:
                self._reset_counts[level] = 0
                items_reset += 1

        # Reset metrics counters if collector is available
        if self._metrics_collector:
            try:
                if hasattr(self._metrics_collector, 'reset_counters'):
                    self._metrics_collector.reset_counters()
                    items_reset += 1
                    logger.debug("Reset metrics counters")
            except Exception as e:
                logger.warning(f"Failed to reset metrics counters: {e}")

        logger.info(f"Recovery tracking reset to clean state: {items_reset} items")
        return items_reset

    async def _factory_reset(self, processor_id: str) -> ResetResult:
        """
        FACTORY reset: Full reset + clear all metadata and counters.

        Args:
            processor_id: Processor ID

        Returns:
            ResetResult
        """
        logger.warning(f"Performing FACTORY reset for {processor_id}")

        errors = []
        items_cleared = 0

        try:
            # Clear caches
            cache_cleared = await self._cache_manager.clear_all_caches()
            items_cleared += cache_cleared

            # Clear session state
            session_cleared = await self._clear_session_state()
            items_cleared += session_cleared

            # Delete all state
            deleted = await self._state_manager.delete_state(processor_id)
            if deleted:
                items_cleared += 1

            # Clear restart counts, metrics, and recovery tracking
            tracking_reset = self._reset_recovery_tracking()
            items_cleared += tracking_reset

            logger.info(f"FACTORY reset complete for {processor_id}")

            return ResetResult(
                success=True,
                level=ResetLevel.FACTORY,
                processor_id=processor_id,
                items_cleared=items_cleared,
            )

        except Exception as e:
            logger.error(f"FACTORY reset failed: {e}")
            errors.append(str(e))
            return ResetResult(
                success=False,
                level=ResetLevel.FACTORY,
                processor_id=processor_id,
                items_cleared=items_cleared,
                errors=errors,
            )

    def get_reset_stats(self) -> Dict[str, int]:
        """
        Get reset statistics.

        Returns:
            Dictionary of reset counts by level
        """
        return {
            level.value: count
            for level, count in self._reset_counts.items()
        }

    async def reset_with_callback(
        self,
        processor_id: str,
        pre_reset_callback=None,
        post_reset_callback=None,
    ) -> bool:
        """
        Perform golden image reset with callbacks.

        Args:
            processor_id: Processor ID to reset
            pre_reset_callback: Async callback before reset
            post_reset_callback: Async callback after reset

        Returns:
            True if reset was successful
        """
        # Pre-reset callback
        if pre_reset_callback:
            try:
                await pre_reset_callback()
            except Exception as e:
                logger.error(f"Pre-reset callback failed: {e}")

        # Perform reset
        success = await self.reset(processor_id)

        # Post-reset callback
        if post_reset_callback and success:
            try:
                await post_reset_callback()
            except Exception as e:
                logger.error(f"Post-reset callback failed: {e}")

        return success


class CacheResetManager:
    """
    Manages cache clearing during recovery.

    Clears in-memory caches while preserving persisted state.
    Used for lighter recovery than full golden image reset.
    """

    def __init__(self):
        """Initialize cache reset manager."""
        self._cache_clear_callbacks: list = []

    def register_cache(self, clear_callback) -> None:
        """
        Register a cache clear callback.

        Args:
            clear_callback: Function to call to clear cache
        """
        self._cache_clear_callbacks.append(clear_callback)

    async def clear_all_caches(self) -> int:
        """
        Clear all registered caches.

        Returns:
            Number of caches cleared
        """
        cleared = 0

        for callback in self._cache_clear_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                cleared += 1
            except Exception as e:
                logger.error(f"Cache clear failed: {e}")

        logger.info(f"Cleared {cleared} caches")
        return cleared


# Import for type checking
import asyncio
