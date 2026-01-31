"""
Retry utilities with exponential backoff.
"""

import asyncio
import functools
import random
from dataclasses import dataclass, field
from typing import Callable, TypeVar, ParamSpec, Awaitable
import logging

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (Exception,)
    )


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """Calculate delay for next retry with exponential backoff."""
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)

    if config.jitter:
        # Add random jitter (0-25% of delay)
        delay = delay * (1 + random.uniform(0, 0.25))

    return delay


async def retry_async(
    func: Callable[P, Awaitable[T]],
    *args: P.args,
    config: RetryConfig | None = None,
    **kwargs: P.kwargs,
) -> T:
    """
    Execute an async function with retry logic.

    Args:
        func: Async function to execute
        *args: Positional arguments for func
        config: Retry configuration (uses defaults if None)
        **kwargs: Keyword arguments for func

    Returns:
        Result of func

    Raises:
        Last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()

    last_exception: Exception | None = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e

            if attempt == config.max_attempts:
                logger.warning(
                    f"Retry exhausted after {attempt} attempts: {e}"
                )
                break

            delay = calculate_delay(attempt, config)
            logger.debug(
                f"Retry attempt {attempt}/{config.max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s"
            )
            await asyncio.sleep(delay)

    if last_exception:
        raise last_exception

    # Should never reach here, but satisfy type checker
    raise RuntimeError("Retry logic error")


def with_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator to add retry logic to async functions.

    Usage:
        @with_retry(RetryConfig(max_attempts=5))
        async def my_flaky_function():
            ...
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await retry_async(func, *args, config=config, **kwargs)
        return wrapper
    return decorator
