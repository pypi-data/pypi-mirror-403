"""
Tests for request tracker middleware.
"""

import asyncio
import pytest

from dory.middleware.request_tracker import (
    RequestTracker,
    track_request,
    RequestStatus,
)


@pytest.mark.asyncio
class TestRequestTracker:
    """Test RequestTracker functionality."""

    async def test_track_request_success(self):
        """Test successful request tracking."""
        tracker = RequestTracker()

        async with tracker.track("test_request") as request_id:
            assert request_id is not None
            # Simulate work
            await asyncio.sleep(0.01)

        # Check metrics
        metrics = tracker.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.active_requests == 0

    async def test_track_request_failure(self):
        """Test failed request tracking."""
        tracker = RequestTracker()

        with pytest.raises(ValueError):
            async with tracker.track("test_request"):
                raise ValueError("Test error")

        # Check metrics
        metrics = tracker.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.failed_requests == 1
        assert metrics.successful_requests == 0

    async def test_track_request_timeout(self):
        """Test request timeout tracking."""
        tracker = RequestTracker()

        with pytest.raises(asyncio.TimeoutError):
            async with tracker.track("test_request", timeout=0.01):
                await asyncio.sleep(1.0)  # Will timeout

        # Check metrics
        metrics = tracker.get_metrics()
        assert metrics.timeout_requests == 1

    async def test_active_request_tracking(self):
        """Test active request tracking."""
        tracker = RequestTracker()

        async def long_request():
            async with tracker.track("long_request"):
                await asyncio.sleep(0.1)

        # Start request
        task = asyncio.create_task(long_request())

        # Give it time to start
        await asyncio.sleep(0.01)

        # Check active requests
        metrics = tracker.get_metrics()
        assert metrics.active_requests == 1

        # Wait for completion
        await task

        # Check completed
        metrics = tracker.get_metrics()
        assert metrics.active_requests == 0
        assert metrics.successful_requests == 1

    async def test_duration_tracking(self):
        """Test duration tracking."""
        tracker = RequestTracker()

        async with tracker.track("test_request"):
            await asyncio.sleep(0.05)

        metrics = tracker.get_metrics()
        assert metrics.avg_duration > 0.04
        assert metrics.min_duration > 0.04
        assert metrics.max_duration > 0.04

    async def test_metrics_by_type(self):
        """Test metrics aggregation by request type."""
        tracker = RequestTracker()

        async with tracker.track("type_a"):
            pass

        async with tracker.track("type_b"):
            pass

        async with tracker.track("type_a"):
            pass

        # Check overall metrics
        overall = tracker.get_metrics()
        assert overall.total_requests == 3

        # Check type-specific metrics
        type_a_metrics = tracker.get_metrics("type_a")
        assert type_a_metrics.total_requests == 2

        type_b_metrics = tracker.get_metrics("type_b")
        assert type_b_metrics.total_requests == 1

    async def test_request_history(self):
        """Test request history tracking."""
        tracker = RequestTracker(enable_history=True, max_history=10)

        for i in range(5):
            async with tracker.track(f"request_{i}"):
                pass

        history = tracker.get_request_history()
        assert len(history) == 5

        # Most recent first
        assert "request_4" in history[0].request_id

    async def test_decorator(self):
        """Test track_request decorator."""
        tracker = RequestTracker()

        @track_request(tracker, "decorated_request")
        async def my_function():
            await asyncio.sleep(0.01)
            return "result"

        result = await my_function()
        assert result == "result"

        metrics = tracker.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1

    async def test_decorator_with_error(self):
        """Test decorator with error."""
        tracker = RequestTracker()

        @track_request(tracker, "decorated_request")
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

        metrics = tracker.get_metrics()
        assert metrics.failed_requests == 1

    async def test_callbacks(self):
        """Test request callbacks."""
        started = []
        completed = []

        def on_start(request_info):
            started.append(request_info.request_id)

        def on_complete(request_info):
            completed.append(request_info.request_id)

        tracker = RequestTracker(
            on_request_start=on_start,
            on_request_complete=on_complete,
        )

        async with tracker.track("test_request"):
            pass

        assert len(started) == 1
        assert len(completed) == 1

    async def test_success_rate(self):
        """Test success rate calculation."""
        tracker = RequestTracker()

        # 3 successes
        for _ in range(3):
            async with tracker.track("test"):
                pass

        # 1 failure
        try:
            async with tracker.track("test"):
                raise ValueError()
        except ValueError:
            pass

        metrics = tracker.get_metrics()
        assert metrics.get_success_rate() == 0.75  # 3/4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
