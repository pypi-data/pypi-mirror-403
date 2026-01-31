"""
Tests for circuit breaker pattern.
"""

import asyncio
import pytest
import time

from dory.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerRegistry,
)


@pytest.mark.asyncio
class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""

    async def test_initial_state_closed(self):
        """Test circuit starts in CLOSED state."""
        breaker = CircuitBreaker(name="test")

        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed
        assert not breaker.is_open
        assert not breaker.is_half_open

    async def test_success_in_closed_state(self):
        """Test successful calls in CLOSED state."""
        breaker = CircuitBreaker(name="test")

        async def succeeds():
            return "success"

        result = await breaker.call(succeeds)
        assert result == "success"
        assert breaker.is_closed

    async def test_open_after_threshold_failures(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        async def fails():
            raise ConnectionError("Failure")

        # Fail 3 times
        for i in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

            if i < 2:
                assert breaker.is_closed
            else:
                assert breaker.is_open

    async def test_fail_fast_when_open(self):
        """Test circuit fails fast when OPEN."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)

        async def fails():
            raise ConnectionError("Failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

        assert breaker.is_open

        # Should fail fast without calling function
        call_count = 0

        async def track_calls():
            nonlocal call_count
            call_count += 1
            return "success"

        with pytest.raises(CircuitOpenError):
            await breaker.call(track_calls)

        assert call_count == 0  # Function not called

    async def test_transition_to_half_open(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(
            name="test", failure_threshold=2, timeout_seconds=0.1
        )

        async def fails():
            raise ConnectionError("Failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

        assert breaker.is_open

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Next call should transition to HALF_OPEN
        async def succeeds():
            return "success"

        result = await breaker.call(succeeds)
        assert result == "success"
        assert breaker.is_half_open or breaker.is_closed

    async def test_half_open_to_closed_on_success(self):
        """Test HALF_OPEN transitions to CLOSED after successes."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.1,
        )

        async def fails():
            raise ConnectionError("Failure")

        async def succeeds():
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

        assert breaker.is_open

        # Wait for half-open
        await asyncio.sleep(0.15)

        # First success -> still HALF_OPEN
        await breaker.call(succeeds)
        assert breaker.is_half_open

        # Second success -> CLOSED
        await breaker.call(succeeds)
        assert breaker.is_closed

    async def test_half_open_to_open_on_failure(self):
        """Test HALF_OPEN reopens on any failure."""
        breaker = CircuitBreaker(
            name="test", failure_threshold=2, timeout_seconds=0.1
        )

        async def fails():
            raise ConnectionError("Failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

        assert breaker.is_open

        # Wait for half-open
        await asyncio.sleep(0.15)

        # Failure reopens immediately
        with pytest.raises(ConnectionError):
            await breaker.call(fails)

        assert breaker.is_open

    async def test_limit_concurrent_calls_in_half_open(self):
        """Test concurrent call limit in HALF_OPEN."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            timeout_seconds=0.1,
            half_open_max_calls=1,
        )

        async def fails():
            raise ConnectionError("Failure")

        async def slow_operation():
            await asyncio.sleep(0.2)
            return "success"

        # Open the circuit
        with pytest.raises(ConnectionError):
            await breaker.call(fails)

        # Wait for half-open
        await asyncio.sleep(0.15)

        # Start slow operation
        task1 = asyncio.create_task(breaker.call(slow_operation))

        # Second call should be rejected
        await asyncio.sleep(0.05)  # Let task1 enter
        with pytest.raises(CircuitOpenError):
            await breaker.call(slow_operation)

        # Wait for first task to complete
        await task1

    async def test_sync_function_support(self):
        """Test circuit breaker works with sync functions."""
        breaker = CircuitBreaker(name="test", failure_threshold=2)

        def sync_fails():
            raise ConnectionError("Failure")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(sync_fails)

        assert breaker.is_open

    async def test_manual_reset(self):
        """Test manual circuit reset."""
        breaker = CircuitBreaker(name="test", failure_threshold=1)

        async def fails():
            raise ConnectionError("Failure")

        # Open circuit
        with pytest.raises(ConnectionError):
            await breaker.call(fails)

        assert breaker.is_open

        # Manual reset
        await breaker.reset()
        assert breaker.is_closed

    async def test_manual_open(self):
        """Test manual circuit open."""
        breaker = CircuitBreaker(name="test")

        assert breaker.is_closed

        # Manually open
        await breaker.open()
        assert breaker.is_open

        # Should fail fast
        with pytest.raises(CircuitOpenError):
            await breaker.call(lambda: "success")

    async def test_state_change_callback(self):
        """Test state change callback is called."""
        state_changes = []

        def track_changes(old_state, new_state):
            state_changes.append((old_state, new_state))

        breaker = CircuitBreaker(
            name="test", failure_threshold=2, on_state_change=track_changes
        )

        async def fails():
            raise ConnectionError("Failure")

        # Trigger state change
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

        assert len(state_changes) == 1
        assert state_changes[0] == (CircuitState.CLOSED, CircuitState.OPEN)

    async def test_get_stats(self):
        """Test circuit breaker statistics."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        async def fails():
            raise ConnectionError("Failure")

        # Record failures
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

        stats = breaker.get_stats()
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 2
        assert stats["config"]["failure_threshold"] == 3

    async def test_failure_count_resets_on_success(self):
        """Test failure count resets on success in CLOSED."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        async def fails():
            raise ConnectionError("Failure")

        async def succeeds():
            return "success"

        # Record 2 failures
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(fails)

        assert breaker.get_stats()["failure_count"] == 2

        # Success resets counter
        await breaker.call(succeeds)
        assert breaker.get_stats()["failure_count"] == 0


@pytest.mark.asyncio
class TestCircuitBreakerRegistry:
    """Test CircuitBreakerRegistry."""

    async def test_register_circuit_breaker(self):
        """Test registering circuit breakers."""
        registry = CircuitBreakerRegistry()

        breaker = await registry.register("test", failure_threshold=5)
        assert breaker.config.name == "test"
        assert breaker.config.failure_threshold == 5

    async def test_register_duplicate_returns_existing(self):
        """Test registering duplicate returns existing."""
        registry = CircuitBreakerRegistry()

        breaker1 = await registry.register("test")
        breaker2 = await registry.register("test")

        assert breaker1 is breaker2

    async def test_get_circuit_breaker(self):
        """Test getting circuit breaker by name."""
        registry = CircuitBreakerRegistry()

        await registry.register("test")
        breaker = registry.get("test")

        assert breaker is not None
        assert breaker.config.name == "test"

    async def test_get_nonexistent_returns_none(self):
        """Test getting nonexistent circuit breaker."""
        registry = CircuitBreakerRegistry()

        breaker = registry.get("nonexistent")
        assert breaker is None

    async def test_call_through_registry(self):
        """Test calling function through registry."""
        registry = CircuitBreakerRegistry()
        await registry.register("test", failure_threshold=2)

        async def succeeds():
            return "success"

        result = await registry.call("test", succeeds)
        assert result == "success"

    async def test_call_nonexistent_raises(self):
        """Test calling through nonexistent circuit breaker."""
        registry = CircuitBreakerRegistry()

        async def succeeds():
            return "success"

        with pytest.raises(ValueError, match="not registered"):
            await registry.call("nonexistent", succeeds)

    async def test_get_all_stats(self):
        """Test getting stats for all breakers."""
        registry = CircuitBreakerRegistry()

        await registry.register("test1", failure_threshold=3)
        await registry.register("test2", failure_threshold=5)

        stats = registry.get_all_stats()
        assert "test1" in stats
        assert "test2" in stats
        assert stats["test1"]["config"]["failure_threshold"] == 3
        assert stats["test2"]["config"]["failure_threshold"] == 5

    async def test_reset_all(self):
        """Test resetting all circuit breakers."""
        registry = CircuitBreakerRegistry()

        breaker1 = await registry.register("test1", failure_threshold=1)
        breaker2 = await registry.register("test2", failure_threshold=1)

        async def fails():
            raise ConnectionError("Failure")

        # Open both circuits
        with pytest.raises(ConnectionError):
            await breaker1.call(fails)
        with pytest.raises(ConnectionError):
            await breaker2.call(fails)

        assert breaker1.is_open
        assert breaker2.is_open

        # Reset all
        await registry.reset_all()

        assert breaker1.is_closed
        assert breaker2.is_closed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
