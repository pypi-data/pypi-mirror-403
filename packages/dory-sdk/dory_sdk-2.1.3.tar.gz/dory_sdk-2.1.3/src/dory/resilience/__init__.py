"""
Resilience patterns for fault-tolerant processing.

This module provides production-ready resilience patterns:
- Retry with exponential backoff
- Circuit breaker pattern
- Rate limiting
- Bulkhead isolation

Example usage:
    from dory.resilience import retry_with_backoff, CircuitBreaker

    @retry_with_backoff(max_attempts=3)
    async def call_api():
        return await api.get()

    breaker = CircuitBreaker(name="database")
    result = await breaker.call(db.query)
"""

from .retry import (
    retry_with_backoff,
    RetryPolicy,
    RetryBudget,
    RetryExhaustedError,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerConfig,
)

__all__ = [
    # Retry
    "retry_with_backoff",
    "RetryPolicy",
    "RetryBudget",
    "RetryExhaustedError",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitOpenError",
    "CircuitBreakerConfig",
]
