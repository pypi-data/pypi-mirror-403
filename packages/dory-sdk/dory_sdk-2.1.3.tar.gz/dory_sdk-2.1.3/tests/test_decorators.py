"""Tests for stateful decorator and auto-state management."""

import pytest
from dory.decorators import (
    stateful,
    StatefulVar,
    get_stateful_vars,
    set_stateful_vars,
)
from dory.core.processor import BaseProcessor
from dory.core.context import ExecutionContext


class TestStatefulDecorator:
    """Tests for @stateful decorator."""

    def test_simple_value(self):
        """Test stateful with simple default value."""

        class MyProcessor(BaseProcessor):
            counter = stateful(0)

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        assert proc.counter == 0
        proc.counter = 5
        assert proc.counter == 5

    def test_factory_default(self):
        """Test stateful with factory function for mutable defaults."""

        class MyProcessor(BaseProcessor):
            data = stateful(dict)
            items = stateful(list)

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc1 = MyProcessor(ctx)
        proc2 = MyProcessor(ctx)

        # Each instance should have its own dict/list
        proc1.data["key"] = "value1"
        proc2.data["key"] = "value2"

        assert proc1.data["key"] == "value1"
        assert proc2.data["key"] == "value2"

    def test_get_stateful_vars(self):
        """Test automatic state collection."""

        class MyProcessor(BaseProcessor):
            counter = stateful(0)
            name = stateful("default")
            data = stateful(dict)

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        proc.counter = 42
        proc.name = "test"
        proc.data["key"] = "value"

        state = get_stateful_vars(proc)

        assert state == {
            "counter": 42,
            "name": "test",
            "data": {"key": "value"},
        }

    def test_set_stateful_vars(self):
        """Test automatic state restoration."""

        class MyProcessor(BaseProcessor):
            counter = stateful(0)
            name = stateful("default")

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        state = {"counter": 100, "name": "restored"}
        set_stateful_vars(proc, state)

        assert proc.counter == 100
        assert proc.name == "restored"

    def test_partial_state_restore(self):
        """Test restoring only some state vars."""

        class MyProcessor(BaseProcessor):
            a = stateful(1)
            b = stateful(2)
            c = stateful(3)

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        # Only restore 'b'
        set_stateful_vars(proc, {"b": 200})

        assert proc.a == 1  # Unchanged
        assert proc.b == 200  # Restored
        assert proc.c == 3  # Unchanged


class TestBaseProcessorAutoState:
    """Tests for BaseProcessor auto get_state/restore_state."""

    def test_auto_get_state(self):
        """Test automatic get_state with @stateful vars."""

        class MyProcessor(BaseProcessor):
            counter = stateful(0)
            data = stateful(dict)

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        proc.counter = 42
        proc.data["key"] = "value"

        state = proc.get_state()

        assert state == {"counter": 42, "data": {"key": "value"}}

    @pytest.mark.asyncio
    async def test_auto_restore_state(self):
        """Test automatic restore_state with @stateful vars."""

        class MyProcessor(BaseProcessor):
            counter = stateful(0)
            data = stateful(dict)

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        await proc.restore_state({"counter": 100, "data": {"restored": True}})

        assert proc.counter == 100
        assert proc.data == {"restored": True}

    def test_empty_state_when_no_stateful(self):
        """Test get_state returns {} when no @stateful vars."""

        class MyProcessor(BaseProcessor):
            def __init__(self, context):
                super().__init__(context)
                self.regular_var = 0

            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        state = proc.get_state()
        assert state == {}

    def test_custom_get_state_overrides_auto(self):
        """Test that custom get_state overrides auto behavior."""

        class MyProcessor(BaseProcessor):
            counter = stateful(0)

            async def run(self):
                pass

            def get_state(self):
                return {"custom": "state"}

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        state = proc.get_state()
        assert state == {"custom": "state"}


class TestRunLoopHelper:
    """Tests for run_loop() helper method."""

    @pytest.mark.asyncio
    async def test_run_loop_iterations(self):
        """Test run_loop yields iteration counts."""

        class MyProcessor(BaseProcessor):
            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        iterations = []

        # Request shutdown after 3 iterations
        async def limited_loop():
            async for i in proc.run_loop(interval=0.01):
                iterations.append(i)
                if i >= 2:
                    ctx.request_shutdown()

        await limited_loop()

        assert iterations == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_run_loop_stops_on_shutdown(self):
        """Test run_loop exits when shutdown requested."""

        class MyProcessor(BaseProcessor):
            async def run(self):
                pass

        ctx = ExecutionContext.from_environment()
        proc = MyProcessor(ctx)

        # Pre-request shutdown
        ctx.request_shutdown()

        iterations = []
        async for i in proc.run_loop(interval=0.01):
            iterations.append(i)

        # Should yield nothing since shutdown already requested
        assert iterations == []
