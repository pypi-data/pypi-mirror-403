"""
ExecutionContext - Runtime context passed to processors.

Contains pod metadata, events, and utility methods. The context is
created by DoryApp and passed to the processor constructor.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionContext:
    """
    Execution context containing pod metadata and utilities.

    Attributes:
        pod_name: Kubernetes pod name (e.g., "camera-processor-1")
        pod_namespace: Kubernetes namespace (e.g., "default")
        processor_id: Unique processor ID from Dory DB
        attempt_number: Pod restart count (1, 2, 3...)
        is_migrating: True if this is a restart due to migration
        previous_pod_name: Name of pod we're migrating from (if applicable)
        shutdown_requested: Event that fires when SIGTERM received
        migration_imminent: Event that fires 10s before forced shutdown
    """

    # Pod metadata (read from K8s/env)
    pod_name: str
    pod_namespace: str
    processor_id: str
    attempt_number: int = 1
    is_migrating: bool = False
    previous_pod_name: str | None = None

    # Async events for coordination
    shutdown_requested: asyncio.Event = field(default_factory=asyncio.Event)
    migration_imminent: asyncio.Event = field(default_factory=asyncio.Event)

    # Internal config cache
    _config: dict[str, Any] = field(default_factory=dict)
    _logger: logging.Logger | None = field(default=None, repr=False)

    def is_shutdown_requested(self) -> bool:
        """
        Check if graceful shutdown is in progress.

        Processors should poll this in their run() loop to exit gracefully.

        Returns:
            True if SIGTERM received and shutdown initiated
        """
        return self.shutdown_requested.is_set()

    def is_migration_imminent(self) -> bool:
        """
        Check if migration is about to happen.

        If True, processor should finish in-flight operations quickly.

        Returns:
            True if migration scheduled within next 10s
        """
        return self.migration_imminent.is_set()

    def config(self) -> dict[str, Any]:
        """
        Get application configuration from environment/ConfigMap.

        Only returns app-specific config (CAMERA_FEED_URL, MODEL_PATH, etc.),
        not SDK internals (DORY_* vars are filtered out).

        Returns:
            Dict with app configuration
        """
        return self._config

    def logger(self) -> logging.Logger:
        """
        Get pre-configured logger with pod context.

        Logger automatically includes pod_name, processor_id, namespace
        in all log messages.

        Returns:
            Logger configured with pod context
        """
        if self._logger is None:
            self._logger = logging.getLogger(f"dory.processor.{self.processor_id}")
        return self._logger

    def get_env(self, key: str, default: str | None = None) -> str | None:
        """
        Get environment variable value.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Environment variable value or default
        """
        return os.environ.get(key, default)

    @classmethod
    def from_environment(cls) -> "ExecutionContext":
        """
        Create ExecutionContext from environment variables.

        Reads DORY_* environment variables set by Dory orchestrator.

        Returns:
            ExecutionContext populated from environment
        """
        # Read Dory system env vars
        pod_name = os.environ.get("DORY_POD_NAME", os.environ.get("POD_NAME", "unknown"))
        pod_namespace = os.environ.get(
            "DORY_POD_NAMESPACE", os.environ.get("POD_NAMESPACE", "default")
        )

        # Get processor_id from env or derive from pod name
        processor_id = os.environ.get("DORY_PROCESSOR_ID", os.environ.get("PROCESSOR_ID"))
        if not processor_id:
            # Derive from pod name (e.g., "myapp-7f8d9c6b-x4h2j" -> "myapp")
            processor_id = cls._derive_processor_id_from_pod_name(pod_name)

        is_migrating = os.environ.get("DORY_IS_MIGRATING", "false").lower() == "true"
        previous_pod = os.environ.get("DORY_MIGRATED_FROM")

        # Parse restart count (will be updated from K8s later)
        attempt_number = 1

        # Load app config (non-DORY_ env vars)
        app_config = {}
        for key, value in os.environ.items():
            if not key.startswith("DORY_") and not key.startswith("KUBERNETES_"):
                app_config[key] = value

        return cls(
            pod_name=pod_name,
            pod_namespace=pod_namespace,
            processor_id=processor_id,
            attempt_number=attempt_number,
            is_migrating=is_migrating,
            previous_pod_name=previous_pod,
            _config=app_config,
        )

    @staticmethod
    def _derive_processor_id_from_pod_name(pod_name: str) -> str:
        """
        Derive processor ID from Kubernetes pod name.

        Pod names typically follow the pattern:
        - Deployment: <deployment>-<replicaset-hash>-<pod-hash> (e.g., "myapp-7f8d9c6b-x4h2j")
        - StatefulSet: <statefulset>-<ordinal> (e.g., "myapp-0")

        Args:
            pod_name: Kubernetes pod name

        Returns:
            Derived processor ID or "unknown" if cannot be derived
        """
        if not pod_name or pod_name == "unknown":
            return "unknown"

        parts = pod_name.split("-")
        if len(parts) >= 3:
            # Deployment format: name-replicaset-pod
            # Try to find where the hash parts start (typically 8+ chars of alphanumeric)
            for i in range(len(parts) - 1, 0, -1):
                part = parts[i]
                # If this looks like a hash (short alphanumeric), skip it
                if len(part) <= 10 and part.isalnum():
                    continue
                # Otherwise, include up to this point
                return "-".join(parts[: i + 1])
            # If all parts look like hashes, take the first part
            return parts[0]
        elif len(parts) == 2:
            # StatefulSet format: name-ordinal or simple name-hash
            if parts[1].isdigit():
                return parts[0]  # StatefulSet
            return parts[0]  # Simple deployment
        else:
            return pod_name

    def request_shutdown(self) -> None:
        """Signal that shutdown has been requested."""
        self.shutdown_requested.set()

    def signal_migration(self) -> None:
        """Signal that migration will happen soon."""
        self.migration_imminent.set()

    def signal_migration_imminent(self) -> None:
        """Signal that migration will happen soon (alias for signal_migration)."""
        self.migration_imminent.set()

    def update_config(self, config: dict[str, Any]) -> None:
        """Update app configuration (internal use)."""
        self._config.update(config)

    def set_attempt_number(self, attempt: int) -> None:
        """Set restart attempt number (internal use)."""
        self.attempt_number = attempt
