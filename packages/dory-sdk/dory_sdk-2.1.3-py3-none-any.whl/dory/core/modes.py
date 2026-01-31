"""
Processing Modes

Implements degraded mode and processing mode management for graceful degradation.
Allows processors to continue operating with reduced functionality instead of failing.

Processing Modes:
- FULL: Normal operation with all features
- DEGRADED: Reduced functionality, core operations only
- MINIMAL: Bare minimum processing, essential operations only
- RECOVERY: Recovery mode after failure, limited operations
- UNHEALTHY: System unhealthy, should not process new requests
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Set

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """
    Processing mode levels from full to unhealthy.
    """
    FULL = "full"               # Normal operation, all features available
    DEGRADED = "degraded"       # Reduced functionality, core operations only
    MINIMAL = "minimal"         # Bare minimum, essential operations only
    RECOVERY = "recovery"       # Recovery mode after failure
    UNHEALTHY = "unhealthy"     # System unhealthy, should not process


class ModeTransitionReason(Enum):
    """Reasons for mode transitions."""
    MANUAL = "manual"                       # Manual mode change
    ERROR_RATE = "error_rate"              # High error rate detected
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Memory/CPU exhaustion
    DEPENDENCY_FAILURE = "dependency_failure"    # External dependency failed
    CIRCUIT_OPEN = "circuit_open"          # Circuit breaker opened
    RECOVERY_ATTEMPT = "recovery_attempt"  # Attempting recovery
    RECOVERY_SUCCESS = "recovery_success"  # Recovery successful
    HEALTH_CHECK_FAILED = "health_check_failed"  # Health check failed
    STARTUP = "startup"                    # System startup
    SHUTDOWN = "shutdown"                  # System shutdown


@dataclass
class ModeTransition:
    """
    Represents a mode transition event.
    """
    from_mode: ProcessingMode
    to_mode: ProcessingMode
    reason: ModeTransitionReason
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_mode": self.from_mode.value,
            "to_mode": self.to_mode.value,
            "reason": self.reason.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ModeConfig:
    """
    Configuration for a processing mode.
    """
    mode: ProcessingMode
    enabled_features: Set[str]
    disabled_features: Set[str]
    max_concurrent_requests: Optional[int] = None
    timeout_seconds: Optional[float] = None
    priority_only: bool = False  # Only process high-priority requests
    description: str = ""

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled in this mode."""
        return feature in self.enabled_features


class ModeManager:
    """
    Manages processing modes and transitions between them.

    Features:
    - Automatic mode transitions based on conditions
    - Mode transition history
    - Feature availability by mode
    - Graceful degradation
    - Mode-specific callbacks

    Usage:
        manager = ModeManager()

        # Configure modes
        manager.configure_mode(
            ProcessingMode.DEGRADED,
            enabled_features=["core_processing"],
            disabled_features=["analytics", "notifications"]
        )

        # Transition to degraded mode
        await manager.transition_to(
            ProcessingMode.DEGRADED,
            reason=ModeTransitionReason.ERROR_RATE
        )

        # Check feature availability
        if manager.is_feature_enabled("analytics"):
            # Do analytics
            pass
    """

    def __init__(
        self,
        initial_mode: ProcessingMode = ProcessingMode.FULL,
        auto_recovery: bool = True,
        recovery_check_interval: float = 60.0,
    ):
        """
        Initialize mode manager.

        Args:
            initial_mode: Starting processing mode
            auto_recovery: Automatically try to recover to higher modes
            recovery_check_interval: Interval for recovery checks (seconds)
        """
        self._current_mode = initial_mode
        self._auto_recovery = auto_recovery
        self._recovery_check_interval = recovery_check_interval

        # Mode configurations
        self._mode_configs: Dict[ProcessingMode, ModeConfig] = {}
        self._initialize_default_configs()

        # Transition history
        self._transition_history: List[ModeTransition] = []
        self._max_history = 100

        # Callbacks
        self._on_transition_callbacks: List[Callable] = []

        # Recovery task
        self._recovery_task: Optional[asyncio.Task] = None

        # Metrics
        self._transition_count = 0
        self._mode_durations: Dict[ProcessingMode, float] = {
            mode: 0.0 for mode in ProcessingMode
        }
        self._last_transition_time = asyncio.get_event_loop().time()

        logger.info(f"ModeManager initialized: mode={initial_mode.value}")

    def _initialize_default_configs(self) -> None:
        """Initialize default mode configurations."""
        # FULL mode - all features enabled
        self._mode_configs[ProcessingMode.FULL] = ModeConfig(
            mode=ProcessingMode.FULL,
            enabled_features={"*"},  # All features
            disabled_features=set(),
            description="Normal operation with all features",
        )

        # DEGRADED mode - core features only
        self._mode_configs[ProcessingMode.DEGRADED] = ModeConfig(
            mode=ProcessingMode.DEGRADED,
            enabled_features={"core_processing", "state_persistence", "error_handling"},
            disabled_features={"analytics", "notifications", "background_jobs"},
            max_concurrent_requests=50,
            description="Reduced functionality, core operations only",
        )

        # MINIMAL mode - essential operations only
        self._mode_configs[ProcessingMode.MINIMAL] = ModeConfig(
            mode=ProcessingMode.MINIMAL,
            enabled_features={"core_processing", "error_handling"},
            disabled_features={"analytics", "notifications", "background_jobs", "state_persistence"},
            max_concurrent_requests=10,
            priority_only=True,
            description="Bare minimum processing, essential operations only",
        )

        # RECOVERY mode - recovery operations
        self._mode_configs[ProcessingMode.RECOVERY] = ModeConfig(
            mode=ProcessingMode.RECOVERY,
            enabled_features={"error_handling", "recovery"},
            disabled_features={"*"},  # Most features disabled
            max_concurrent_requests=1,
            description="Recovery mode after failure",
        )

        # UNHEALTHY mode - no processing
        self._mode_configs[ProcessingMode.UNHEALTHY] = ModeConfig(
            mode=ProcessingMode.UNHEALTHY,
            enabled_features=set(),
            disabled_features={"*"},
            max_concurrent_requests=0,
            description="System unhealthy, should not process",
        )

    def configure_mode(
        self,
        mode: ProcessingMode,
        enabled_features: Optional[Set[str]] = None,
        disabled_features: Optional[Set[str]] = None,
        max_concurrent_requests: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        priority_only: bool = False,
        description: str = "",
    ) -> None:
        """
        Configure a processing mode.

        Args:
            mode: Mode to configure
            enabled_features: Set of enabled feature names
            disabled_features: Set of disabled feature names
            max_concurrent_requests: Max concurrent requests in this mode
            timeout_seconds: Timeout for operations in this mode
            priority_only: Only process high-priority requests
            description: Mode description
        """
        config = self._mode_configs.get(mode)
        if config:
            # Update existing config
            if enabled_features is not None:
                config.enabled_features = enabled_features
            if disabled_features is not None:
                config.disabled_features = disabled_features
            if max_concurrent_requests is not None:
                config.max_concurrent_requests = max_concurrent_requests
            if timeout_seconds is not None:
                config.timeout_seconds = timeout_seconds
            if priority_only:
                config.priority_only = priority_only
            if description:
                config.description = description
        else:
            # Create new config
            self._mode_configs[mode] = ModeConfig(
                mode=mode,
                enabled_features=enabled_features or set(),
                disabled_features=disabled_features or set(),
                max_concurrent_requests=max_concurrent_requests,
                timeout_seconds=timeout_seconds,
                priority_only=priority_only,
                description=description,
            )

        logger.info(f"Mode configured: {mode.value} with {len(enabled_features or [])} features")

    async def transition_to(
        self,
        target_mode: ProcessingMode,
        reason: ModeTransitionReason,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Transition to a new processing mode.

        Args:
            target_mode: Target mode
            reason: Reason for transition
            metadata: Optional metadata about transition

        Returns:
            True if transition successful
        """
        if target_mode == self._current_mode:
            logger.debug(f"Already in {target_mode.value} mode")
            return True

        logger.info(
            f"Mode transition: {self._current_mode.value} -> {target_mode.value} "
            f"(reason: {reason.value})"
        )

        # Record transition
        current_time = asyncio.get_event_loop().time()
        transition = ModeTransition(
            from_mode=self._current_mode,
            to_mode=target_mode,
            reason=reason,
            timestamp=current_time,
            metadata=metadata or {},
        )

        # Update mode duration
        duration = current_time - self._last_transition_time
        self._mode_durations[self._current_mode] += duration
        self._last_transition_time = current_time

        # Change mode
        old_mode = self._current_mode
        self._current_mode = target_mode

        # Update history
        self._transition_history.append(transition)
        if len(self._transition_history) > self._max_history:
            self._transition_history.pop(0)

        # Update metrics
        self._transition_count += 1

        # Call transition callbacks
        for callback in self._on_transition_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(transition)
                else:
                    callback(transition)
            except Exception as e:
                logger.error(f"Transition callback failed: {e}")

        logger.info(f"Mode transition complete: now in {target_mode.value}")

        # Start auto-recovery if transitioning to degraded/minimal/recovery
        if self._auto_recovery and target_mode in [
            ProcessingMode.DEGRADED,
            ProcessingMode.MINIMAL,
            ProcessingMode.RECOVERY,
        ]:
            self._start_auto_recovery()

        return True

    def get_current_mode(self) -> ProcessingMode:
        """Get current processing mode."""
        return self._current_mode

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled in current mode.

        Args:
            feature: Feature name

        Returns:
            True if enabled
        """
        config = self._mode_configs.get(self._current_mode)
        if not config:
            return False

        # Check wildcard
        if "*" in config.enabled_features:
            return feature not in config.disabled_features

        # Check explicit enable/disable
        if feature in config.disabled_features:
            return False

        return feature in config.enabled_features

    def get_mode_config(self, mode: Optional[ProcessingMode] = None) -> ModeConfig:
        """
        Get configuration for a mode.

        Args:
            mode: Mode to get config for (current mode if None)

        Returns:
            ModeConfig
        """
        mode = mode or self._current_mode
        return self._mode_configs[mode]

    def can_process_requests(self) -> bool:
        """Check if system can process requests in current mode."""
        return self._current_mode != ProcessingMode.UNHEALTHY

    def get_max_concurrent_requests(self) -> Optional[int]:
        """Get max concurrent requests for current mode."""
        config = self._mode_configs.get(self._current_mode)
        return config.max_concurrent_requests if config else None

    def on_transition(self, callback: Callable) -> None:
        """
        Register a callback for mode transitions.

        Args:
            callback: Callable that receives ModeTransition
        """
        self._on_transition_callbacks.append(callback)

    def get_transition_history(self, limit: Optional[int] = None) -> List[ModeTransition]:
        """
        Get mode transition history.

        Args:
            limit: Maximum number of transitions to return

        Returns:
            List of transitions (most recent first)
        """
        history = list(reversed(self._transition_history))
        if limit:
            history = history[:limit]
        return history

    def get_stats(self) -> Dict[str, Any]:
        """
        Get mode manager statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "current_mode": self._current_mode.value,
            "transition_count": self._transition_count,
            "mode_durations": {
                mode.value: duration
                for mode, duration in self._mode_durations.items()
            },
            "auto_recovery_enabled": self._auto_recovery,
            "features_enabled": len([
                f for f in ["core", "analytics", "notifications"]
                if self.is_feature_enabled(f)
            ]),
        }

    def _start_auto_recovery(self) -> None:
        """Start automatic recovery task."""
        if self._recovery_task and not self._recovery_task.done():
            return

        self._recovery_task = asyncio.create_task(self._auto_recovery_loop())

    async def _auto_recovery_loop(self) -> None:
        """Automatic recovery loop to attempt mode upgrades."""
        logger.info("Starting auto-recovery loop")

        while self._auto_recovery and self._current_mode != ProcessingMode.FULL:
            await asyncio.sleep(self._recovery_check_interval)

            # Try to upgrade mode
            if self._current_mode == ProcessingMode.RECOVERY:
                # Try to go to MINIMAL
                logger.info("Attempting recovery: RECOVERY -> MINIMAL")
                await self.transition_to(
                    ProcessingMode.MINIMAL,
                    ModeTransitionReason.RECOVERY_ATTEMPT,
                )
            elif self._current_mode == ProcessingMode.MINIMAL:
                # Try to go to DEGRADED
                logger.info("Attempting recovery: MINIMAL -> DEGRADED")
                await self.transition_to(
                    ProcessingMode.DEGRADED,
                    ModeTransitionReason.RECOVERY_ATTEMPT,
                )
            elif self._current_mode == ProcessingMode.DEGRADED:
                # Try to go to FULL
                logger.info("Attempting recovery: DEGRADED -> FULL")
                await self.transition_to(
                    ProcessingMode.FULL,
                    ModeTransitionReason.RECOVERY_SUCCESS,
                )

        logger.info("Auto-recovery loop stopped")

    async def stop_auto_recovery(self) -> None:
        """Stop automatic recovery."""
        self._auto_recovery = False
        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass
