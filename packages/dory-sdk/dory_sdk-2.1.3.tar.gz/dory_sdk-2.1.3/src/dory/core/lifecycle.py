"""
LifecycleManager - Manages processor lifecycle state machine.

Handles transitions between lifecycle states and enforces valid
state transitions.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from dory.types import LifecycleState
from dory.utils.errors import DoryStartupError, DoryShutdownError

if TYPE_CHECKING:
    from dory.core.processor import BaseProcessor
    from dory.core.context import ExecutionContext

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Manages the processor lifecycle state machine.

    States:
        CREATED -> STARTING -> RUNNING -> SHUTTING_DOWN -> STOPPED
                              |
                              v
                           FAILED (from any state on error)
    """

    # Valid state transitions
    VALID_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
        LifecycleState.CREATED: {LifecycleState.STARTING, LifecycleState.FAILED},
        LifecycleState.STARTING: {LifecycleState.RUNNING, LifecycleState.FAILED},
        LifecycleState.RUNNING: {LifecycleState.SHUTTING_DOWN, LifecycleState.FAILED},
        LifecycleState.SHUTTING_DOWN: {LifecycleState.STOPPED, LifecycleState.FAILED},
        LifecycleState.STOPPED: set(),  # Terminal state
        LifecycleState.FAILED: set(),   # Terminal state
    }

    def __init__(self):
        self._state = LifecycleState.CREATED
        self._state_lock = asyncio.Lock()
        self._state_changed = asyncio.Event()

    @property
    def state(self) -> LifecycleState:
        """Current lifecycle state."""
        return self._state

    def is_running(self) -> bool:
        """Check if processor is in running state."""
        return self._state == LifecycleState.RUNNING

    def is_stopped(self) -> bool:
        """Check if processor has stopped (gracefully or failed)."""
        return self._state in (LifecycleState.STOPPED, LifecycleState.FAILED)

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._state == LifecycleState.SHUTTING_DOWN

    async def transition_to(self, new_state: LifecycleState) -> None:
        """
        Transition to a new lifecycle state.

        Args:
            new_state: Target state

        Raises:
            ValueError: If transition is not valid
        """
        async with self._state_lock:
            if new_state not in self.VALID_TRANSITIONS.get(self._state, set()):
                raise ValueError(
                    f"Invalid state transition: {self._state.name} -> {new_state.name}"
                )

            old_state = self._state
            self._state = new_state
            self._state_changed.set()
            self._state_changed.clear()

            logger.debug(f"Lifecycle transition: {old_state.name} -> {new_state.name}")

    async def wait_for_state(
        self,
        target_states: set[LifecycleState],
        timeout: float | None = None,
    ) -> LifecycleState:
        """
        Wait for lifecycle to reach one of the target states.

        Args:
            target_states: Set of states to wait for
            timeout: Maximum time to wait (None = forever)

        Returns:
            The state that was reached

        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        while self._state not in target_states:
            try:
                await asyncio.wait_for(
                    self._state_changed.wait(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                raise

        return self._state

    async def run_startup(
        self,
        processor: "BaseProcessor",
        timeout: float = 60.0,
    ) -> None:
        """
        Run processor startup with timeout.

        Args:
            processor: Processor instance to start
            timeout: Maximum time for startup (seconds)

        Raises:
            DoryStartupError: If startup fails or times out
        """
        await self.transition_to(LifecycleState.STARTING)

        try:
            await asyncio.wait_for(
                processor.startup(),
                timeout=timeout,
            )
            await self.transition_to(LifecycleState.RUNNING)
            logger.info("Processor startup completed")

        except asyncio.TimeoutError:
            await self.transition_to(LifecycleState.FAILED)
            raise DoryStartupError(f"Startup timed out after {timeout}s")

        except Exception as e:
            await self.transition_to(LifecycleState.FAILED)
            raise DoryStartupError(f"Startup failed: {e}", cause=e)

    async def run_shutdown(
        self,
        processor: "BaseProcessor",
        timeout: float = 30.0,
    ) -> None:
        """
        Run processor shutdown with timeout.

        Args:
            processor: Processor instance to shutdown
            timeout: Maximum time for shutdown (seconds)

        Raises:
            DoryShutdownError: If shutdown times out
        """
        if self._state in (LifecycleState.STOPPED, LifecycleState.FAILED):
            return  # Already stopped

        await self.transition_to(LifecycleState.SHUTTING_DOWN)

        try:
            await asyncio.wait_for(
                processor.shutdown(),
                timeout=timeout,
            )
            await self.transition_to(LifecycleState.STOPPED)
            logger.info("Processor shutdown completed")

        except asyncio.TimeoutError:
            logger.error(f"Shutdown timed out after {timeout}s, forcing exit")
            await self.transition_to(LifecycleState.FAILED)
            raise DoryShutdownError(f"Shutdown timed out after {timeout}s")

        except Exception as e:
            # Log but continue - shutdown should complete
            logger.error(f"Error during shutdown: {e}")
            await self.transition_to(LifecycleState.STOPPED)

    async def run_main_loop(
        self,
        processor: "BaseProcessor",
        context: "ExecutionContext",
    ) -> None:
        """
        Run processor main loop until shutdown requested.

        Args:
            processor: Processor instance to run
            context: Execution context
        """
        if self._state != LifecycleState.RUNNING:
            raise ValueError(f"Cannot run: state is {self._state.name}, expected RUNNING")

        try:
            await processor.run()
            logger.info("Processor run() completed")

        except asyncio.CancelledError:
            logger.info("Processor run() cancelled")
            raise

        except Exception as e:
            logger.error(f"Error in processor run(): {e}")
            await self.transition_to(LifecycleState.FAILED)
            raise
