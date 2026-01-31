"""
Prometheus metrics collector.

Collects and exports metrics in Prometheus format.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """A single metric value with labels."""
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class MetricDefinition:
    """Definition of a metric."""
    name: str
    help: str
    type: str  # counter, gauge, histogram, summary
    values: List[MetricValue] = field(default_factory=list)


class MetricsCollector:
    """
    Collects and exports Prometheus metrics.

    Metrics collected:
    - dory_startup_duration_seconds: Time to complete startup
    - dory_shutdown_duration_seconds: Time to complete shutdown
    - dory_state_save_duration_seconds: Time to save state
    - dory_state_load_duration_seconds: Time to load state
    - dory_restart_count: Number of restarts
    - dory_golden_image_resets: Number of golden image resets
    - dory_health_check_failures: Number of health check failures
    """

    def __init__(self, prefix: str = "dory"):
        """
        Initialize metrics collector.

        Args:
            prefix: Metric name prefix
        """
        self._prefix = prefix
        self._metrics: Dict[str, MetricDefinition] = {}

        # Timing state
        self._startup_start: float | None = None
        self._startup_completed_at: float | None = None
        self._shutdown_start: float | None = None
        self._request_count: int = 0

        # Initialize standard metrics
        self._init_standard_metrics()

    def _init_standard_metrics(self) -> None:
        """Initialize standard Dory metrics."""
        self._register_metric(
            "startup_duration_seconds",
            "Time to complete processor startup",
            "gauge",
        )
        self._register_metric(
            "shutdown_duration_seconds",
            "Time to complete processor shutdown",
            "gauge",
        )
        self._register_metric(
            "state_save_duration_seconds",
            "Time to save processor state",
            "gauge",
        )
        self._register_metric(
            "state_load_duration_seconds",
            "Time to load processor state",
            "gauge",
        )
        self._register_metric(
            "restart_count",
            "Total number of processor restarts",
            "counter",
        )
        self._register_metric(
            "golden_image_resets_total",
            "Total number of golden image resets",
            "counter",
        )
        self._register_metric(
            "health_check_failures_total",
            "Total number of health check failures",
            "counter",
        )
        self._register_metric(
            "state_size_bytes",
            "Size of processor state in bytes",
            "gauge",
        )
        self._register_metric(
            "processor_info",
            "Processor information",
            "gauge",
        )

    def _register_metric(self, name: str, help: str, type: str) -> None:
        """Register a metric definition."""
        full_name = f"{self._prefix}_{name}"
        self._metrics[full_name] = MetricDefinition(
            name=full_name,
            help=help,
            type=type,
        )

    def _metric_name(self, name: str) -> str:
        """Get full metric name."""
        return f"{self._prefix}_{name}"

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] | None = None,
    ) -> None:
        """
        Set a gauge metric value.

        Args:
            name: Metric name (without prefix)
            value: Metric value
            labels: Optional labels
        """
        full_name = self._metric_name(name)
        if full_name not in self._metrics:
            self._register_metric(name, f"Custom gauge {name}", "gauge")

        metric = self._metrics[full_name]
        metric.values = [MetricValue(value=value, labels=labels or {})]

    def inc_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Dict[str, str] | None = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name (without prefix)
            value: Amount to increment (default 1)
            labels: Optional labels
        """
        full_name = self._metric_name(name)
        if full_name not in self._metrics:
            self._register_metric(name, f"Custom counter {name}", "counter")

        metric = self._metrics[full_name]

        # Find existing value with same labels or create new
        labels = labels or {}
        for mv in metric.values:
            if mv.labels == labels:
                mv.value += value
                mv.timestamp = time.time()
                return

        metric.values.append(MetricValue(value=value, labels=labels))

    # Convenience methods for standard metrics

    def record_startup_started(self) -> None:
        """Record that startup has started."""
        self._startup_start = time.time()

    def record_startup_completed(self) -> None:
        """Record that startup has completed."""
        self._startup_completed_at = time.time()
        if self._startup_start:
            duration = self._startup_completed_at - self._startup_start
            self.set_gauge("startup_duration_seconds", duration)
            logger.debug(f"Startup completed in {duration:.3f}s")

    def record_shutdown_started(self) -> None:
        """Record that shutdown has started."""
        self._shutdown_start = time.time()

    def record_shutdown_completed(self) -> None:
        """Record that shutdown has completed."""
        if self._shutdown_start:
            duration = time.time() - self._shutdown_start
            self.set_gauge("shutdown_duration_seconds", duration)
            logger.debug(f"Shutdown completed in {duration:.3f}s")

    def record_state_save(self, duration: float, size_bytes: int = 0) -> None:
        """Record state save operation."""
        self.set_gauge("state_save_duration_seconds", duration)
        if size_bytes > 0:
            self.set_gauge("state_size_bytes", size_bytes)

    def record_state_load(self, duration: float) -> None:
        """Record state load operation."""
        self.set_gauge("state_load_duration_seconds", duration)

    def record_restart(self) -> None:
        """Record a restart event."""
        self.inc_counter("restart_count")

    def record_golden_image_reset(self) -> None:
        """Record a golden image reset."""
        self.inc_counter("golden_image_resets_total")

    def record_health_check_failure(self) -> None:
        """Record a health check failure."""
        self.inc_counter("health_check_failures_total")

    def set_processor_info(
        self,
        processor_id: str,
        version: str = "",
        pod_name: str = "",
    ) -> None:
        """Set processor information metric."""
        self.set_gauge(
            "processor_info",
            1.0,
            labels={
                "processor_id": processor_id,
                "version": version,
                "pod": pod_name,
            },
        )

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        for metric in self._metrics.values():
            # HELP line
            lines.append(f"# HELP {metric.name} {metric.help}")
            # TYPE line
            lines.append(f"# TYPE {metric.name} {metric.type}")

            # Metric values
            for mv in metric.values:
                if mv.labels:
                    label_str = ",".join(
                        f'{k}="{v}"' for k, v in mv.labels.items()
                    )
                    lines.append(f"{metric.name}{{{label_str}}} {mv.value}")
                else:
                    lines.append(f"{metric.name} {mv.value}")

        return "\n".join(lines) + "\n"

    def flush(self) -> None:
        """Flush any buffered metrics."""
        # In this implementation, metrics are not buffered
        # This is a hook for implementations that buffer
        pass

    def get_uptime_seconds(self) -> float:
        """
        Get the processor uptime in seconds.

        Returns:
            Uptime in seconds since startup completed, or 0 if not started
        """
        if self._startup_completed_at is None:
            return 0.0
        return time.time() - self._startup_completed_at

    def get_request_count(self) -> int:
        """
        Get the total request count.

        Returns:
            Total number of requests processed
        """
        return self._request_count

    def increment_request_count(self, count: int = 1) -> None:
        """
        Increment the request counter.

        Args:
            count: Amount to increment (default 1)
        """
        self._request_count += count
