"""
Dory Monitoring and Observability

OpenTelemetry integration for distributed tracing and metrics.
"""

from dory.monitoring.opentelemetry import (
    OpenTelemetryManager,
    trace_function,
    create_span,
    add_span_attributes,
    record_exception,
    get_tracer,
)

__all__ = [
    "OpenTelemetryManager",
    "trace_function",
    "create_span",
    "add_span_attributes",
    "record_exception",
    "get_tracer",
]
