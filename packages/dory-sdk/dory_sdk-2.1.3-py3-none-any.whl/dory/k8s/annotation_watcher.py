"""
Annotation watcher for migration signals.

Watches pod annotations for migration-related signals
from the orchestrator.
"""

import asyncio
import logging
from typing import Callable, Any

from dory.k8s.client import K8sClient
from dory.utils.errors import DoryK8sError

logger = logging.getLogger(__name__)


class AnnotationWatcher:
    """
    Watches pod annotations for orchestrator signals.

    Monitors annotations:
    - dory.io/migration: "true" when migration imminent
    - dory.io/shutdown: "true" when shutdown requested
    - dory.io/snapshot: "true" when snapshot requested
    """

    MIGRATION_ANNOTATION = "dory.io/migration"
    SHUTDOWN_ANNOTATION = "dory.io/shutdown"
    SNAPSHOT_ANNOTATION = "dory.io/snapshot"
    DEADLINE_ANNOTATION = "dory.io/migration-deadline"

    def __init__(
        self,
        k8s_client: K8sClient,
        pod_name: str,
        poll_interval: float = 5.0,
    ):
        """
        Initialize annotation watcher.

        Args:
            k8s_client: Kubernetes client
            pod_name: Name of pod to watch
            poll_interval: Seconds between polls
        """
        self._k8s_client = k8s_client
        self._pod_name = pod_name
        self._poll_interval = poll_interval

        self._running = False
        self._watch_task: asyncio.Task | None = None

        # Callbacks
        self._on_migration: Callable[[], Any] | None = None
        self._on_shutdown: Callable[[], Any] | None = None
        self._on_snapshot: Callable[[], Any] | None = None

        # State tracking
        self._last_annotations: dict[str, str] = {}

    def on_migration(self, callback: Callable[[], Any]) -> None:
        """Set callback for migration signal."""
        self._on_migration = callback

    def on_shutdown(self, callback: Callable[[], Any]) -> None:
        """Set callback for shutdown signal."""
        self._on_shutdown = callback

    def on_snapshot(self, callback: Callable[[], Any]) -> None:
        """Set callback for snapshot signal."""
        self._on_snapshot = callback

    async def start(self) -> None:
        """Start watching annotations."""
        if self._running:
            return

        self._running = True
        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info(f"Started annotation watcher for pod {self._pod_name}")

    async def stop(self) -> None:
        """Stop watching annotations."""
        self._running = False

        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None

        logger.info("Annotation watcher stopped")

    async def _watch_loop(self) -> None:
        """Main watch loop."""
        while self._running:
            try:
                await self._check_annotations()
            except DoryK8sError as e:
                logger.warning(f"Failed to check annotations: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in annotation watcher: {e}")

            await asyncio.sleep(self._poll_interval)

    async def _check_annotations(self) -> None:
        """Check annotations for changes."""
        try:
            annotations = await self._k8s_client.get_pod_annotations(self._pod_name)
        except DoryK8sError:
            # Pod might not exist yet or API unavailable
            return

        # Check migration annotation
        if self._annotation_changed(self.MIGRATION_ANNOTATION, annotations, "true"):
            logger.info("Migration signal detected")
            if self._on_migration:
                await self._invoke_callback(self._on_migration)

        # Check shutdown annotation
        if self._annotation_changed(self.SHUTDOWN_ANNOTATION, annotations, "true"):
            logger.info("Shutdown signal detected")
            if self._on_shutdown:
                await self._invoke_callback(self._on_shutdown)

        # Check snapshot annotation
        if self._annotation_changed(self.SNAPSHOT_ANNOTATION, annotations, "true"):
            logger.info("Snapshot signal detected")
            if self._on_snapshot:
                await self._invoke_callback(self._on_snapshot)
            # Clear snapshot annotation after processing
            await self._clear_annotation(self.SNAPSHOT_ANNOTATION)

        self._last_annotations = annotations

    def _annotation_changed(
        self,
        key: str,
        new_annotations: dict[str, str],
        trigger_value: str,
    ) -> bool:
        """Check if annotation changed to trigger value."""
        old_value = self._last_annotations.get(key)
        new_value = new_annotations.get(key)

        return old_value != new_value and new_value == trigger_value

    async def _invoke_callback(self, callback: Callable[[], Any]) -> None:
        """Invoke callback, handling async/sync."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        except Exception as e:
            logger.error(f"Callback error: {e}")

    async def _clear_annotation(self, key: str) -> None:
        """Clear an annotation after processing."""
        try:
            await self._k8s_client.patch_pod_annotations(
                self._pod_name,
                {key: None},  # Setting to None removes the annotation
            )
        except DoryK8sError as e:
            logger.warning(f"Failed to clear annotation {key}: {e}")

    def get_migration_deadline(self) -> float | None:
        """
        Get migration deadline from annotations.

        Returns:
            Unix timestamp of deadline, or None
        """
        deadline_str = self._last_annotations.get(self.DEADLINE_ANNOTATION)
        if deadline_str:
            try:
                return float(deadline_str)
            except ValueError:
                pass
        return None
