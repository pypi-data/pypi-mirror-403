"""
Retry with exponential backoff implementation.

Provides automatic retry logic with:
- Exponential backoff with jitter
- Retry budgets to prevent retry storms
- Per-exception-type retry policies
- Comprehensive metrics

Usage:
    @retry_with_backoff(max_attempts=3)
    async def call_api():
        return await api.get()
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when retry attempts are exhausted."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Retry exhausted after {attempts} attempts. Last error: {last_error}"
        )


@dataclass
class RetryPolicy:
    """
    Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 30.0)
        multiplier: Exponential backoff multiplier (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        retryable_exceptions: Tuple of exceptions to retry (default: Exception)
        non_retryable_exceptions: Exceptions that should never be retried
        on_retry: Optional callback called on each retry attempt
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    multiplier: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = ()
    on_retry: Optional[Callable[[int, Exception], None]] = None

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Uses exponential backoff: delay = initial_delay * (multiplier ** attempt)
        Caps at max_delay and adds jitter if enabled.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(self.initial_delay * (self.multiplier**attempt), self.max_delay)

        if self.jitter:
            # Add +/- 25% jitter
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)  # Ensure non-negative

    def is_retryable(self, error: Exception) -> bool:
        """
        Determine if an error should be retried.

        Args:
            error: The exception that occurred

        Returns:
            True if error should be retried, False otherwise
        """
        # Non-retryable takes precedence
        if isinstance(error, self.non_retryable_exceptions):
            return False

        return isinstance(error, self.retryable_exceptions)


@dataclass
class RetryBudget:
    """
    Retry budget to prevent retry storms.

    Limits the percentage of requests that can be retried within a time window.
    This prevents cascading failures where retries overwhelm the system.

    Attributes:
        budget_percent: Percentage of requests allowed to retry (0-100)
        window_seconds: Time window in seconds (default: 60)
        _requests: Total requests in current window
        _retries: Retry attempts in current window
        _window_start: Start time of current window
    """

    budget_percent: float = 20.0  # Allow 20% of requests to retry
    window_seconds: float = 60.0
    _requests: int = field(default=0, init=False)
    _retries: int = field(default=0, init=False)
    _window_start: float = field(default_factory=time.time, init=False)

    def can_retry(self) -> bool:
        """
        Check if retry is allowed within budget.

        Returns:
            True if retry is within budget, False otherwise
        """
        self._reset_window_if_needed()

        if self._requests == 0:
            return True

        retry_ratio = (self._retries / self._requests) * 100
        return retry_ratio <= self.budget_percent

    def record_request(self):
        """Record a new request."""
        self._reset_window_if_needed()
        self._requests += 1

    def record_retry(self):
        """Record a retry attempt."""
        self._reset_window_if_needed()
        self._retries += 1

    def _reset_window_if_needed(self):
        """Reset counters if window has expired."""
        now = time.time()
        if now - self._window_start >= self.window_seconds:
            self._requests = 0
            self._retries = 0
            self._window_start = now

    def get_stats(self) -> dict:
        """Get current budget statistics."""
        self._reset_window_if_needed()
        return {
            "requests": self._requests,
            "retries": self._retries,
            "retry_ratio": (
                (self._retries / self._requests * 100) if self._requests > 0 else 0.0
            ),
            "budget_remaining": (
                self.budget_percent
                - ((self._retries / self._requests * 100) if self._requests > 0 else 0)
            ),
        }


class RetryContext:
    """
    Context for retry execution.

    Tracks metrics and state across retry attempts.
    """

    def __init__(self, function_name: str, policy: RetryPolicy):
        self.function_name = function_name
        self.policy = policy
        self.attempt = 0
        self.start_time = time.time()
        self.errors: list = []

    def record_attempt(self, error: Optional[Exception] = None):
        """Record a retry attempt."""
        self.attempt += 1
        if error:
            self.errors.append(error)

        if self.policy.on_retry and error:
            try:
                self.policy.on_retry(self.attempt, error)
            except Exception as e:
                logger.warning(f"Error in on_retry callback: {e}")

    def get_metrics(self) -> dict:
        """Get retry metrics."""
        return {
            "function": self.function_name,
            "attempts": self.attempt,
            "duration_seconds": time.time() - self.start_time,
            "errors": [type(e).__name__ for e in self.errors],
        }


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    multiplier: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (),
    budget: Optional[RetryBudget] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Decorator for automatic retry with exponential backoff.

    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        async def call_api():
            return await api.get()

        # With custom exceptions
        @retry_with_backoff(
            max_attempts=5,
            retryable_exceptions=(ConnectionError, TimeoutError),
            non_retryable_exceptions=(ValueError,)
        )
        async def fetch_data():
            return await db.query()

    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Exponential backoff multiplier
        jitter: Add random jitter
        retryable_exceptions: Exceptions to retry
        non_retryable_exceptions: Exceptions to never retry
        budget: Optional RetryBudget to prevent retry storms
        on_retry: Optional callback called on each retry

    Returns:
        Decorated function with retry logic
    """

    policy = RetryPolicy(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        multiplier=multiplier,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
        on_retry=on_retry,
    )

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            context = RetryContext(func.__name__, policy)

            if budget:
                budget.record_request()

            last_error = None

            for attempt in range(max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded for {func.__name__} "
                            f"on attempt {attempt + 1}/{max_attempts}"
                        )
                    return result

                except Exception as e:
                    last_error = e
                    context.record_attempt(e)

                    # Check if retryable
                    if not policy.is_retryable(e):
                        logger.warning(
                            f"Non-retryable error in {func.__name__}: {type(e).__name__}"
                        )
                        raise

                    # Check if we have attempts left
                    if attempt >= max_attempts - 1:
                        logger.error(
                            f"Retry exhausted for {func.__name__} "
                            f"after {max_attempts} attempts. "
                            f"Metrics: {context.get_metrics()}"
                        )
                        raise RetryExhaustedError(max_attempts, e)

                    # Check retry budget
                    if budget and not budget.can_retry():
                        logger.warning(
                            f"Retry budget exhausted for {func.__name__}. "
                            f"Budget stats: {budget.get_stats()}"
                        )
                        raise

                    if budget:
                        budget.record_retry()

                    # Calculate delay and retry
                    delay = policy.calculate_delay(attempt)
                    logger.warning(
                        f"Retrying {func.__name__} after {delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_attempts}). "
                        f"Error: {type(e).__name__}: {e}"
                    )
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            raise RetryExhaustedError(max_attempts, last_error)

        def sync_wrapper(*args, **kwargs):
            """Synchronous wrapper for non-async functions."""
            context = RetryContext(func.__name__, policy)

            if budget:
                budget.record_request()

            last_error = None

            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded for {func.__name__} "
                            f"on attempt {attempt + 1}/{max_attempts}"
                        )
                    return result

                except Exception as e:
                    last_error = e
                    context.record_attempt(e)

                    if not policy.is_retryable(e):
                        logger.warning(
                            f"Non-retryable error in {func.__name__}: {type(e).__name__}"
                        )
                        raise

                    if attempt >= max_attempts - 1:
                        logger.error(
                            f"Retry exhausted for {func.__name__} "
                            f"after {max_attempts} attempts"
                        )
                        raise RetryExhaustedError(max_attempts, e)

                    if budget and not budget.can_retry():
                        logger.warning(
                            f"Retry budget exhausted for {func.__name__}"
                        )
                        raise

                    if budget:
                        budget.record_retry()

                    delay = policy.calculate_delay(attempt)
                    logger.warning(
                        f"Retrying {func.__name__} after {delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_attempts}). "
                        f"Error: {type(e).__name__}: {e}"
                    )
                    time.sleep(delay)

            raise RetryExhaustedError(max_attempts, last_error)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            async_wrapper.__name__ = func.__name__
            async_wrapper.__doc__ = func.__doc__
            return async_wrapper
        else:
            sync_wrapper.__name__ = func.__name__
            sync_wrapper.__doc__ = func.__doc__
            return sync_wrapper

    return decorator
