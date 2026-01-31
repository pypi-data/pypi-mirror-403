"""
Type definitions for Dory SDK.

This module contains all type hints and type aliases used across the SDK.
No application-specific types should be defined here.
"""

from typing import TypeVar, Callable, Awaitable, Any, Protocol
from enum import Enum, auto


class LifecycleState(Enum):
    """States in the processor lifecycle state machine."""

    CREATED = auto()       # Instance created, not yet started
    STARTING = auto()      # startup() in progress
    RUNNING = auto()       # run() in progress
    SHUTTING_DOWN = auto() # shutdown() in progress
    STOPPED = auto()       # Gracefully stopped
    FAILED = auto()        # Error occurred


class StateBackend(Enum):
    """Supported state storage backends."""

    CONFIGMAP = "configmap"  # Kubernetes ConfigMap (default, <1MB)
    PVC = "pvc"              # Persistent Volume Claim
    S3 = "s3"                # AWS S3 (for multi-cluster)
    LOCAL = "local"          # Local file (for testing)


class LogFormat(Enum):
    """Log output formats."""

    JSON = "json"   # Structured JSON (default, for production)
    TEXT = "text"   # Human-readable text (for local dev)


class RecoveryStrategy(Enum):
    """Recovery strategies after fault detection."""

    RESTORE_STATE = "restore_state"          # Try to restore from checkpoint
    GOLDEN_IMAGE = "golden_image"            # Start fresh, discard state
    GOLDEN_WITH_BACKOFF = "golden_backoff"   # Start fresh with delay


class FaultType(Enum):
    """Types of faults detected by SDK."""

    CLEAN_EXIT = "clean_exit"           # Normal termination
    UNEXPECTED_CRASH = "crash"          # Exit code non-zero
    HUNG_PROCESS = "hung"               # Liveness probe timeout
    STATE_CORRUPTION = "state_corrupt"  # State validation failed
    STARTUP_FAILURE = "startup_fail"    # Startup threw exception
    HEALTH_CHECK_FAILURE = "health_fail"  # Health endpoint returned error


# Type aliases
StateDict = dict[str, Any]
ConfigDict = dict[str, Any]
MetadataDict = dict[str, str]

# Callback types
ShutdownCallback = Callable[[], Awaitable[None]]
StateCallback = Callable[[], StateDict]


class ProcessorProtocol(Protocol):
    """Protocol defining the processor interface."""

    async def startup(self) -> None: ...
    async def run(self) -> None: ...
    async def shutdown(self) -> None: ...
    def get_state(self) -> StateDict: ...
    async def restore_state(self, state: StateDict) -> None: ...
