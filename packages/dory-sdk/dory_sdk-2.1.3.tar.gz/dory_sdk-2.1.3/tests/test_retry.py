"""
Tests for retry with exponential backoff.
"""

import asyncio
import pytest
import time
from unittest.mock import MagicMock

from dory.resilience.retry import (
    retry_with_backoff,
    RetryPolicy,
    RetryBudget,
    RetryExhaustedError,
)


class TestRetryPolicy:
    """Test RetryPolicy configuration."""

    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation."""
        policy = RetryPolicy(
            initial_delay=1.0, multiplier=2.0, max_delay=30.0, jitter=False
        )

        assert policy.calculate_delay(0) == 1.0  # 1 * 2^0
        assert policy.calculate_delay(1) == 2.0  # 1 * 2^1
        assert policy.calculate_delay(2) == 4.0  # 1 * 2^2
        assert policy.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_calculate_delay_max_cap(self):
        """Test delay is capped at max_delay."""
        policy = RetryPolicy(
            initial_delay=10.0, multiplier=2.0, max_delay=30.0, jitter=False
        )

        assert policy.calculate_delay(5) == 30.0  # Capped at 30

    def test_calculate_delay_with_jitter(self):
        """Test jitter adds randomness."""
        policy = RetryPolicy(
            initial_delay=10.0, multiplier=2.0, max_delay=100.0, jitter=True
        )

        delays = [policy.calculate_delay(1) for _ in range(100)]

        # Should have variance
        assert len(set(delays)) > 1
        # Should be within bounds (20 +/- 5)
        assert all(15.0 <= d <= 25.0 for d in delays)

    def test_is_retryable_default(self):
        """Test default retryable behavior."""
        policy = RetryPolicy()

        assert policy.is_retryable(ConnectionError())
        assert policy.is_retryable(TimeoutError())
        assert policy.is_retryable(ValueError())

    def test_is_retryable_custom_exceptions(self):
        """Test custom retryable exceptions."""
        policy = RetryPolicy(
            retryable_exceptions=(ConnectionError, TimeoutError),
            non_retryable_exceptions=(ValueError,),
        )

        assert policy.is_retryable(ConnectionError())
        assert policy.is_retryable(TimeoutError())
        assert not policy.is_retryable(ValueError())
        assert not policy.is_retryable(TypeError())

    def test_non_retryable_takes_precedence(self):
        """Test non-retryable exceptions take precedence."""
        policy = RetryPolicy(
            retryable_exceptions=(Exception,), non_retryable_exceptions=(ValueError,)
        )

        # ValueError is in Exception, but marked non-retryable
        assert not policy.is_retryable(ValueError())


class TestRetryBudget:
    """Test RetryBudget for preventing retry storms."""

    def test_initial_budget_allows_retry(self):
        """Test initial state allows retry."""
        budget = RetryBudget(budget_percent=20.0, window_seconds=60.0)

        assert budget.can_retry()

    def test_budget_limit_enforced(self):
        """Test retry budget limit is enforced."""
        budget = RetryBudget(budget_percent=20.0, window_seconds=60.0)

        # Record requests and retries
        for _ in range(10):
            budget.record_request()

        # First retry is allowed (0/10 = 0%)
        budget.record_retry()
        assert budget.can_retry()  # 1/10 = 10% < 20%

        # Second retry is allowed
        budget.record_retry()
        assert budget.can_retry()  # 2/10 = 20% = 20%

        # Third retry exceeds budget
        budget.record_retry()
        assert not budget.can_retry()  # 3/10 = 30% > 20%

    def test_budget_resets_after_window(self):
        """Test budget resets after time window."""
        budget = RetryBudget(budget_percent=20.0, window_seconds=0.1)

        # Exhaust budget
        for _ in range(10):
            budget.record_request()
        for _ in range(3):
            budget.record_retry()

        assert not budget.can_retry()

        # Wait for window to expire
        time.sleep(0.2)

        # Budget should reset
        assert budget.can_retry()

    def test_get_stats(self):
        """Test budget statistics."""
        budget = RetryBudget(budget_percent=25.0, window_seconds=60.0)

        for _ in range(10):
            budget.record_request()
        for _ in range(2):
            budget.record_retry()

        stats = budget.get_stats()
        assert stats["requests"] == 10
        assert stats["retries"] == 2
        assert stats["retry_ratio"] == 20.0  # 2/10 * 100
        assert stats["budget_remaining"] == 5.0  # 25 - 20


@pytest.mark.asyncio
class TestRetryWithBackoff:
    """Test retry_with_backoff decorator."""

    async def test_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def succeeds_immediately():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await succeeds_immediately()
        assert result == "success"
        assert call_count == 1

    async def test_success_on_nth_attempt(self):
        """Test successful execution after retries."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        async def succeeds_on_third():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await succeeds_on_third()
        assert result == "success"
        assert call_count == 3

    async def test_exhaust_max_attempts(self):
        """Test retry exhaustion."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await always_fails()

        assert call_count == 3
        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_error, ConnectionError)

    async def test_non_retryable_exception(self):
        """Test non-retryable exceptions fail immediately."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            retryable_exceptions=(ConnectionError,),
            non_retryable_exceptions=(ValueError,),
        )
        async def fails_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable")

        with pytest.raises(ValueError):
            await fails_with_value_error()

        # Should not retry
        assert call_count == 1

    async def test_exponential_backoff_timing(self):
        """Test exponential backoff delays."""
        delays = []
        last_time = time.time()
        first_call = True

        @retry_with_backoff(
            max_attempts=4, initial_delay=0.1, multiplier=2.0, jitter=False
        )
        async def track_delays():
            nonlocal last_time, first_call
            current_time = time.time()
            if not first_call:  # Not the first call, record delay
                delays.append(current_time - last_time)
            first_call = False  # Mark that we've had the first call
            last_time = current_time
            if len(delays) < 3:
                raise ConnectionError("Retry")
            return "done"

        await track_delays()

        # Expected delays: ~0.1, ~0.2, ~0.4
        assert len(delays) == 3
        assert 0.08 <= delays[0] <= 0.15  # ~0.1s
        assert 0.18 <= delays[1] <= 0.25  # ~0.2s
        assert 0.38 <= delays[2] <= 0.45  # ~0.4s

    async def test_retry_budget_enforcement(self):
        """Test retry budget prevents retry storms."""
        budget = RetryBudget(budget_percent=10.0, window_seconds=60.0)

        # Fill budget (10 requests, 2 retries = 20% > 10%)
        for _ in range(10):
            budget.record_request()
        budget.record_retry()

        @retry_with_backoff(max_attempts=3, budget=budget, initial_delay=0.01)
        async def will_be_limited():
            raise ConnectionError("Fail")

        # Budget allows first retry
        with pytest.raises(ConnectionError):
            await will_be_limited()

    async def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_attempts = []

        def track_retries(attempt, error):
            retry_attempts.append((attempt, type(error).__name__))

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, on_retry=track_retries
        )
        async def fails_twice():
            if len(retry_attempts) < 2:
                raise ConnectionError("Retry me")
            return "success"

        result = await fails_twice()
        assert result == "success"
        assert len(retry_attempts) == 2
        assert retry_attempts[0] == (1, "ConnectionError")
        assert retry_attempts[1] == (2, "ConnectionError")

    async def test_sync_function_retry(self):
        """Test retry works with synchronous functions."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def sync_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Retry")
            return "success"

        result = sync_function()
        assert result == "success"
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
