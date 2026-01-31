"""
Metaclass for automatic handler instrumentation.

Automatically applies @auto_instrument to all async methods
starting with "handle_" or "_handle_".

No manual decorators needed!
"""

import inspect
import logging
from abc import ABCMeta
from typing import Any

logger = logging.getLogger(__name__)


class AutoInstrumentMeta(ABCMeta):
    """
    Metaclass that automatically applies @auto_instrument to handler methods.

    This eliminates the need for developers to add decorators manually.

    Usage:
        class MyProcessor(BaseProcessor, metaclass=AutoInstrumentMeta):
            async def handle_request(self, request):
                # Automatically instrumented!
                # - Request ID generated
                # - Request tracked
                # - Span created
                # - Errors classified
                return {"status": "ok"}

            async def handle_webhook(self, webhook):
                # Also automatically instrumented!
                return {"received": True}

            async def internal_method(self):
                # NOT instrumented (doesn't start with handle_)
                pass

    Auto-instrumented methods:
    - async def handle_*(...): Public handlers
    - async def _handle_*(...): Private handlers

    Not instrumented:
    - Other methods (don't start with handle_)
    - Sync methods
    - Lifecycle methods (startup, shutdown, run)
    """

    # List of methods that should NOT be auto-instrumented
    EXCLUDED_METHODS = {
        "startup",
        "shutdown",
        "run",
        "get_state",
        "restore_state",
        "on_state_restore_failed",
        "on_rapid_restart_detected",
        "on_health_check_failed",
        "reset_caches",
        "run_loop",
        "is_shutting_down",
    }

    def __new__(mcs, name, bases, namespace):
        """
        Create new class with auto-instrumented handler methods.

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace (attributes and methods)

        Returns:
            New class with auto-instrumented handlers
        """
        # Import here to avoid circular dependency
        try:
            from dory.auto_instrument import auto_instrument
        except ImportError:
            logger.warning(
                "auto_instrument decorator not available, skipping auto-instrumentation"
            )
            return super().__new__(mcs, name, bases, namespace)

        # Count of instrumented methods
        instrumented_count = 0

        # Auto-instrument handler methods
        for attr_name, attr_value in list(namespace.items()):
            # Check if this is an async method
            if not inspect.iscoroutinefunction(attr_value):
                continue

            # Check if method should be instrumented
            should_instrument = False

            # Instrument methods starting with handle_ or _handle_
            if attr_name.startswith("handle_") or attr_name.startswith("_handle_"):
                should_instrument = True

            # Don't instrument excluded methods
            if attr_name in mcs.EXCLUDED_METHODS:
                should_instrument = False

            # Don't instrument special methods
            if attr_name.startswith("__") and attr_name.endswith("__"):
                should_instrument = False

            # Apply auto-instrumentation
            if should_instrument:
                namespace[attr_name] = auto_instrument(attr_value)
                instrumented_count += 1
                logger.debug(f"Auto-instrumented method: {name}.{attr_name}")

        if instrumented_count > 0:
            logger.info(f"Auto-instrumented {instrumented_count} methods in {name}")

        return super().__new__(mcs, name, bases, namespace)
