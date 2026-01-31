"""
Decorators for simplified Dory SDK integration.

Provides @stateful decorator for automatic state management,
eliminating the need to manually implement get_state() and restore_state().
"""

from dataclasses import dataclass, field
from typing import Any, TypeVar, Generic, Callable

T = TypeVar('T')


@dataclass
class StatefulVar(Generic[T]):
    """
    A stateful variable that automatically participates in state save/restore.

    Usage:
        from dory import stateful

        class MyProcessor(BaseProcessor):
            counter = stateful(0)
            sessions = stateful(dict)

            async def run(self):
                self.counter += 1  # Automatically saved/restored
    """
    _default: T | Callable[[], T]
    _name: str = ""
    _value: T = field(default=None, repr=False)
    _initialized: bool = field(default=False, repr=False)

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when descriptor is assigned to a class attribute."""
        self._name = name
        # Register this stateful var with the class
        if not hasattr(owner, '_stateful_vars'):
            owner._stateful_vars = {}
        owner._stateful_vars[name] = self

    def __get__(self, obj: Any, objtype: type | None = None) -> T:
        """Get the current value."""
        if obj is None:
            return self

        # Initialize on first access
        if not hasattr(obj, f'_stateful_{self._name}_value'):
            default = self._default() if callable(self._default) else self._default
            setattr(obj, f'_stateful_{self._name}_value', default)

        return getattr(obj, f'_stateful_{self._name}_value')

    def __set__(self, obj: Any, value: T) -> None:
        """Set the value."""
        setattr(obj, f'_stateful_{self._name}_value', value)


def stateful(default: T | Callable[[], T] = None) -> StatefulVar[T]:
    """
    Mark a class attribute as stateful for automatic state management.

    The SDK will automatically include this attribute in get_state() output
    and restore it in restore_state().

    Args:
        default: Default value or factory function (use factory for mutable defaults)

    Usage:
        class MyProcessor(BaseProcessor):
            # Simple values
            counter = stateful(0)
            name = stateful("default")

            # Mutable defaults (use factory to avoid sharing)
            sessions = stateful(dict)  # Same as stateful(lambda: {})
            items = stateful(list)     # Same as stateful(lambda: [])

    Example:
        from dory import DoryApp, BaseProcessor, stateful

        class MyProcessor(BaseProcessor):
            counter = stateful(0)
            data = stateful(dict)

            async def run(self):
                while not self.context.is_shutdown_requested():
                    self.counter += 1
                    await asyncio.sleep(1)

            # No need to implement get_state() or restore_state()!
            # SDK handles it automatically.
    """
    return StatefulVar(_default=default)


def get_stateful_vars(obj: Any) -> dict[str, Any]:
    """
    Get all stateful variables from an object.

    Used internally by SDK to auto-generate get_state().
    """
    cls = type(obj)
    if not hasattr(cls, '_stateful_vars'):
        return {}

    result = {}
    for name in cls._stateful_vars:
        result[name] = getattr(obj, name)
    return result


def set_stateful_vars(obj: Any, state: dict[str, Any]) -> None:
    """
    Set stateful variables on an object from state dict.

    Used internally by SDK to auto-generate restore_state().
    """
    cls = type(obj)
    if not hasattr(cls, '_stateful_vars'):
        return

    for name in cls._stateful_vars:
        if name in state:
            setattr(obj, name, state[name])


class StatefulMixin:
    """
    Mixin that provides automatic get_state() and restore_state() for @stateful vars.

    If a class has @stateful decorated attributes but doesn't override
    get_state()/restore_state(), this mixin provides default implementations.
    """

    def _get_stateful_state(self) -> dict:
        """Get state from @stateful decorated attributes."""
        return get_stateful_vars(self)

    def _set_stateful_state(self, state: dict) -> None:
        """Set state to @stateful decorated attributes."""
        set_stateful_vars(self, state)
