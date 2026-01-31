"""
StateManager - High-level state management for migrations.

Provides unified interface for state operations across different
storage backends (ConfigMap, PVC, S3, local file).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

from dory.types import StateBackend
from dory.migration.serialization import StateSerializer
from dory.migration.configmap import ConfigMapStore
from dory.utils.errors import DoryStateError

if TYPE_CHECKING:
    from dory.config.schema import DoryConfig

logger = logging.getLogger(__name__)


class StateManager:
    """
    High-level state management for processor migrations.

    Supports multiple backends:
    - ConfigMap: Kubernetes ConfigMap (default, <1MB)
    - PVC: Persistent Volume Claim
    - S3: AWS S3 (for multi-cluster)
    - Local: Local file (for testing)
    """

    LOCAL_STATE_PATH = "/data/dory-state.json"
    LOCAL_STATE_PATH_FALLBACK = "/tmp/dory-state.json"

    def __init__(
        self,
        backend: str | StateBackend = StateBackend.CONFIGMAP,
        config: "DoryConfig | None" = None,
    ):
        """
        Initialize state manager.

        Args:
            backend: Storage backend to use
            config: SDK configuration
        """
        if isinstance(backend, str):
            backend = StateBackend(backend)

        self._backend = backend
        self._config = config
        self._serializer = StateSerializer()
        self._configmap_store: ConfigMapStore | None = None

        # Get namespace from environment
        self._namespace = os.environ.get("POD_NAMESPACE", "default")
        self._pod_name = os.environ.get("POD_NAME", "unknown")

    async def save_state(
        self,
        processor_id: str,
        state: dict[str, Any],
        restart_count: int = 0,
    ) -> None:
        """
        Save processor state.

        Args:
            processor_id: Processor ID
            state: State dictionary to save
            restart_count: Current restart count for metadata

        Raises:
            DoryStateError: If save fails
        """
        logger.debug(f"Saving state for processor {processor_id}")

        # Serialize state
        state_json = self._serializer.serialize(
            state=state,
            processor_id=processor_id,
            pod_name=self._pod_name,
            restart_count=restart_count,
        )

        # Save to backend
        if self._backend == StateBackend.CONFIGMAP:
            await self._save_to_configmap(processor_id, state_json)
        elif self._backend == StateBackend.LOCAL:
            await self._save_to_local(processor_id, state_json)
        elif self._backend == StateBackend.PVC:
            await self._save_to_pvc(processor_id, state_json)
        elif self._backend == StateBackend.S3:
            await self._save_to_s3(processor_id, state_json)
        else:
            raise DoryStateError(f"Unsupported state backend: {self._backend}")

        logger.info(f"State saved for processor {processor_id}")

    async def load_state(self, processor_id: str) -> dict[str, Any] | None:
        """
        Load processor state.

        Args:
            processor_id: Processor ID

        Returns:
            State dictionary, or None if no state found

        Raises:
            DoryStateError: If load fails
        """
        logger.debug(f"Loading state for processor {processor_id}")

        # Load from backend
        state_json: str | None = None

        if self._backend == StateBackend.CONFIGMAP:
            state_json = await self._load_from_configmap(processor_id)
        elif self._backend == StateBackend.LOCAL:
            state_json = await self._load_from_local(processor_id)
        elif self._backend == StateBackend.PVC:
            state_json = await self._load_from_pvc(processor_id)
        elif self._backend == StateBackend.S3:
            state_json = await self._load_from_s3(processor_id)
        else:
            raise DoryStateError(f"Unsupported state backend: {self._backend}")

        if state_json is None:
            logger.debug(f"No state found for processor {processor_id}")
            return None

        # Deserialize state
        state = self._serializer.deserialize(state_json)
        logger.info(f"State loaded for processor {processor_id}")
        return state

    async def delete_state(self, processor_id: str) -> bool:
        """
        Delete processor state (golden image reset).

        Args:
            processor_id: Processor ID

        Returns:
            True if state was deleted

        Raises:
            DoryStateError: If delete fails
        """
        logger.debug(f"Deleting state for processor {processor_id}")

        if self._backend == StateBackend.CONFIGMAP:
            return await self._delete_from_configmap(processor_id)
        elif self._backend == StateBackend.LOCAL:
            return await self._delete_from_local(processor_id)
        elif self._backend == StateBackend.PVC:
            return await self._delete_from_pvc(processor_id)
        elif self._backend == StateBackend.S3:
            return await self._delete_from_s3(processor_id)
        else:
            raise DoryStateError(f"Unsupported state backend: {self._backend}")

    # =========================================================================
    # ConfigMap Backend
    # =========================================================================

    async def _save_to_configmap(self, processor_id: str, state_json: str) -> None:
        """Save state to Kubernetes ConfigMap."""
        if self._configmap_store is None:
            self._configmap_store = ConfigMapStore(namespace=self._namespace)

        await self._configmap_store.save(processor_id, state_json)

    async def _load_from_configmap(self, processor_id: str) -> str | None:
        """Load state from Kubernetes ConfigMap."""
        if self._configmap_store is None:
            self._configmap_store = ConfigMapStore(namespace=self._namespace)

        return await self._configmap_store.load(processor_id)

    async def _delete_from_configmap(self, processor_id: str) -> bool:
        """Delete state ConfigMap."""
        if self._configmap_store is None:
            self._configmap_store = ConfigMapStore(namespace=self._namespace)

        return await self._configmap_store.delete(processor_id)

    # =========================================================================
    # Local File Backend
    # =========================================================================

    def _get_local_path(self, processor_id: str) -> Path:
        """Get local file path for state."""
        # Try /data first, fall back to /tmp
        base_path = Path(self.LOCAL_STATE_PATH).parent
        if not base_path.exists():
            base_path = Path(self.LOCAL_STATE_PATH_FALLBACK).parent

        return base_path / f"dory-state-{processor_id}.json"

    async def _save_to_local(self, processor_id: str, state_json: str) -> None:
        """Save state to local file."""
        path = self._get_local_path(processor_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            path.write_text(state_json)
            logger.debug(f"State saved to local file: {path}")
        except Exception as e:
            raise DoryStateError(f"Failed to save state to {path}: {e}", cause=e)

    async def _load_from_local(self, processor_id: str) -> str | None:
        """Load state from local file."""
        path = self._get_local_path(processor_id)

        if not path.exists():
            return None

        try:
            return path.read_text()
        except Exception as e:
            raise DoryStateError(f"Failed to load state from {path}: {e}", cause=e)

    async def _delete_from_local(self, processor_id: str) -> bool:
        """Delete local state file."""
        path = self._get_local_path(processor_id)

        if not path.exists():
            return False

        try:
            path.unlink()
            logger.debug(f"State file deleted: {path}")
            return True
        except Exception as e:
            raise DoryStateError(f"Failed to delete state file {path}: {e}", cause=e)

    # =========================================================================
    # PVC Backend
    # =========================================================================

    async def _save_to_pvc(self, processor_id: str, state_json: str) -> None:
        """Save state to PVC mount."""
        # PVC uses local file at mounted path
        mount_path = self._config.state_pvc_mount if self._config else "/data"
        path = Path(mount_path) / f"dory-state-{processor_id}.json"

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(state_json)
            logger.debug(f"State saved to PVC: {path}")
        except Exception as e:
            raise DoryStateError(f"Failed to save state to PVC {path}: {e}", cause=e)

    async def _load_from_pvc(self, processor_id: str) -> str | None:
        """Load state from PVC mount."""
        mount_path = self._config.state_pvc_mount if self._config else "/data"
        path = Path(mount_path) / f"dory-state-{processor_id}.json"

        if not path.exists():
            return None

        try:
            return path.read_text()
        except Exception as e:
            raise DoryStateError(f"Failed to load state from PVC {path}: {e}", cause=e)

    async def _delete_from_pvc(self, processor_id: str) -> bool:
        """Delete state from PVC."""
        mount_path = self._config.state_pvc_mount if self._config else "/data"
        path = Path(mount_path) / f"dory-state-{processor_id}.json"

        if not path.exists():
            return False

        try:
            path.unlink()
            return True
        except Exception as e:
            raise DoryStateError(f"Failed to delete state from PVC {path}: {e}", cause=e)

    # =========================================================================
    # S3 Backend (placeholder - would need boto3)
    # =========================================================================

    async def _save_to_s3(self, processor_id: str, state_json: str) -> None:
        """Save state to S3."""
        raise DoryStateError("S3 backend not yet implemented")

    async def _load_from_s3(self, processor_id: str) -> str | None:
        """Load state from S3."""
        raise DoryStateError("S3 backend not yet implemented")

    async def _delete_from_s3(self, processor_id: str) -> bool:
        """Delete state from S3."""
        raise DoryStateError("S3 backend not yet implemented")
