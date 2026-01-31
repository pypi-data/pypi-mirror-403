"""
Pod metadata extraction from Kubernetes environment.

Retrieves pod information from:
1. Downward API environment variables
2. Kubernetes API
3. /etc/podinfo files
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PodMetadata:
    """
    Pod metadata extracted from environment.

    Populated from:
    - Environment variables (POD_NAME, POD_NAMESPACE, etc.)
    - Downward API files (/etc/podinfo/)
    - Kubernetes API (if available)
    """

    # Core identification
    name: str = ""
    namespace: str = "default"
    uid: str = ""

    # Node information
    node_name: str = ""
    service_account: str = ""

    # Labels and annotations
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    # Resource info
    cpu_request: str = ""
    cpu_limit: str = ""
    memory_request: str = ""
    memory_limit: str = ""

    # Container info
    container_name: str = ""
    image: str = ""

    @classmethod
    def from_environment(cls) -> "PodMetadata":
        """
        Create PodMetadata from environment.

        Reads from environment variables and downward API files.
        """
        metadata = cls()

        # Read from environment variables
        metadata.name = os.environ.get("POD_NAME", "")
        metadata.namespace = os.environ.get("POD_NAMESPACE", "default")
        metadata.uid = os.environ.get("POD_UID", "")
        metadata.node_name = os.environ.get("NODE_NAME", "")
        metadata.service_account = os.environ.get("SERVICE_ACCOUNT", "")
        metadata.container_name = os.environ.get("CONTAINER_NAME", "")

        # Try reading from downward API files
        metadata._read_downward_api_files()

        # Parse labels/annotations from environment
        metadata._parse_labels_from_env()

        logger.debug(f"Pod metadata: {metadata}")
        return metadata

    def _read_downward_api_files(self) -> None:
        """Read metadata from downward API volume mounts."""
        podinfo_path = Path("/etc/podinfo")

        if not podinfo_path.exists():
            return

        # Read labels file
        labels_file = podinfo_path / "labels"
        if labels_file.exists():
            self.labels = self._parse_labels_file(labels_file)

        # Read annotations file
        annotations_file = podinfo_path / "annotations"
        if annotations_file.exists():
            self.annotations = self._parse_labels_file(annotations_file)

        # Read individual files
        for attr, filename in [
            ("name", "name"),
            ("namespace", "namespace"),
            ("uid", "uid"),
            ("node_name", "nodeName"),
        ]:
            file_path = podinfo_path / filename
            if file_path.exists():
                try:
                    value = file_path.read_text().strip()
                    if value:
                        setattr(self, attr, value)
                except IOError:
                    pass

    def _parse_labels_file(self, path: Path) -> dict[str, str]:
        """
        Parse labels/annotations file.

        Format: key="value"
        """
        result = {}
        try:
            content = path.read_text()
            for line in content.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes
                    value = value.strip('"')
                    result[key] = value
        except IOError:
            pass
        return result

    def _parse_labels_from_env(self) -> None:
        """Parse labels from POD_LABELS environment variable."""
        labels_env = os.environ.get("POD_LABELS", "")
        if labels_env:
            # Format: key1=value1,key2=value2
            for pair in labels_env.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    self.labels[key] = value

    def get_processor_id(self) -> str:
        """
        Get processor ID from metadata.

        Uses label if present, otherwise pod name.
        """
        # Try label first
        processor_id = self.labels.get("dory.io/processor-id")
        if processor_id:
            return processor_id

        # Fall back to pod name with suffix stripped
        name = self.name
        if name:
            # Strip deployment suffix (e.g., myapp-7f8d9c6b-x4h2j -> myapp)
            parts = name.rsplit("-", 2)
            if len(parts) >= 2:
                return parts[0]

        return name or "unknown"

    def is_migration(self) -> bool:
        """Check if this is a migration restart."""
        return self.annotations.get("dory.io/migration") == "true"

    def get_previous_pod(self) -> str | None:
        """Get previous pod name if this is a migration."""
        return self.annotations.get("dory.io/previous-pod")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "namespace": self.namespace,
            "uid": self.uid,
            "node_name": self.node_name,
            "service_account": self.service_account,
            "labels": self.labels,
            "annotations": self.annotations,
            "container_name": self.container_name,
            "processor_id": self.get_processor_id(),
        }
