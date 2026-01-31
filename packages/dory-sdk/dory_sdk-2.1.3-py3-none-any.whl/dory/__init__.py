"""
Dory SDK - Python Integration Package for Processor Applications

This SDK handles all operational concerns (graceful shutdown, state migration,
health checks, observability) so developers focus solely on business logic.

Quick Start (Class-based API):
    from dory import DoryApp, BaseProcessor, stateful

    class MyProcessor(BaseProcessor):
        counter = stateful(0)  # Auto-saved/restored

        async def run(self):
            async for _ in self.run_loop(interval=1):
                self.counter += 1

    if __name__ == '__main__':
        DoryApp().run(MyProcessor)

Quick Start (Function-based API):
    from dory.simple import processor, state

    counter = state(0)

    @processor
    async def main(ctx):
        async for _ in ctx.run_loop(interval=1):
            counter.value += 1
"""

__version__ = "2.1.2"

# Core API
from dory.core.processor import BaseProcessor
from dory.core.context import ExecutionContext
from dory.core.app import DoryApp

# Configuration
from dory.config.schema import DoryConfig

# Decorators for simplified integration
from dory.decorators import stateful, StatefulVar

# Exceptions
from dory.utils.errors import (
    DoryError,
    DoryStartupError,
    DoryShutdownError,
    DoryStateError,
    DoryConfigError,
)

__all__ = [
    # Core API
    "BaseProcessor",
    "ExecutionContext",
    "DoryApp",
    "DoryConfig",
    # Decorators
    "stateful",
    "StatefulVar",
    # Exceptions
    "DoryError",
    "DoryStartupError",
    "DoryShutdownError",
    "DoryStateError",
    "DoryConfigError",
    # Version
    "__version__",
]
