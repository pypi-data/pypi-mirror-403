"""
Circuit breaker pattern implementation.

Prevents cascading failures by stopping requests to failing dependencies.

States:
- CLOSED: Normal operation, requests go through
- OPEN: Too many failures, requests fail fast
- HALF_OPEN: Testing if dependency recovered

Usage:
    breaker = CircuitBreaker(name="database", failure_threshold=5)

    try:
        result = await breaker.call(db.query, args)
    except CircuitOpenError:
        # Circuit is open, fail fast
        result = get_cached_data()
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, next_attempt_time: float):
        self.circuit_name = circuit_name
        self.next_attempt_time = next_attempt_time
        seconds_until = max(0, next_attempt_time - time.time())
        super().__init__(
            f"Circuit '{circuit_name}' is OPEN. "
            f"Next attempt in {seconds_until:.1f}s"
        )


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for circuit breaker behavior.

    Attributes:
        name: Circuit breaker name for identification
        failure_threshold: Number of failures before opening (default: 5)
        success_threshold: Successes needed in half-open to close (default: 2)
        timeout_seconds: Seconds to wait before half-open (default: 60)
        half_open_max_calls: Max concurrent calls in half-open (default: 1)
        on_state_change: Callback for state transitions
    """

    name: str
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 1
    on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None


class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.

    Tracks failures and successes to determine when to open/close the circuit.
    When open, requests fail fast without executing.

    Example:
        breaker = CircuitBreaker(name="api", failure_threshold=5)

        async def call_api():
            return await breaker.call(api.get, "/users")

        # With error handling
        try:
            result = await breaker.call(risky_operation)
        except CircuitOpenError as e:
            logger.warning(f"Circuit open: {e}")
            result = get_fallback_data()
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
        half_open_max_calls: int = 1,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique name for this circuit breaker
            failure_threshold: Failures before opening circuit
            success_threshold: Successes in half-open to close
            timeout_seconds: Wait time before trying half-open
            half_open_max_calls: Max concurrent calls in half-open
            on_state_change: Optional callback for state changes
        """
        self.config = CircuitBreakerConfig(
            name=name,
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_seconds=timeout_seconds,
            half_open_max_calls=half_open_max_calls,
            on_state_change=on_state_change,
        )

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, "
            f"timeout={timeout_seconds}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self._state == CircuitState.HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute (can be sync or async)
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from the function
        """
        async with self._lock:
            await self._check_state_transition()

            # Fail fast if circuit is open
            if self._state == CircuitState.OPEN:
                next_attempt = (
                    self._last_failure_time + self.config.timeout_seconds
                    if self._last_failure_time
                    else time.time()
                )
                raise CircuitOpenError(self.config.name, next_attempt)

            # Limit concurrent calls in half-open
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitOpenError(
                        self.config.name,
                        time.time() + self.config.timeout_seconds,
                    )
                self._half_open_calls += 1

        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure(e)
            raise

        finally:
            if self._state == CircuitState.HALF_OPEN:
                async with self._lock:
                    self._half_open_calls -= 1

    async def _check_state_transition(self):
        """Check if circuit should transition to half-open."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            time_since_failure = time.time() - self._last_failure_time

            if time_since_failure >= self.config.timeout_seconds:
                logger.info(
                    f"Circuit '{self.config.name}' transitioning OPEN -> HALF_OPEN "
                    f"after {time_since_failure:.1f}s timeout"
                )
                await self._transition_to(CircuitState.HALF_OPEN)

    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"Circuit '{self.config.name}' success in HALF_OPEN: "
                    f"{self._success_count}/{self.config.success_threshold}"
                )

                if self._success_count >= self.config.success_threshold:
                    logger.info(
                        f"Circuit '{self.config.name}' transitioning HALF_OPEN -> CLOSED "
                        f"after {self._success_count} successes"
                    )
                    await self._transition_to(CircuitState.CLOSED)

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                if self._failure_count > 0:
                    self._failure_count = 0

    async def _on_failure(self, error: Exception):
        """Handle failed execution."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            logger.warning(
                f"Circuit '{self.config.name}' failure #{self._failure_count}: "
                f"{type(error).__name__}: {error}"
            )

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens the circuit
                logger.warning(
                    f"Circuit '{self.config.name}' transitioning HALF_OPEN -> OPEN "
                    f"due to failure"
                )
                await self._transition_to(CircuitState.OPEN)

            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self.config.failure_threshold
            ):
                logger.error(
                    f"Circuit '{self.config.name}' transitioning CLOSED -> OPEN "
                    f"after {self._failure_count} failures"
                )
                await self._transition_to(CircuitState.OPEN)

    async def _transition_to(self, new_state: CircuitState):
        """
        Transition to new circuit state.

        Args:
            new_state: Target state
        """
        old_state = self._state
        self._state = new_state

        # Reset counters based on new state
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.OPEN:
            self._success_count = 0

        # Call state change callback
        if self.config.on_state_change:
            try:
                self.config.on_state_change(old_state, new_state)
            except Exception as e:
                logger.warning(f"Error in on_state_change callback: {e}")

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with current stats
        """
        return {
            "name": self.config.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "half_open_calls": self._half_open_calls,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }

    async def reset(self):
        """
        Manually reset circuit breaker to CLOSED state.

        Use with caution - typically for admin/testing purposes only.
        """
        async with self._lock:
            logger.warning(
                f"Circuit '{self.config.name}' manually reset to CLOSED "
                f"from {self._state.value}"
            )
            await self._transition_to(CircuitState.CLOSED)

    async def open(self):
        """
        Manually open circuit breaker.

        Use for planned maintenance or testing.
        """
        async with self._lock:
            logger.warning(
                f"Circuit '{self.config.name}' manually opened "
                f"from {self._state.value}"
            )
            await self._transition_to(CircuitState.OPEN)
            self._last_failure_time = time.time()


class CircuitBreakerRegistry:
    """
    Global registry for circuit breakers.

    Allows managing multiple circuit breakers from a central location.

    Example:
        registry = CircuitBreakerRegistry()
        registry.register("database", failure_threshold=5)
        registry.register("api", failure_threshold=3)

        # Use circuit breakers
        result = await registry.call("database", db.query, sql)

        # Get stats
        stats = registry.get_all_stats()
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def register(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
        **kwargs,
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.

        Args:
            name: Unique circuit breaker name
            failure_threshold: Failures before opening
            success_threshold: Successes to close
            timeout_seconds: Timeout before half-open
            **kwargs: Additional CircuitBreaker arguments

        Returns:
            Registered CircuitBreaker instance
        """
        async with self._lock:
            if name in self._breakers:
                logger.warning(
                    f"Circuit breaker '{name}' already registered, returning existing"
                )
                return self._breakers[name]

            breaker = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds,
                **kwargs,
            )
            self._breakers[name] = breaker
            return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)

    async def call(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through named circuit breaker.

        Args:
            name: Circuit breaker name
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            ValueError: If circuit breaker not found
        """
        breaker = self.get(name)
        if not breaker:
            raise ValueError(f"Circuit breaker '{name}' not registered")

        return await breaker.call(func, *args, **kwargs)

    def get_all_stats(self) -> dict:
        """Get stats for all registered circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    async def reset_all(self):
        """Reset all circuit breakers to CLOSED state."""
        for breaker in self._breakers.values():
            await breaker.reset()


# Global registry instance
_global_registry = CircuitBreakerRegistry()


def get_global_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    return _global_registry
