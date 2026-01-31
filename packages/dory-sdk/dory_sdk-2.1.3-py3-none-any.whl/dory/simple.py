"""
Simple function-based API for Dory processors.

For applications that don't need the full class-based API,
this module provides a simpler decorator-based approach.

Usage:
    from dory.simple import processor, state

    counter = state(0)

    @processor
    async def main(ctx):
        async for _ in ctx.run_loop(interval=1):
            counter.value += 1
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, TypeVar, Generic

from dory.core.app import DoryApp
from dory.core.processor import BaseProcessor
from dory.core.context import ExecutionContext

T = TypeVar('T')


@dataclass
class StateVar(Generic[T]):
    """
    A state variable for function-based processors.

    Usage:
        counter = state(0)
        sessions = state(dict)  # Factory for mutable defaults

        @processor
        async def main(ctx):
            counter.value += 1
            sessions.value["user1"] = data
    """
    _default: T | Callable[[], T]
    _value: T = field(default=None, init=False, repr=False)
    _initialized: bool = field(default=False, init=False)

    @property
    def value(self) -> T:
        """Get the current value."""
        if not self._initialized:
            if callable(self._default):
                self._value = self._default()
            else:
                self._value = self._default
            self._initialized = True
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        """Set a new value."""
        self._value = new_value
        self._initialized = True

    def reset(self) -> None:
        """Reset to default value."""
        self._initialized = False

    def get(self) -> T:
        """Alias for value property."""
        return self.value

    def set(self, new_value: T) -> None:
        """Alias for value setter."""
        self.value = new_value


def state(default: T | Callable[[], T] = None) -> StateVar[T]:
    """
    Create a state variable for function-based processors.

    State variables are automatically saved and restored during migrations.

    Args:
        default: Default value or factory function for mutable defaults

    Usage:
        # Simple values
        counter = state(0)
        name = state("default")

        # Mutable values (use factory)
        data = state(dict)   # Creates new dict each time
        items = state(list)  # Creates new list each time

        @processor
        async def main(ctx):
            counter.value += 1
            data.value["key"] = "value"
    """
    return StateVar(_default=default)


# Global registry of state variables for current processor
_state_registry: dict[str, StateVar] = {}


def _register_state(name: str, var: StateVar) -> None:
    """Register a state variable (called by processor decorator)."""
    _state_registry[name] = var


def _get_all_state() -> dict[str, Any]:
    """Get all state values."""
    return {name: var.value for name, var in _state_registry.items()}


def _set_all_state(values: dict[str, Any]) -> None:
    """Set all state values."""
    for name, value in values.items():
        if name in _state_registry:
            _state_registry[name].value = value


class FunctionProcessor(BaseProcessor):
    """
    Wrapper that converts a function into a BaseProcessor.

    Internal use by @processor decorator.
    """

    def __init__(
        self,
        func: Callable[[ExecutionContext], Awaitable[None]],
        state_vars: dict[str, StateVar],
        context: ExecutionContext | None = None,
    ):
        super().__init__(context)
        self._func = func
        self._state_vars = state_vars

    async def run(self) -> None:
        """Run the wrapped function."""
        await self._func(self.context)

    def get_state(self) -> dict:
        """Get state from registered state variables."""
        return {name: var.value for name, var in self._state_vars.items()}

    async def restore_state(self, state: dict) -> None:
        """Restore state to registered state variables."""
        for name, value in state.items():
            if name in self._state_vars:
                self._state_vars[name].value = value


class ContextWrapper:
    """
    Wrapper around ExecutionContext with additional helpers for function-based API.

    Provides run_loop() and other conveniences directly on ctx.
    """

    def __init__(self, context: ExecutionContext):
        self._context = context

    def __getattr__(self, name: str) -> Any:
        """Delegate to underlying context."""
        return getattr(self._context, name)

    async def run_loop(
        self,
        interval: float = 1.0,
        check_migration: bool = True,
    ):
        """
        Async iterator that yields until shutdown is requested.

        Usage:
            @processor
            async def main(ctx):
                async for i in ctx.run_loop(interval=1):
                    counter.value += 1
        """
        iteration = 0
        while not self._context.is_shutdown_requested():
            yield iteration
            iteration += 1

            if check_migration and self._context.is_migration_imminent():
                self._context.logger().info(
                    f"Migration imminent, completing iteration {iteration}"
                )

            await asyncio.sleep(interval)

    @property
    def shutdown_requested(self) -> bool:
        """Check if shutdown is requested (simpler than is_shutdown_requested())."""
        return self._context.is_shutdown_requested()

    @property
    def migration_imminent(self) -> bool:
        """Check if migration is imminent (simpler than is_migration_imminent())."""
        return self._context.is_migration_imminent()


def processor(
    func: Callable[[ContextWrapper], Awaitable[None]] | None = None,
    *,
    config_file: str | None = None,
    log_level: str | None = None,
):
    """
    Decorator to create a Dory processor from a simple async function.

    This is the simplest way to create a Dory processor. Just decorate
    your main async function and it handles everything else.

    Args:
        func: The async function to wrap
        config_file: Optional path to config file
        log_level: Optional log level override

    Usage:
        # Minimal stateless processor
        from dory.simple import processor

        @processor
        async def main(ctx):
            while not ctx.shutdown_requested:
                print("Working...")
                await asyncio.sleep(1)

        # With state
        from dory.simple import processor, state

        counter = state(0)
        data = state(dict)

        @processor
        async def main(ctx):
            async for i in ctx.run_loop(interval=1):
                counter.value += 1
                print(f"Count: {counter.value}")

        # With config
        @processor(config_file="dory.yaml", log_level="DEBUG")
        async def main(ctx):
            ...
    """
    def decorator(fn: Callable[[ContextWrapper], Awaitable[None]]):
        # Collect state variables from the module
        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            module_globals = frame.f_back.f_back.f_globals
            state_vars = {
                name: var
                for name, var in module_globals.items()
                if isinstance(var, StateVar)
            }
        else:
            state_vars = {}

        # Create wrapper function that wraps context
        async def wrapped_func(context: ExecutionContext) -> None:
            wrapper = ContextWrapper(context)
            await fn(wrapper)

        # Create processor class dynamically
        class DynamicProcessor(FunctionProcessor):
            def __init__(self, context: ExecutionContext | None = None):
                super().__init__(wrapped_func, state_vars, context)

        # Run immediately if this is the main module
        if frame and frame.f_back and frame.f_back.f_back:
            if module_globals.get("__name__") == "__main__":
                DoryApp(
                    config_file=config_file,
                    log_level=log_level,
                ).run(DynamicProcessor)

        return fn

    if func is not None:
        # Called without arguments: @processor
        return decorator(func)
    else:
        # Called with arguments: @processor(config_file="...")
        return decorator


def run_processor(
    func: Callable[[ContextWrapper], Awaitable[None]],
    *,
    config_file: str | None = None,
    log_level: str | None = None,
) -> None:
    """
    Run a function as a Dory processor.

    Alternative to @processor decorator when you want explicit control.

    Usage:
        from dory.simple import run_processor, state

        counter = state(0)

        async def main(ctx):
            async for _ in ctx.run_loop(interval=1):
                counter.value += 1

        if __name__ == "__main__":
            run_processor(main)
    """
    # Collect state variables from caller's module
    frame = inspect.currentframe()
    if frame and frame.f_back:
        module_globals = frame.f_back.f_globals
        state_vars = {
            name: var
            for name, var in module_globals.items()
            if isinstance(var, StateVar)
        }
    else:
        state_vars = {}

    # Create wrapper function
    async def wrapped_func(context: ExecutionContext) -> None:
        wrapper = ContextWrapper(context)
        await func(wrapper)

    # Create processor class
    class DynamicProcessor(FunctionProcessor):
        def __init__(self, context: ExecutionContext | None = None):
            super().__init__(wrapped_func, state_vars, context)

    # Run
    DoryApp(
        config_file=config_file,
        log_level=log_level,
    ).run(DynamicProcessor)
