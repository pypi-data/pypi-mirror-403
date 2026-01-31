"""
Health probe implementations.

Provides liveness and readiness probes for Kubernetes.
"""

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Union

logger = logging.getLogger(__name__)


@dataclass
class ProbeResult:
    """Result of a health probe check."""
    healthy: bool
    message: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        return {
            "healthy": self.healthy,
            "message": self.message,
            "details": self.details,
        }


class HealthProbe(ABC):
    """Abstract base class for health probes."""

    @abstractmethod
    async def check(self) -> ProbeResult:
        """
        Perform health check.

        Returns:
            ProbeResult indicating health status
        """
        pass


class LivenessProbe(HealthProbe):
    """
    Liveness probe for Kubernetes.

    Indicates whether the process is alive and should not be killed.
    Failed liveness = Kubernetes restarts the pod.

    Should be lightweight and always pass unless process is deadlocked.
    """

    def __init__(self):
        """Initialize liveness probe."""
        self._custom_checks: list[Callable[[], Union[bool, Awaitable[bool]]]] = []

    def add_check(self, check: Callable[[], Union[bool, Awaitable[bool]]]) -> None:
        """
        Add custom liveness check.

        Args:
            check: Sync or async function returning True if healthy
        """
        self._custom_checks.append(check)

    async def check(self) -> ProbeResult:
        """
        Perform liveness check.

        Default implementation always returns healthy.
        Override or add custom checks for specific requirements.
        """
        # Run custom checks
        for i, custom_check in enumerate(self._custom_checks):
            try:
                # Handle both sync and async functions
                if asyncio.iscoroutinefunction(custom_check):
                    result = await custom_check()
                else:
                    result = custom_check()

                if not result:
                    return ProbeResult(
                        healthy=False,
                        message=f"Custom liveness check {i} failed",
                    )
            except Exception as e:
                logger.error(f"Liveness check {i} error: {e}")
                return ProbeResult(
                    healthy=False,
                    message=f"Custom liveness check {i} error: {e}",
                )

        return ProbeResult(healthy=True, message="Process is alive")


class ReadinessProbe(HealthProbe):
    """
    Readiness probe for Kubernetes.

    Indicates whether the process is ready to receive traffic.
    Failed readiness = Kubernetes removes pod from service endpoints.

    Should check that all dependencies are available.
    """

    def __init__(self):
        """Initialize readiness probe."""
        self._ready = False
        self._custom_checks: list[Callable[[], Union[bool, Awaitable[bool]]]] = []

    def mark_ready(self) -> None:
        """Mark the processor as ready to receive traffic."""
        self._ready = True
        logger.info("Processor marked as ready")

    def mark_not_ready(self) -> None:
        """Mark the processor as not ready."""
        self._ready = False
        logger.info("Processor marked as not ready")

    def is_ready(self) -> bool:
        """Check if currently marked as ready."""
        return self._ready

    def add_check(self, check: Callable[[], Union[bool, Awaitable[bool]]]) -> None:
        """
        Add custom readiness check.

        Args:
            check: Sync or async function returning True if ready
        """
        self._custom_checks.append(check)

    async def check(self) -> ProbeResult:
        """
        Perform readiness check.

        Returns not ready until explicitly marked ready.
        Also runs any custom checks.
        """
        if not self._ready:
            return ProbeResult(
                healthy=False,
                message="Processor not yet ready",
            )

        # Run custom checks
        for i, custom_check in enumerate(self._custom_checks):
            try:
                # Handle both sync and async functions
                if asyncio.iscoroutinefunction(custom_check):
                    result = await custom_check()
                else:
                    result = custom_check()

                if not result:
                    return ProbeResult(
                        healthy=False,
                        message=f"Custom readiness check {i} failed",
                    )
            except Exception as e:
                logger.error(f"Readiness check {i} error: {e}")
                return ProbeResult(
                    healthy=False,
                    message=f"Custom readiness check {i} error: {e}",
                )

        return ProbeResult(healthy=True, message="Processor is ready")


class StartupProbe(HealthProbe):
    """
    Startup probe for Kubernetes.

    Indicates whether the application has finished starting up.
    Failed startup = Kubernetes keeps waiting (up to failureThreshold).

    Useful for slow-starting applications.
    """

    def __init__(self, startup_complete_check: Callable[[], bool] | None = None):
        """
        Initialize startup probe.

        Args:
            startup_complete_check: Function returning True when startup is complete
        """
        self._startup_complete = False
        self._startup_check = startup_complete_check

    def mark_startup_complete(self) -> None:
        """Mark startup as complete."""
        self._startup_complete = True
        logger.info("Startup marked as complete")

    async def check(self) -> ProbeResult:
        """Perform startup check."""
        if self._startup_complete:
            return ProbeResult(healthy=True, message="Startup complete")

        if self._startup_check and self._startup_check():
            self._startup_complete = True
            return ProbeResult(healthy=True, message="Startup complete")

        return ProbeResult(healthy=False, message="Still starting up")
