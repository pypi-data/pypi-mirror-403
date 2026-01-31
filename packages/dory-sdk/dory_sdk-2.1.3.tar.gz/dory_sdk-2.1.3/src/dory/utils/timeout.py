"""
Timeout utilities for async operations.
"""

import asyncio
import functools
from dataclasses import dataclass
from typing import Callable, TypeVar, ParamSpec, Awaitable

from dory.utils.errors import DoryTimeoutError

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class TimeoutConfig:
    """Configuration for timeout behavior."""

    timeout_seconds: float
    error_message: str | None = None


async def timeout_async(
    func: Callable[P, Awaitable[T]],
    *args: P.args,
    timeout_seconds: float,
    error_message: str | None = None,
    **kwargs: P.kwargs,
) -> T:
    """
    Execute an async function with a timeout.

    Args:
        func: Async function to execute
        *args: Positional arguments for func
        timeout_seconds: Maximum time to wait
        error_message: Custom error message on timeout
        **kwargs: Keyword arguments for func

    Returns:
        Result of func

    Raises:
        DoryTimeoutError: If function doesn't complete within timeout
    """
    try:
        return await asyncio.wait_for(
            func(*args, **kwargs),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        msg = error_message or f"Operation timed out after {timeout_seconds}s"
        raise DoryTimeoutError(msg)


def with_timeout(
    timeout_seconds: float,
    error_message: str | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator to add timeout to async functions.

    Usage:
        @with_timeout(30, "Startup took too long")
        async def startup():
            ...
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await timeout_async(
                func,
                *args,
                timeout_seconds=timeout_seconds,
                error_message=error_message,
                **kwargs,
            )
        return wrapper
    return decorator
