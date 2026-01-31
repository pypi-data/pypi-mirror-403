"""
Golden Snapshot Manager

Captures and manages golden snapshots of processor state to prevent
100% data loss during resets. Implements:
- Snapshot capture with checksums
- Versioned snapshot storage
- Snapshot validation
- Restoration from snapshots
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable
import gzip

logger = logging.getLogger(__name__)


class SnapshotStorageError(Exception):
    """Raised when snapshot storage operations fail."""
    pass


class SnapshotValidationError(Exception):
    """Raised when snapshot validation fails."""
    pass


class SnapshotFormat(Enum):
    """Snapshot storage format."""
    JSON = "json"
    JSON_GZ = "json.gz"  # Compressed JSON
    BINARY = "binary"


@dataclass
class SnapshotMetadata:
    """
    Metadata about a golden snapshot.

    Includes version, timestamps, checksums, and size information.
    """
    snapshot_id: str
    processor_id: str
    created_at: float
    state_version: str
    checksum: str
    size_bytes: int
    compressed: bool = False
    format: str = "json"
    validation_passed: bool = True
    restore_count: int = 0
    last_restored_at: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotMetadata":
        """Create from dictionary."""
        return cls(**data)

    def age_seconds(self) -> float:
        """Get age of snapshot in seconds."""
        return time.time() - self.created_at


@dataclass
class Snapshot:
    """
    Complete snapshot including metadata and state data.
    """
    metadata: SnapshotMetadata
    state_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "state_data": self.state_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """Create from dictionary."""
        return cls(
            metadata=SnapshotMetadata.from_dict(data["metadata"]),
            state_data=data["state_data"]
        )


class GoldenSnapshotManager:
    """
    Manages golden snapshots of processor state.

    Features:
    - Automatic snapshot capture at key points
    - Checksum validation
    - Multiple snapshot versions
    - Compression support
    - Restore with validation
    - Snapshot lifecycle management

    Usage:
        manager = GoldenSnapshotManager(storage_path="./snapshots")

        # Capture snapshot
        snapshot = await manager.capture_snapshot(
            processor_id="my-processor",
            state_data={"key": "value"},
            tags={"version": "1.0"}
        )

        # List snapshots
        snapshots = await manager.list_snapshots(processor_id="my-processor")

        # Restore from snapshot
        state = await manager.restore_snapshot(snapshot.metadata.snapshot_id)
    """

    def __init__(
        self,
        storage_path: str = "./golden_snapshots",
        max_snapshots_per_processor: int = 5,
        compression_enabled: bool = True,
        checksum_algorithm: str = "sha256",
        auto_cleanup: bool = True,
        on_capture: Optional[Callable] = None,
        on_restore: Optional[Callable] = None,
    ):
        """
        Initialize golden snapshot manager.

        Args:
            storage_path: Directory to store snapshots
            max_snapshots_per_processor: Maximum snapshots per processor
            compression_enabled: Whether to compress snapshots
            checksum_algorithm: Algorithm for checksums (sha256, md5)
            auto_cleanup: Automatically cleanup old snapshots
            on_capture: Callback when snapshot is captured
            on_restore: Callback when snapshot is restored
        """
        self.storage_path = Path(storage_path)
        self.max_snapshots_per_processor = max_snapshots_per_processor
        self.compression_enabled = compression_enabled
        self.checksum_algorithm = checksum_algorithm
        self.auto_cleanup = auto_cleanup
        self.on_capture = on_capture
        self.on_restore = on_restore

        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Metrics
        self._capture_count = 0
        self._restore_count = 0
        self._validation_failures = 0

        logger.info(
            f"GoldenSnapshotManager initialized: storage={storage_path}, "
            f"compression={compression_enabled}, max_per_processor={max_snapshots_per_processor}"
        )

    async def capture_snapshot(
        self,
        processor_id: str,
        state_data: Dict[str, Any],
        state_version: str = "1.0",
        tags: Optional[Dict[str, str]] = None,
        validate_before_save: bool = True,
    ) -> Snapshot:
        """
        Capture a golden snapshot of processor state.

        Args:
            processor_id: ID of processor
            state_data: State data to snapshot
            state_version: Version of state schema
            tags: Optional tags for the snapshot
            validate_before_save: Validate state before saving

        Returns:
            Captured snapshot with metadata

        Raises:
            SnapshotValidationError: If validation fails
            SnapshotStorageError: If storage fails
        """
        logger.info(f"Capturing snapshot for processor {processor_id}")

        # Validate state data
        if validate_before_save:
            if not self._validate_state_data(state_data):
                raise SnapshotValidationError("State data validation failed")

        # Generate snapshot ID
        snapshot_id = self._generate_snapshot_id(processor_id)

        # Serialize state data
        state_json = json.dumps(state_data, sort_keys=True)

        # Compress if enabled
        if self.compression_enabled:
            state_bytes = gzip.compress(state_json.encode())
            compressed = True
            format_type = SnapshotFormat.JSON_GZ.value
        else:
            state_bytes = state_json.encode()
            compressed = False
            format_type = SnapshotFormat.JSON.value

        # Calculate checksum
        checksum = self._calculate_checksum(state_bytes)

        # Create metadata
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            processor_id=processor_id,
            created_at=time.time(),
            state_version=state_version,
            checksum=checksum,
            size_bytes=len(state_bytes),
            compressed=compressed,
            format=format_type,
            tags=tags or {},
        )

        # Create snapshot
        snapshot = Snapshot(metadata=metadata, state_data=state_data)

        # Save to storage
        try:
            await self._save_snapshot(snapshot, state_bytes)
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise SnapshotStorageError(f"Failed to save snapshot: {e}")

        # Update metrics
        self._capture_count += 1

        # Cleanup old snapshots if auto_cleanup enabled
        if self.auto_cleanup:
            await self._cleanup_old_snapshots(processor_id)

        # Call capture callback
        if self.on_capture:
            try:
                if asyncio.iscoroutinefunction(self.on_capture):
                    await self.on_capture(snapshot)
                else:
                    self.on_capture(snapshot)
            except Exception as e:
                logger.warning(f"Capture callback failed: {e}")

        logger.info(
            f"Snapshot captured: id={snapshot_id}, size={len(state_bytes)} bytes, "
            f"compressed={compressed}, checksum={checksum[:8]}..."
        )

        return snapshot

    async def restore_snapshot(
        self,
        snapshot_id: str,
        validate_checksum: bool = True,
        update_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Restore state from a snapshot.

        Args:
            snapshot_id: ID of snapshot to restore
            validate_checksum: Validate checksum before restoring
            update_metadata: Update metadata (restore count, timestamp)

        Returns:
            Restored state data

        Raises:
            SnapshotValidationError: If validation fails
            SnapshotStorageError: If snapshot not found or load fails
        """
        logger.info(f"Restoring snapshot {snapshot_id}")

        # Load snapshot
        try:
            snapshot, state_bytes = await self._load_snapshot(snapshot_id)
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            raise SnapshotStorageError(f"Failed to load snapshot: {e}")

        # Validate checksum
        if validate_checksum:
            calculated_checksum = self._calculate_checksum(state_bytes)
            if calculated_checksum != snapshot.metadata.checksum:
                self._validation_failures += 1
                raise SnapshotValidationError(
                    f"Checksum mismatch: expected {snapshot.metadata.checksum}, "
                    f"got {calculated_checksum}"
                )

        # Update metadata
        if update_metadata:
            snapshot.metadata.restore_count += 1
            snapshot.metadata.last_restored_at = time.time()
            await self._update_metadata(snapshot.metadata)

        # Update metrics
        self._restore_count += 1

        # Call restore callback
        if self.on_restore:
            try:
                if asyncio.iscoroutinefunction(self.on_restore):
                    await self.on_restore(snapshot)
                else:
                    self.on_restore(snapshot)
            except Exception as e:
                logger.warning(f"Restore callback failed: {e}")

        logger.info(
            f"Snapshot restored: id={snapshot_id}, "
            f"restore_count={snapshot.metadata.restore_count}"
        )

        return snapshot.state_data

    async def list_snapshots(
        self,
        processor_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[SnapshotMetadata]:
        """
        List available snapshots.

        Args:
            processor_id: Filter by processor ID (None for all)
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot metadata, sorted by created_at (newest first)
        """
        snapshots = []

        # Iterate through storage directory
        for meta_file in self.storage_path.glob("*.meta.json"):
            try:
                with open(meta_file, "r") as f:
                    meta_data = json.load(f)
                    metadata = SnapshotMetadata.from_dict(meta_data)

                    # Filter by processor_id if specified
                    if processor_id is None or metadata.processor_id == processor_id:
                        snapshots.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to load metadata from {meta_file}: {e}")

        # Sort by created_at (newest first)
        snapshots.sort(key=lambda x: x.created_at, reverse=True)

        # Apply limit
        if limit is not None:
            snapshots = snapshots[:limit]

        return snapshots

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.

        Args:
            snapshot_id: ID of snapshot to delete

        Returns:
            True if deleted successfully
        """
        logger.info(f"Deleting snapshot {snapshot_id}")

        try:
            # Delete data file
            data_file = self.storage_path / f"{snapshot_id}.data"
            if data_file.exists():
                data_file.unlink()

            # Delete metadata file
            meta_file = self.storage_path / f"{snapshot_id}.meta.json"
            if meta_file.exists():
                meta_file.unlink()

            logger.info(f"Snapshot deleted: {snapshot_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
            return False

    async def get_latest_snapshot(
        self,
        processor_id: str
    ) -> Optional[SnapshotMetadata]:
        """
        Get the latest snapshot for a processor.

        Args:
            processor_id: Processor ID

        Returns:
            Latest snapshot metadata, or None if no snapshots exist
        """
        snapshots = await self.list_snapshots(processor_id=processor_id, limit=1)
        return snapshots[0] if snapshots else None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get snapshot manager statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "storage_path": str(self.storage_path),
            "capture_count": self._capture_count,
            "restore_count": self._restore_count,
            "validation_failures": self._validation_failures,
            "compression_enabled": self.compression_enabled,
            "max_snapshots_per_processor": self.max_snapshots_per_processor,
        }

    # Private methods

    def _generate_snapshot_id(self, processor_id: str) -> str:
        """Generate unique snapshot ID."""
        timestamp = int(time.time() * 1000)
        return f"{processor_id}_{timestamp}"

    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate checksum for data."""
        if self.checksum_algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif self.checksum_algorithm == "md5":
            return hashlib.md5(data).hexdigest()
        else:
            raise ValueError(f"Unsupported checksum algorithm: {self.checksum_algorithm}")

    def _validate_state_data(self, state_data: Dict[str, Any]) -> bool:
        """
        Validate state data before capture.

        Args:
            state_data: State data to validate

        Returns:
            True if valid
        """
        # Basic validation
        if not isinstance(state_data, dict):
            logger.error("State data must be a dictionary")
            return False

        # Check if serializable
        try:
            json.dumps(state_data)
        except (TypeError, ValueError) as e:
            logger.error(f"State data is not JSON serializable: {e}")
            return False

        return True

    async def _save_snapshot(self, snapshot: Snapshot, state_bytes: bytes) -> None:
        """Save snapshot to storage."""
        snapshot_id = snapshot.metadata.snapshot_id

        # Save data file
        data_file = self.storage_path / f"{snapshot_id}.data"
        with open(data_file, "wb") as f:
            f.write(state_bytes)

        # Save metadata file
        meta_file = self.storage_path / f"{snapshot_id}.meta.json"
        with open(meta_file, "w") as f:
            json.dump(snapshot.metadata.to_dict(), f, indent=2)

    async def _load_snapshot(self, snapshot_id: str) -> tuple[Snapshot, bytes]:
        """Load snapshot from storage."""
        # Load metadata
        meta_file = self.storage_path / f"{snapshot_id}.meta.json"
        if not meta_file.exists():
            raise SnapshotStorageError(f"Snapshot metadata not found: {snapshot_id}")

        with open(meta_file, "r") as f:
            meta_data = json.load(f)
            metadata = SnapshotMetadata.from_dict(meta_data)

        # Load data
        data_file = self.storage_path / f"{snapshot_id}.data"
        if not data_file.exists():
            raise SnapshotStorageError(f"Snapshot data not found: {snapshot_id}")

        with open(data_file, "rb") as f:
            state_bytes = f.read()

        # Decompress if needed
        if metadata.compressed:
            state_json = gzip.decompress(state_bytes).decode()
        else:
            state_json = state_bytes.decode()

        # Parse JSON
        state_data = json.loads(state_json)

        # Create snapshot object
        snapshot = Snapshot(metadata=metadata, state_data=state_data)

        return snapshot, state_bytes

    async def _update_metadata(self, metadata: SnapshotMetadata) -> None:
        """Update snapshot metadata."""
        meta_file = self.storage_path / f"{metadata.snapshot_id}.meta.json"
        with open(meta_file, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

    async def _cleanup_old_snapshots(self, processor_id: str) -> int:
        """
        Cleanup old snapshots exceeding max limit.

        Args:
            processor_id: Processor ID

        Returns:
            Number of snapshots deleted
        """
        snapshots = await self.list_snapshots(processor_id=processor_id)

        # Keep only max_snapshots_per_processor newest snapshots
        if len(snapshots) <= self.max_snapshots_per_processor:
            return 0

        # Delete excess snapshots
        to_delete = snapshots[self.max_snapshots_per_processor:]
        deleted_count = 0

        for metadata in to_delete:
            if await self.delete_snapshot(metadata.snapshot_id):
                deleted_count += 1

        if deleted_count > 0:
            logger.info(
                f"Cleaned up {deleted_count} old snapshots for processor {processor_id}"
            )

        return deleted_count
