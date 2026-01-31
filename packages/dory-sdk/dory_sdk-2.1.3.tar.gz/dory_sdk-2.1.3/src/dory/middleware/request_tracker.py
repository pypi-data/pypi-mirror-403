"""
Request Tracker Middleware

Automatically tracks request lifecycle, duration, success/failure, and metrics.
Eliminates boilerplate for request tracking.

Features:
- Automatic request lifecycle tracking
- Duration measurement
- Success/failure counting
- Active request tracking
- Request metrics aggregation
- Decorators for easy integration
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Dict, Optional, List, Callable, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    """Request status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class RequestInfo:
    """
    Information about a tracked request.
    """
    request_id: str
    request_type: str
    status: RequestStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "request_type": self.request_type,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "error": self.error,
            "metadata": self.metadata,
        }

    def is_active(self) -> bool:
        """Check if request is still active."""
        return self.status in [RequestStatus.PENDING, RequestStatus.IN_PROGRESS]


@dataclass
class RequestMetrics:
    """
    Aggregated request metrics.
    """
    total_requests: int = 0
    active_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    cancelled_requests: int = 0
    total_duration: float = 0.0
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    avg_duration: float = 0.0

    def update_duration(self, duration: float) -> None:
        """Update duration statistics."""
        self.total_duration += duration
        if self.min_duration is None or duration < self.min_duration:
            self.min_duration = duration
        if self.max_duration is None or duration > self.max_duration:
            self.max_duration = duration

        completed = self.successful_requests + self.failed_requests + self.timeout_requests + self.cancelled_requests
        if completed > 0:
            self.avg_duration = self.total_duration / completed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "active_requests": self.active_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "timeout_requests": self.timeout_requests,
            "cancelled_requests": self.cancelled_requests,
            "total_duration": self.total_duration,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "avg_duration": self.avg_duration,
            "success_rate": self.get_success_rate(),
        }

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        completed = self.successful_requests + self.failed_requests + self.timeout_requests + self.cancelled_requests
        if completed == 0:
            return 0.0
        return self.successful_requests / completed


class RequestTracker:
    """
    Tracks requests automatically.

    Features:
    - Automatic request tracking
    - Duration measurement
    - Success/failure counting
    - Active request monitoring
    - Metrics aggregation by request type
    - Request history

    Usage:
        tracker = RequestTracker()

        # Track request manually
        async with tracker.track("process_item") as request_id:
            await process_item()

        # Or use decorator
        @track_request(tracker, "process_item")
        async def process_item():
            pass

        # Get metrics
        metrics = tracker.get_metrics()
        print(f"Active requests: {metrics.active_requests}")
    """

    def __init__(
        self,
        max_history: int = 1000,
        enable_history: bool = True,
        on_request_start: Optional[Callable] = None,
        on_request_complete: Optional[Callable] = None,
    ):
        """
        Initialize request tracker.

        Args:
            max_history: Maximum number of completed requests to keep in history
            enable_history: Whether to keep request history
            on_request_start: Callback when request starts
            on_request_complete: Callback when request completes
        """
        self.max_history = max_history
        self.enable_history = enable_history
        self.on_request_start = on_request_start
        self.on_request_complete = on_request_complete

        # Active requests
        self._active_requests: Dict[str, RequestInfo] = {}

        # Request history (completed requests)
        self._request_history: List[RequestInfo] = []

        # Metrics by request type
        self._metrics: Dict[str, RequestMetrics] = defaultdict(RequestMetrics)

        # Overall metrics
        self._overall_metrics = RequestMetrics()

        # Request counter
        self._request_counter = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"RequestTracker initialized: max_history={max_history}, "
            f"enable_history={enable_history}"
        )

    def _generate_request_id(self, request_type: str) -> str:
        """Generate unique request ID."""
        self._request_counter += 1
        timestamp = int(time.time() * 1000)
        return f"{request_type}_{timestamp}_{self._request_counter}"

    @asynccontextmanager
    async def track(
        self,
        request_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ):
        """
        Context manager to track a request.

        Args:
            request_type: Type of request
            metadata: Optional metadata
            timeout: Optional timeout in seconds

        Yields:
            Request ID

        Example:
            async with tracker.track("process_item") as request_id:
                await process_item()
        """
        request_id = self._generate_request_id(request_type)

        async with self._lock:
            # Create request info
            request_info = RequestInfo(
                request_id=request_id,
                request_type=request_type,
                status=RequestStatus.IN_PROGRESS,
                start_time=time.time(),
                metadata=metadata or {},
            )

            # Add to active requests
            self._active_requests[request_id] = request_info

            # Update metrics
            self._metrics[request_type].total_requests += 1
            self._metrics[request_type].active_requests += 1
            self._overall_metrics.total_requests += 1
            self._overall_metrics.active_requests += 1

        # Call start callback
        if self.on_request_start:
            try:
                if asyncio.iscoroutinefunction(self.on_request_start):
                    await self.on_request_start(request_info)
                else:
                    self.on_request_start(request_info)
            except Exception as e:
                logger.error(f"Request start callback failed: {e}")

        logger.debug(f"Request started: {request_id} ({request_type})")

        try:
            # Execute with optional timeout
            if timeout:
                # Python 3.10 compatible timeout implementation
                timeout_handle = None
                timed_out = False

                def _timeout_callback():
                    nonlocal timed_out
                    timed_out = True

                try:
                    # Set up timeout
                    loop = asyncio.get_event_loop()
                    timeout_handle = loop.call_later(timeout, _timeout_callback)

                    yield request_id

                    # Check if timed out
                    if timed_out:
                        await self._complete_request(request_id, RequestStatus.TIMEOUT, "Request timeout")
                        raise asyncio.TimeoutError("Request timeout")

                    await self._complete_request(request_id, RequestStatus.SUCCESS)

                finally:
                    # Cancel timeout if still pending
                    if timeout_handle is not None:
                        timeout_handle.cancel()
            else:
                yield request_id
                await self._complete_request(request_id, RequestStatus.SUCCESS)

        except asyncio.CancelledError:
            await self._complete_request(request_id, RequestStatus.CANCELLED, "Request cancelled")
            raise

        except Exception as e:
            await self._complete_request(request_id, RequestStatus.FAILED, str(e))
            raise

    async def _complete_request(
        self,
        request_id: str,
        status: RequestStatus,
        error: Optional[str] = None,
    ) -> None:
        """Complete a request."""
        async with self._lock:
            if request_id not in self._active_requests:
                logger.warning(f"Request {request_id} not found in active requests")
                return

            request_info = self._active_requests[request_id]
            request_type = request_info.request_type

            # Update request info
            request_info.status = status
            request_info.end_time = time.time()
            request_info.duration = request_info.end_time - request_info.start_time
            request_info.error = error

            # Update metrics
            self._metrics[request_type].active_requests -= 1
            self._overall_metrics.active_requests -= 1

            if status == RequestStatus.SUCCESS:
                self._metrics[request_type].successful_requests += 1
                self._overall_metrics.successful_requests += 1
            elif status == RequestStatus.FAILED:
                self._metrics[request_type].failed_requests += 1
                self._overall_metrics.failed_requests += 1
            elif status == RequestStatus.TIMEOUT:
                self._metrics[request_type].timeout_requests += 1
                self._overall_metrics.timeout_requests += 1
            elif status == RequestStatus.CANCELLED:
                self._metrics[request_type].cancelled_requests += 1
                self._overall_metrics.cancelled_requests += 1

            # Update duration stats
            if request_info.duration is not None:
                self._metrics[request_type].update_duration(request_info.duration)
                self._overall_metrics.update_duration(request_info.duration)

            # Move to history
            if self.enable_history:
                self._request_history.append(request_info)
                if len(self._request_history) > self.max_history:
                    self._request_history.pop(0)

            # Remove from active
            del self._active_requests[request_id]

        # Call complete callback
        if self.on_request_complete:
            try:
                if asyncio.iscoroutinefunction(self.on_request_complete):
                    await self.on_request_complete(request_info)
                else:
                    self.on_request_complete(request_info)
            except Exception as e:
                logger.error(f"Request complete callback failed: {e}")

        logger.debug(
            f"Request completed: {request_id} ({request_type}) - "
            f"{status.value} in {request_info.duration:.3f}s"
        )

    def get_active_requests(self, request_type: Optional[str] = None) -> List[RequestInfo]:
        """
        Get active requests.

        Args:
            request_type: Optional filter by request type

        Returns:
            List of active request info
        """
        if request_type:
            return [
                req for req in self._active_requests.values()
                if req.request_type == request_type
            ]
        return list(self._active_requests.values())

    def get_request_history(
        self,
        request_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[RequestInfo]:
        """
        Get request history.

        Args:
            request_type: Optional filter by request type
            limit: Optional limit on number of requests

        Returns:
            List of completed request info (most recent first)
        """
        history = list(reversed(self._request_history))

        if request_type:
            history = [req for req in history if req.request_type == request_type]

        if limit:
            history = history[:limit]

        return history

    def get_metrics(self, request_type: Optional[str] = None) -> RequestMetrics:
        """
        Get request metrics.

        Args:
            request_type: Optional filter by request type (None for overall)

        Returns:
            RequestMetrics
        """
        if request_type:
            return self._metrics[request_type]
        return self._overall_metrics

    def get_all_metrics(self) -> Dict[str, RequestMetrics]:
        """
        Get metrics for all request types.

        Returns:
            Dictionary mapping request type to metrics
        """
        return dict(self._metrics)

    def reset_metrics(self, request_type: Optional[str] = None) -> None:
        """
        Reset metrics.

        Args:
            request_type: Optional request type (None resets all)
        """
        if request_type:
            self._metrics[request_type] = RequestMetrics()
        else:
            self._metrics.clear()
            self._overall_metrics = RequestMetrics()

        logger.info(f"Metrics reset: {request_type or 'all'}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get tracker statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "active_requests_count": len(self._active_requests),
            "history_count": len(self._request_history),
            "tracked_request_types": len(self._metrics),
            "overall_metrics": self._overall_metrics.to_dict(),
        }


# Decorator for automatic request tracking

def track_request(
    tracker: RequestTracker,
    request_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
):
    """
    Decorator to automatically track requests.

    Args:
        tracker: RequestTracker instance
        request_type: Type of request (uses function name if None)
        metadata: Optional metadata
        timeout: Optional timeout in seconds

    Example:
        tracker = RequestTracker()

        @track_request(tracker, "process_item")
        async def process_item(item):
            # Processing logic
            pass

        # Request automatically tracked with duration, success/failure
        await process_item(my_item)
    """
    def decorator(func):
        nonlocal request_type
        if request_type is None:
            request_type = func.__name__

        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with tracker.track(request_type, metadata, timeout):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
