"""
State serialization utilities.

Handles JSON serialization/deserialization with checksum validation.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

from dory.utils.errors import DoryStateError


@dataclass
class StateEnvelope:
    """
    Envelope wrapping state data with metadata.

    Attributes:
        payload: The actual state data
        metadata: Metadata about when/where state was created
        checksum: SHA256 checksum of payload for integrity
    """

    payload: dict[str, Any]
    metadata: dict[str, Any]
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "payload": self.payload,
            "metadata": self.metadata,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateEnvelope":
        """Create from dictionary."""
        return cls(
            payload=data["payload"],
            metadata=data["metadata"],
            checksum=data["checksum"],
        )


class StateSerializer:
    """
    Serializes and deserializes state with integrity checking.

    Uses JSON format with SHA256 checksums for integrity validation.
    """

    @staticmethod
    def compute_checksum(payload: dict[str, Any]) -> str:
        """
        Compute SHA256 checksum for payload.

        Args:
            payload: State payload

        Returns:
            Hex-encoded SHA256 checksum
        """
        payload_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_json.encode()).hexdigest()

    def serialize(
        self,
        state: dict[str, Any],
        processor_id: str,
        pod_name: str,
        restart_count: int = 0,
    ) -> str:
        """
        Serialize state to JSON string with envelope.

        Args:
            state: State dictionary to serialize
            processor_id: Processor ID for metadata
            pod_name: Pod name for metadata
            restart_count: Current restart count

        Returns:
            JSON string with state envelope
        """
        envelope = StateEnvelope(
            payload=state,
            metadata={
                "timestamp": time.time(),
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "processor_id": processor_id,
                "pod_name": pod_name,
                "restart_count": restart_count,
            },
            checksum=self.compute_checksum(state),
        )

        return json.dumps(envelope.to_dict(), indent=2)

    def deserialize(self, data: str) -> dict[str, Any]:
        """
        Deserialize state from JSON string.

        Args:
            data: JSON string with state envelope

        Returns:
            State payload dictionary

        Raises:
            DoryStateError: If deserialization or validation fails
        """
        try:
            envelope_dict = json.loads(data)
        except json.JSONDecodeError as e:
            raise DoryStateError(f"Invalid JSON in state data: {e}", cause=e)

        try:
            envelope = StateEnvelope.from_dict(envelope_dict)
        except KeyError as e:
            raise DoryStateError(f"Missing field in state envelope: {e}", cause=e)

        # Validate checksum
        expected_checksum = self.compute_checksum(envelope.payload)
        if envelope.checksum != expected_checksum:
            raise DoryStateError(
                f"State checksum mismatch: expected {expected_checksum}, "
                f"got {envelope.checksum}"
            )

        return envelope.payload

    def deserialize_with_metadata(self, data: str) -> StateEnvelope:
        """
        Deserialize state with full envelope including metadata.

        Args:
            data: JSON string with state envelope

        Returns:
            StateEnvelope with payload and metadata

        Raises:
            DoryStateError: If deserialization or validation fails
        """
        try:
            envelope_dict = json.loads(data)
        except json.JSONDecodeError as e:
            raise DoryStateError(f"Invalid JSON in state data: {e}", cause=e)

        try:
            envelope = StateEnvelope.from_dict(envelope_dict)
        except KeyError as e:
            raise DoryStateError(f"Missing field in state envelope: {e}", cause=e)

        # Validate checksum
        expected_checksum = self.compute_checksum(envelope.payload)
        if envelope.checksum != expected_checksum:
            raise DoryStateError(
                f"State checksum mismatch: expected {expected_checksum}, "
                f"got {envelope.checksum}"
            )

        return envelope
