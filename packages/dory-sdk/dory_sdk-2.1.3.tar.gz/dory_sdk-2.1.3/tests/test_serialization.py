"""Tests for state serialization."""

import json
import pytest
from dory.migration.serialization import StateSerializer, StateEnvelope
from dory.utils.errors import DoryStateError


class TestStateSerializer:
    """Tests for StateSerializer."""

    def test_serialize_simple_state(self):
        """Test serializing a simple state dictionary."""
        serializer = StateSerializer()
        state = {"counter": 42, "name": "test"}

        result = serializer.serialize(
            state=state,
            processor_id="test-proc",
            pod_name="test-pod",
            restart_count=0,
        )

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["payload"] == state
        assert parsed["metadata"]["processor_id"] == "test-proc"
        assert parsed["metadata"]["pod_name"] == "test-pod"
        assert "checksum" in parsed

    def test_deserialize_valid_state(self):
        """Test deserializing valid state."""
        serializer = StateSerializer()
        state = {"counter": 42}

        serialized = serializer.serialize(
            state=state,
            processor_id="test",
            pod_name="pod",
        )

        result = serializer.deserialize(serialized)
        assert result == state

    def test_deserialize_invalid_json(self):
        """Test deserializing invalid JSON raises error."""
        serializer = StateSerializer()

        with pytest.raises(DoryStateError) as exc_info:
            serializer.deserialize("not valid json")

        assert "Invalid JSON" in str(exc_info.value)

    def test_deserialize_corrupted_checksum(self):
        """Test deserializing with corrupted checksum raises error."""
        serializer = StateSerializer()

        # Create valid envelope then corrupt checksum
        envelope = {
            "payload": {"counter": 42},
            "metadata": {},
            "checksum": "invalid_checksum",
        }

        with pytest.raises(DoryStateError) as exc_info:
            serializer.deserialize(json.dumps(envelope))

        assert "checksum mismatch" in str(exc_info.value)

    def test_deserialize_missing_field(self):
        """Test deserializing with missing field raises error."""
        serializer = StateSerializer()

        envelope = {"payload": {}}  # Missing checksum and metadata

        with pytest.raises(DoryStateError) as exc_info:
            serializer.deserialize(json.dumps(envelope))

        assert "Missing field" in str(exc_info.value)

    def test_checksum_deterministic(self):
        """Test that checksum is deterministic for same payload."""
        serializer = StateSerializer()
        state = {"b": 2, "a": 1}  # Different order

        checksum1 = StateSerializer.compute_checksum(state)
        checksum2 = StateSerializer.compute_checksum(state)

        assert checksum1 == checksum2

    def test_checksum_different_for_different_payload(self):
        """Test that checksum differs for different payloads."""
        state1 = {"counter": 1}
        state2 = {"counter": 2}

        checksum1 = StateSerializer.compute_checksum(state1)
        checksum2 = StateSerializer.compute_checksum(state2)

        assert checksum1 != checksum2

    def test_deserialize_with_metadata(self):
        """Test deserializing with full metadata."""
        serializer = StateSerializer()
        state = {"data": "value"}

        serialized = serializer.serialize(
            state=state,
            processor_id="proc-1",
            pod_name="pod-abc",
            restart_count=3,
        )

        envelope = serializer.deserialize_with_metadata(serialized)

        assert envelope.payload == state
        assert envelope.metadata["processor_id"] == "proc-1"
        assert envelope.metadata["restart_count"] == 3


class TestStateEnvelope:
    """Tests for StateEnvelope dataclass."""

    def test_to_dict(self):
        """Test converting envelope to dictionary."""
        envelope = StateEnvelope(
            payload={"key": "value"},
            metadata={"meta": "data"},
            checksum="abc123",
        )

        result = envelope.to_dict()

        assert result["payload"] == {"key": "value"}
        assert result["metadata"] == {"meta": "data"}
        assert result["checksum"] == "abc123"

    def test_from_dict(self):
        """Test creating envelope from dictionary."""
        data = {
            "payload": {"key": "value"},
            "metadata": {"meta": "data"},
            "checksum": "abc123",
        }

        envelope = StateEnvelope.from_dict(data)

        assert envelope.payload == {"key": "value"}
        assert envelope.metadata == {"meta": "data"}
        assert envelope.checksum == "abc123"
