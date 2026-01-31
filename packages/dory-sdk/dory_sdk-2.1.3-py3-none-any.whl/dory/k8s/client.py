"""
Kubernetes client wrapper.

Provides simplified interface to Kubernetes API.
"""

import logging
from typing import Any

from dory.utils.errors import DoryK8sError

logger = logging.getLogger(__name__)

# Optional kubernetes import
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    client = None
    config = None
    ApiException = Exception


class K8sClient:
    """
    Kubernetes API client wrapper.

    Handles configuration loading and provides
    simplified access to common operations.
    """

    def __init__(self, namespace: str | None = None):
        """
        Initialize Kubernetes client.

        Args:
            namespace: Kubernetes namespace (auto-detected if not provided)
        """
        self._namespace = namespace
        self._core_api: Any = None
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

        self._core_api = client.CoreV1Api()

        # Auto-detect namespace if not provided
        if not self._namespace:
            import os
            self._namespace = os.environ.get("POD_NAMESPACE", "default")

        self._initialized = True

    @property
    def namespace(self) -> str:
        """Get current namespace."""
        self._ensure_initialized()
        return self._namespace

    @property
    def core_api(self):
        """Get CoreV1Api client."""
        self._ensure_initialized()
        return self._core_api

    async def get_pod(self, name: str) -> dict[str, Any]:
        """
        Get pod details.

        Args:
            name: Pod name

        Returns:
            Pod details as dictionary

        Raises:
            DoryK8sError: If operation fails
        """
        self._ensure_initialized()

        try:
            pod = self._core_api.read_namespaced_pod(
                name=name,
                namespace=self._namespace,
            )
            return pod.to_dict()

        except ApiException as e:
            if e.status == 404:
                raise DoryK8sError(f"Pod not found: {name}", cause=e)
            raise DoryK8sError(f"Failed to get pod {name}: {e}", cause=e)

    async def get_pod_annotations(self, name: str) -> dict[str, str]:
        """
        Get pod annotations.

        Args:
            name: Pod name

        Returns:
            Annotations dictionary
        """
        pod = await self.get_pod(name)
        return pod.get("metadata", {}).get("annotations", {})

    async def patch_pod_annotations(
        self,
        name: str,
        annotations: dict[str, str],
    ) -> None:
        """
        Patch pod annotations.

        Args:
            name: Pod name
            annotations: Annotations to add/update
        """
        self._ensure_initialized()

        body = {
            "metadata": {
                "annotations": annotations,
            }
        }

        try:
            self._core_api.patch_namespaced_pod(
                name=name,
                namespace=self._namespace,
                body=body,
            )
            logger.debug(f"Patched annotations on pod {name}")

        except ApiException as e:
            raise DoryK8sError(f"Failed to patch pod {name}: {e}", cause=e)

    async def get_configmap(self, name: str) -> dict[str, str] | None:
        """
        Get ConfigMap data.

        Args:
            name: ConfigMap name

        Returns:
            ConfigMap data, or None if not found
        """
        self._ensure_initialized()

        try:
            cm = self._core_api.read_namespaced_config_map(
                name=name,
                namespace=self._namespace,
            )
            return cm.data or {}

        except ApiException as e:
            if e.status == 404:
                return None
            raise DoryK8sError(f"Failed to get ConfigMap {name}: {e}", cause=e)

    async def create_or_update_configmap(
        self,
        name: str,
        data: dict[str, str],
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Create or update a ConfigMap.

        Args:
            name: ConfigMap name
            data: ConfigMap data
            labels: Optional labels
        """
        self._ensure_initialized()

        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=self._namespace,
                labels=labels,
            ),
            data=data,
        )

        try:
            # Try create first
            self._core_api.create_namespaced_config_map(
                namespace=self._namespace,
                body=configmap,
            )
            logger.debug(f"Created ConfigMap {name}")

        except ApiException as e:
            if e.status == 409:
                # Already exists, update
                self._core_api.replace_namespaced_config_map(
                    name=name,
                    namespace=self._namespace,
                    body=configmap,
                )
                logger.debug(f"Updated ConfigMap {name}")
            else:
                raise DoryK8sError(f"Failed to create ConfigMap {name}: {e}", cause=e)

    async def delete_configmap(self, name: str) -> bool:
        """
        Delete a ConfigMap.

        Args:
            name: ConfigMap name

        Returns:
            True if deleted, False if not found
        """
        self._ensure_initialized()

        try:
            self._core_api.delete_namespaced_config_map(
                name=name,
                namespace=self._namespace,
            )
            return True

        except ApiException as e:
            if e.status == 404:
                return False
            raise DoryK8sError(f"Failed to delete ConfigMap {name}: {e}", cause=e)
