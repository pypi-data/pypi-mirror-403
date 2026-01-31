"""
SignalHandler - Handles OS signals for graceful shutdown.

Captures SIGTERM, SIGINT, and SIGUSR1 and triggers appropriate
actions in the SDK.
"""

import asyncio
import logging
import signal
import sys
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class SignalHandler:
    """
    Handles OS signals for graceful shutdown.

    Signals handled:
        SIGTERM: Graceful shutdown (from Kubelet)
        SIGINT: Graceful shutdown (Ctrl+C for local testing)
        SIGUSR1: Trigger state snapshot (for debugging)
    """

    def __init__(self):
        self._shutdown_callback: Callable[[], Awaitable[None]] | None = None
        self._snapshot_callback: Callable[[], Awaitable[None]] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._shutdown_triggered = False

    def setup(
        self,
        shutdown_callback: Callable[[], Awaitable[None]],
        snapshot_callback: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        """
        Setup signal handlers.

        Args:
            shutdown_callback: Async callback for graceful shutdown
            snapshot_callback: Optional async callback for state snapshot
        """
        self._shutdown_callback = shutdown_callback
        self._snapshot_callback = snapshot_callback
        self._loop = asyncio.get_event_loop()

        # Register signal handlers
        if sys.platform != "win32":
            # Unix signals
            self._loop.add_signal_handler(
                signal.SIGTERM,
                self._handle_shutdown_signal,
                "SIGTERM",
            )
            self._loop.add_signal_handler(
                signal.SIGINT,
                self._handle_shutdown_signal,
                "SIGINT",
            )
            self._loop.add_signal_handler(
                signal.SIGUSR1,
                self._handle_snapshot_signal,
            )
            logger.debug("Signal handlers registered (Unix)")
        else:
            # Windows - limited signal support
            signal.signal(signal.SIGTERM, self._handle_shutdown_signal_sync)
            signal.signal(signal.SIGINT, self._handle_shutdown_signal_sync)
            logger.debug("Signal handlers registered (Windows)")

    def _handle_shutdown_signal(self, sig_name: str) -> None:
        """Handle SIGTERM/SIGINT asynchronously."""
        if self._shutdown_triggered:
            logger.warning(f"Received {sig_name} but shutdown already in progress")
            return

        self._shutdown_triggered = True
        logger.info(f"Received {sig_name}, initiating graceful shutdown")

        if self._shutdown_callback and self._loop:
            asyncio.ensure_future(
                self._shutdown_callback(),
                loop=self._loop,
            )

    def _handle_shutdown_signal_sync(self, signum: int, frame) -> None:
        """Handle signal synchronously (Windows compatibility)."""
        sig_name = signal.Signals(signum).name
        self._handle_shutdown_signal(sig_name)

    def _handle_snapshot_signal(self) -> None:
        """Handle SIGUSR1 for debug state snapshot."""
        logger.info("Received SIGUSR1, triggering state snapshot")

        if self._snapshot_callback and self._loop:
            asyncio.ensure_future(
                self._snapshot_callback(),
                loop=self._loop,
            )

    def remove_handlers(self) -> None:
        """Remove signal handlers during shutdown."""
        if self._loop and sys.platform != "win32":
            try:
                self._loop.remove_signal_handler(signal.SIGTERM)
                self._loop.remove_signal_handler(signal.SIGINT)
                self._loop.remove_signal_handler(signal.SIGUSR1)
                logger.debug("Signal handlers removed")
            except (ValueError, RuntimeError):
                # Handler not registered or loop closed
                pass

    @property
    def shutdown_triggered(self) -> bool:
        """Check if shutdown has been triggered."""
        return self._shutdown_triggered

    def reset(self) -> None:
        """Reset shutdown state (for testing)."""
        self._shutdown_triggered = False
