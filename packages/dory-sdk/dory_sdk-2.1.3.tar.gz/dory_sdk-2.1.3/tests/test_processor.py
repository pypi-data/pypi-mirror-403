"""Tests for processor base class and context."""

import asyncio
import pytest
from typing import Any

from dory.core.processor import BaseProcessor
from dory.core.context import ExecutionContext


class SimpleTestProcessor(BaseProcessor):
    """Simple processor implementation for testing."""

    def __init__(self, context: ExecutionContext):
        super().__init__(context)
        self.started = False
        self.stopped = False
        self.run_count = 0
        self._state = {"counter": 0}

    async def startup(self) -> None:
        self.started = True

    async def run(self) -> None:
        self.run_count += 1
        self._state["counter"] += 1

    async def shutdown(self) -> None:
        self.stopped = True

    def get_state(self) -> dict[str, Any]:
        return self._state.copy()

    async def restore_state(self, state: dict[str, Any]) -> None:
        self._state = state.copy()


class TestExecutionContext:
    """Tests for ExecutionContext."""

    def test_from_environment(self, monkeypatch):
        """Test creating context from environment."""
        monkeypatch.setenv("POD_NAME", "test-pod-123")
        monkeypatch.setenv("POD_NAMESPACE", "test-ns")
        monkeypatch.setenv("PROCESSOR_ID", "my-processor")

        context = ExecutionContext.from_environment()

        assert context.pod_name == "test-pod-123"
        assert context.pod_namespace == "test-ns"
        assert context.processor_id == "my-processor"

    def test_shutdown_requested(self):
        """Test shutdown request handling."""
        context = ExecutionContext(
            pod_name="pod",
            pod_namespace="ns",
            processor_id="proc",
        )

        assert context.is_shutdown_requested() is False

        context.request_shutdown()

        assert context.is_shutdown_requested() is True

    def test_migration_imminent(self):
        """Test migration imminent signal."""
        context = ExecutionContext(
            pod_name="pod",
            pod_namespace="ns",
            processor_id="proc",
        )

        assert context.is_migration_imminent() is False

        context.signal_migration()

        assert context.is_migration_imminent() is True

    def test_attempt_number(self):
        """Test attempt number tracking."""
        context = ExecutionContext(
            pod_name="pod",
            pod_namespace="ns",
            processor_id="proc",
            attempt_number=1,
        )

        assert context.attempt_number == 1

        context.set_attempt_number(5)

        assert context.attempt_number == 5

    def test_processor_id_from_pod_name(self, monkeypatch):
        """Test processor ID derivation from pod name."""
        monkeypatch.setenv("POD_NAME", "myapp-7f8d9c6b-x4h2j")
        monkeypatch.delenv("PROCESSOR_ID", raising=False)

        context = ExecutionContext.from_environment()

        # Should extract prefix from deployment pod name
        assert "myapp" in context.processor_id


class TestBaseProcessor:
    """Tests for BaseProcessor base class."""

    @pytest.fixture
    def context(self):
        """Create a test context."""
        return ExecutionContext(
            pod_name="test-pod",
            pod_namespace="test-ns",
            processor_id="test-proc",
        )

    @pytest.fixture
    def processor(self, context):
        """Create a test processor."""
        return SimpleTestProcessor(context)

    @pytest.mark.asyncio
    async def test_startup(self, processor):
        """Test processor startup."""
        await processor.startup()
        assert processor.started is True

    @pytest.mark.asyncio
    async def test_run(self, processor):
        """Test processor run."""
        await processor.run()
        assert processor.run_count == 1
        assert processor._state["counter"] == 1

    @pytest.mark.asyncio
    async def test_shutdown(self, processor):
        """Test processor shutdown."""
        await processor.shutdown()
        assert processor.stopped is True

    @pytest.mark.asyncio
    async def test_state_save_restore(self, processor):
        """Test state save and restore."""
        # Modify state
        await processor.run()
        await processor.run()

        # Get state
        state = processor.get_state()
        assert state["counter"] == 2

        # Create new processor and restore
        new_processor = SimpleTestProcessor(processor.context)
        await new_processor.restore_state(state)

        assert new_processor._state["counter"] == 2

    def test_context_access(self, processor):
        """Test context is accessible."""
        assert processor.context.pod_name == "test-pod"
        assert processor.context.processor_id == "test-proc"

    @pytest.mark.asyncio
    async def test_default_fault_handlers(self, processor):
        """Test default fault handler implementations."""
        # Default: continue on state restore failure
        result = await processor.on_state_restore_failed(Exception("test"))
        assert result is True

        # Default: continue on rapid restart
        result = await processor.on_rapid_restart_detected(5)
        assert result is True

        # Default: don't continue on health check failure
        result = await processor.on_health_check_failed(Exception("test"))
        assert result is False
