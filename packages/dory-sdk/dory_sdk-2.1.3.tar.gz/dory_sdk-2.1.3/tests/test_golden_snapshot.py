"""
Tests for golden snapshot manager.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path

from dory.recovery.golden_snapshot import (
    GoldenSnapshotManager,
    Snapshot,
    SnapshotMetadata,
    SnapshotStorageError,
    SnapshotValidationError,
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
class TestGoldenSnapshotManager:
    """Test GoldenSnapshotManager functionality."""

    async def test_capture_snapshot(self, temp_storage):
        """Test capturing a snapshot."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        state_data = {"counter": 42, "status": "active", "data": [1, 2, 3]}

        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data=state_data,
            tags={"version": "1.0"},
        )

        assert snapshot.metadata.processor_id == "test-processor"
        assert snapshot.metadata.checksum is not None
        assert snapshot.metadata.size_bytes > 0
        assert snapshot.state_data == state_data
        assert snapshot.metadata.tags["version"] == "1.0"

    async def test_capture_with_compression(self, temp_storage):
        """Test snapshot capture with compression."""
        manager = GoldenSnapshotManager(
            storage_path=temp_storage,
            compression_enabled=True,
        )

        state_data = {"key": "value" * 1000}  # Larger data

        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data=state_data,
        )

        assert snapshot.metadata.compressed is True
        assert snapshot.metadata.size_bytes > 0

    async def test_restore_snapshot(self, temp_storage):
        """Test restoring from a snapshot."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        original_state = {"counter": 42, "status": "active"}

        # Capture
        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data=original_state,
        )

        # Restore
        restored_state = await manager.restore_snapshot(snapshot.metadata.snapshot_id)

        assert restored_state == original_state

    async def test_restore_with_checksum_validation(self, temp_storage):
        """Test restore with checksum validation."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        state_data = {"key": "value"}

        # Capture
        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data=state_data,
        )

        # Restore with validation
        restored_state = await manager.restore_snapshot(
            snapshot.metadata.snapshot_id,
            validate_checksum=True,
        )

        assert restored_state == state_data

    async def test_restore_nonexistent_snapshot(self, temp_storage):
        """Test restoring nonexistent snapshot raises error."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        with pytest.raises(SnapshotStorageError):
            await manager.restore_snapshot("nonexistent-snapshot")

    async def test_list_snapshots(self, temp_storage):
        """Test listing snapshots."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        # Create multiple snapshots
        await manager.capture_snapshot(
            processor_id="processor-1",
            state_data={"data": 1},
        )
        await manager.capture_snapshot(
            processor_id="processor-1",
            state_data={"data": 2},
        )
        await manager.capture_snapshot(
            processor_id="processor-2",
            state_data={"data": 3},
        )

        # List all snapshots
        all_snapshots = await manager.list_snapshots()
        assert len(all_snapshots) == 3

        # List for specific processor
        proc1_snapshots = await manager.list_snapshots(processor_id="processor-1")
        assert len(proc1_snapshots) == 2

    async def test_list_snapshots_with_limit(self, temp_storage):
        """Test listing snapshots with limit."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        # Create multiple snapshots
        for i in range(5):
            await manager.capture_snapshot(
                processor_id="test-processor",
                state_data={"data": i},
            )

        # List with limit
        snapshots = await manager.list_snapshots(limit=3)
        assert len(snapshots) == 3

    async def test_delete_snapshot(self, temp_storage):
        """Test deleting a snapshot."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        # Create snapshot
        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data={"data": "test"},
        )

        # Delete
        result = await manager.delete_snapshot(snapshot.metadata.snapshot_id)
        assert result is True

        # Verify deleted
        snapshots = await manager.list_snapshots()
        assert len(snapshots) == 0

    async def test_get_latest_snapshot(self, temp_storage):
        """Test getting latest snapshot."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        # Create snapshots
        await manager.capture_snapshot(
            processor_id="test-processor",
            state_data={"version": 1},
        )
        await asyncio.sleep(0.01)  # Ensure different timestamps
        snapshot2 = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data={"version": 2},
        )

        # Get latest
        latest = await manager.get_latest_snapshot("test-processor")
        assert latest is not None
        assert latest.snapshot_id == snapshot2.metadata.snapshot_id

    async def test_auto_cleanup(self, temp_storage):
        """Test automatic cleanup of old snapshots."""
        manager = GoldenSnapshotManager(
            storage_path=temp_storage,
            max_snapshots_per_processor=3,
            auto_cleanup=True,
        )

        # Create more than max snapshots
        for i in range(5):
            await manager.capture_snapshot(
                processor_id="test-processor",
                state_data={"version": i},
            )
            await asyncio.sleep(0.01)

        # Should only have 3 snapshots (most recent)
        snapshots = await manager.list_snapshots(processor_id="test-processor")
        assert len(snapshots) == 3

    async def test_snapshot_metadata_updates(self, temp_storage):
        """Test that metadata is updated on restore."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        # Create snapshot
        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data={"data": "test"},
        )

        assert snapshot.metadata.restore_count == 0
        assert snapshot.metadata.last_restored_at is None

        # Restore
        await manager.restore_snapshot(
            snapshot.metadata.snapshot_id,
            update_metadata=True,
        )

        # Check updated metadata
        snapshots = await manager.list_snapshots()
        assert snapshots[0].restore_count == 1
        assert snapshots[0].last_restored_at is not None

    async def test_capture_invalid_state(self, temp_storage):
        """Test capturing invalid state data."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        # Non-serializable data
        class NonSerializable:
            pass

        with pytest.raises(SnapshotValidationError):
            await manager.capture_snapshot(
                processor_id="test-processor",
                state_data={"obj": NonSerializable()},
            )

    async def test_capture_callback(self, temp_storage):
        """Test capture callback is called."""
        captured_snapshots = []

        def on_capture(snapshot):
            captured_snapshots.append(snapshot)

        manager = GoldenSnapshotManager(
            storage_path=temp_storage,
            on_capture=on_capture,
        )

        await manager.capture_snapshot(
            processor_id="test-processor",
            state_data={"data": "test"},
        )

        assert len(captured_snapshots) == 1

    async def test_restore_callback(self, temp_storage):
        """Test restore callback is called."""
        restored_snapshots = []

        def on_restore(snapshot):
            restored_snapshots.append(snapshot)

        manager = GoldenSnapshotManager(
            storage_path=temp_storage,
            on_restore=on_restore,
        )

        # Capture
        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data={"data": "test"},
        )

        # Restore
        await manager.restore_snapshot(snapshot.metadata.snapshot_id)

        assert len(restored_snapshots) == 1

    async def test_get_stats(self, temp_storage):
        """Test getting manager statistics."""
        manager = GoldenSnapshotManager(storage_path=temp_storage)

        # Capture and restore
        snapshot = await manager.capture_snapshot(
            processor_id="test-processor",
            state_data={"data": "test"},
        )
        await manager.restore_snapshot(snapshot.metadata.snapshot_id)

        stats = manager.get_stats()
        assert stats["capture_count"] == 1
        assert stats["restore_count"] == 1
        assert stats["validation_failures"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
