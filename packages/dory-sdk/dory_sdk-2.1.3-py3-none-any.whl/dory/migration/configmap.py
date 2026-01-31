"""
ConfigMap storage backend for state persistence.

Uses Kubernetes ConfigMaps to store processor state during migrations.
"""

import logging
import time
from typing import Any

from dory.utils.errors import DoryK8sError, DoryStateError

logger = logging.getLogger(__name__)

# Optional kubernetes import - gracefully handle if not available
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    client = None
    config = None
    ApiException = Exception


class ConfigMapStore:
    """
    Store and retrieve state from Kubernetes ConfigMaps.

    ConfigMap naming convention: dory-state-{processor_id}
    TTL: Auto-cleanup after 1 hour if not claimed.
    """

    STATE_CONFIGMAP_PREFIX = "dory-state-"
    STATE_KEY = "state"
    TTL_ANNOTATION = "dory.io/state-ttl"
    CREATED_ANNOTATION = "dory.io/created-timestamp"
    OWNER_LABEL = "dory.io/state-owner"
    DEFAULT_TTL_SECONDS = 3600  # 1 hour

    def __init__(self, namespace: str | None = None):
        """
        Initialize ConfigMap store.

        Args:
            namespace: Kubernetes namespace (defaults to current pod's namespace)
        """
        self._namespace = namespace
        self._api: Any = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Initialize Kubernetes client if not already done."""
        if self._initialized:
            return

        if not K8S_AVAILABLE:
            raise DoryK8sError(
                "Kubernetes client not available. "
                "Install with: pip install kubernetes"
            )

        try:
            # Try in-cluster config first
            config.load_incluster_config()
            logger.debug("Using in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                # Fall back to kubeconfig
                config.load_kube_config()
                logger.debug("Using kubeconfig")
            except config.ConfigException as e:
                raise DoryK8sError(f"Failed to load Kubernetes config: {e}", cause=e)

        self._api = client.CoreV1Api()

        # Get namespace from pod environment if not specified
        if not self._namespace:
            import os
            self._namespace = os.environ.get("POD_NAMESPACE", "default")

        self._initialized = True

    def _configmap_name(self, processor_id: str) -> str:
        """Generate ConfigMap name for processor."""
        return f"{self.STATE_CONFIGMAP_PREFIX}{processor_id}"

    async def save(
        self,
        processor_id: str,
        state_json: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """
        Save state to ConfigMap.

        Args:
            processor_id: Processor ID
            state_json: JSON-serialized state
            ttl_seconds: TTL for auto-cleanup (default 1 hour)

        Raises:
            DoryK8sError: If ConfigMap operation fails
        """
        self._ensure_initialized()

        cm_name = self._configmap_name(processor_id)
        ttl = ttl_seconds or self.DEFAULT_TTL_SECONDS

        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=cm_name,
                namespace=self._namespace,
                labels={
                    self.OWNER_LABEL: "true",
                },
                annotations={
                    self.TTL_ANNOTATION: str(ttl),
                    self.CREATED_ANNOTATION: time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                    ),
                },
            ),
            data={
                self.STATE_KEY: state_json,
            },
        )

        try:
            # Try to create first
            self._api.create_namespaced_config_map(
                namespace=self._namespace,
                body=configmap,
            )
            logger.debug(f"Created state ConfigMap: {cm_name}")

        except ApiException as e:
            if e.status == 409:
                # Already exists, update it
                try:
                    self._api.replace_namespaced_config_map(
                        name=cm_name,
                        namespace=self._namespace,
                        body=configmap,
                    )
                    logger.debug(f"Updated state ConfigMap: {cm_name}")
                except ApiException as e2:
                    raise DoryK8sError(
                        f"Failed to update ConfigMap {cm_name}: {e2}",
                        cause=e2,
                    )
            else:
                raise DoryK8sError(
                    f"Failed to create ConfigMap {cm_name}: {e}",
                    cause=e,
                )

    async def load(self, processor_id: str) -> str | None:
        """
        Load state from ConfigMap.

        Args:
            processor_id: Processor ID

        Returns:
            JSON-serialized state, or None if not found

        Raises:
            DoryK8sError: If ConfigMap operation fails
        """
        self._ensure_initialized()

        cm_name = self._configmap_name(processor_id)

        try:
            configmap = self._api.read_namespaced_config_map(
                name=cm_name,
                namespace=self._namespace,
            )

            state_json = configmap.data.get(self.STATE_KEY)
            if state_json:
                logger.debug(f"Loaded state from ConfigMap: {cm_name}")
                return state_json
            else:
                logger.warning(f"ConfigMap {cm_name} exists but has no state data")
                return None

        except ApiException as e:
            if e.status == 404:
                logger.debug(f"State ConfigMap not found: {cm_name}")
                return None
            raise DoryK8sError(
                f"Failed to read ConfigMap {cm_name}: {e}",
                cause=e,
            )

    async def delete(self, processor_id: str) -> bool:
        """
        Delete state ConfigMap.

        Args:
            processor_id: Processor ID

        Returns:
            True if deleted, False if not found

        Raises:
            DoryK8sError: If ConfigMap operation fails
        """
        self._ensure_initialized()

        cm_name = self._configmap_name(processor_id)

        try:
            self._api.delete_namespaced_config_map(
                name=cm_name,
                namespace=self._namespace,
            )
            logger.debug(f"Deleted state ConfigMap: {cm_name}")
            return True

        except ApiException as e:
            if e.status == 404:
                logger.debug(f"State ConfigMap not found for deletion: {cm_name}")
                return False
            raise DoryK8sError(
                f"Failed to delete ConfigMap {cm_name}: {e}",
                cause=e,
            )

    async def exists(self, processor_id: str) -> bool:
        """
        Check if state ConfigMap exists.

        Args:
            processor_id: Processor ID

        Returns:
            True if ConfigMap exists
        """
        self._ensure_initialized()

        cm_name = self._configmap_name(processor_id)

        try:
            self._api.read_namespaced_config_map(
                name=cm_name,
                namespace=self._namespace,
            )
            return True

        except ApiException as e:
            if e.status == 404:
                return False
            raise DoryK8sError(
                f"Failed to check ConfigMap {cm_name}: {e}",
                cause=e,
            )
