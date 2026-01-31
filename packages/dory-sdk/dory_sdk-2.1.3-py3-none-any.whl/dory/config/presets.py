"""Configuration presets for common scenarios."""

from typing import Dict, Any

# Development preset - developer-friendly defaults
DEVELOPMENT_PRESET = {
    "environment": "development",
    "log_level": "DEBUG",
    "log_format": "text",

    # Health server
    "health_port": 8080,
    "health_path": "/healthz",
    "ready_path": "/ready",
    "metrics_path": "/metrics",

    # State management
    "state_backend": "local",
    "state_pvc_mount": "/data",

    # Lifecycle timeouts
    "startup_timeout_sec": 30,
    "shutdown_timeout_sec": 30,
    "health_check_interval_sec": 10,

    # Recovery
    "max_restart_attempts": 3,
    "restart_backoff_sec": 10,
    "golden_image_threshold": 5,

    # Metrics
    "metrics_enabled": True,
    "metrics_prefix": "dory",

    # Retry configuration
    "retry": {
        "max_attempts": 3,
        "initial_delay": 0.1,
        "multiplier": 2.0,
        "max_delay": 30.0,
        "jitter": True,
        "budget_percent": 20.0,
    },

    # Circuit breaker configuration
    "circuit_breaker": {
        "failure_threshold": 5,
        "success_threshold": 2,
        "timeout": 30.0,
        "half_open_max_calls": 3,
    },

    # Error classification
    "error_classification": {
        "enabled": True,
        "unknown_as_transient": False,
    },

    # OpenTelemetry configuration
    "opentelemetry": {
        "enabled": True,
        "console_export": True,
        "sampling": {"ratio": 1.0},
        "otlp": {
            "endpoint": "",
            "console_export": True,
        },
    },

    # Bookkeeping configuration
    "bookkeeping": {
        "request_tracking": {
            "enabled": True,
            "max_concurrent": 100,
            "timeout": 30.0,
            "collect_metrics": True,
        },
        "request_id": {
            "enabled": True,
            "format": "uuid4",
            "add_to_response": True,
        },
        "connection_tracking": {
            "enabled": True,
            "collect_metrics": True,
        },
    },

    # Middleware configuration
    "middleware": {
        "enabled": True,
        "order": [
            "request_id",
            "request_tracker",
            "opentelemetry",
            "connection_tracker",
        ],
    },
}

# Production preset - production-ready defaults
PRODUCTION_PRESET = {
    "environment": "production",
    "log_level": "INFO",
    "log_format": "json",

    # Health server
    "health_port": 8080,
    "health_path": "/healthz",
    "ready_path": "/ready",
    "metrics_path": "/metrics",

    # State management
    "state_backend": "configmap",
    "state_pvc_mount": "/data",

    # Lifecycle timeouts
    "startup_timeout_sec": 30,
    "shutdown_timeout_sec": 30,
    "health_check_interval_sec": 10,

    # Recovery
    "max_restart_attempts": 3,
    "restart_backoff_sec": 10,
    "golden_image_threshold": 5,

    # Metrics
    "metrics_enabled": True,
    "metrics_prefix": "dory",

    # Retry configuration
    "retry": {
        "max_attempts": 3,
        "initial_delay": 0.1,
        "multiplier": 2.0,
        "max_delay": 30.0,
        "jitter": True,
        "budget_percent": 20.0,
    },

    # Circuit breaker configuration
    "circuit_breaker": {
        "failure_threshold": 5,
        "success_threshold": 2,
        "timeout": 30.0,
        "half_open_max_calls": 3,
    },

    # Error classification
    "error_classification": {
        "enabled": True,
        "unknown_as_transient": False,
    },

    # OpenTelemetry configuration
    "opentelemetry": {
        "enabled": True,
        "console_export": False,
        "sampling": {"ratio": 0.1},  # Sample 10% in production
        "otlp": {
            "endpoint": "",
            "console_export": False,
        },
    },

    # Bookkeeping configuration
    "bookkeeping": {
        "request_tracking": {
            "enabled": True,
            "max_concurrent": 1000,
            "timeout": 30.0,
            "collect_metrics": True,
        },
        "request_id": {
            "enabled": True,
            "format": "uuid4",
            "add_to_response": True,
        },
        "connection_tracking": {
            "enabled": True,
            "collect_metrics": True,
        },
    },

    # Middleware configuration
    "middleware": {
        "enabled": True,
        "order": [
            "request_id",
            "request_tracker",
            "opentelemetry",
            "connection_tracker",
        ],
    },
}

# High-availability preset - aggressive fault tolerance
HIGH_AVAILABILITY_PRESET = {
    "environment": "production",
    "log_level": "INFO",
    "log_format": "json",

    # Health server
    "health_port": 8080,
    "health_path": "/healthz",
    "ready_path": "/ready",
    "metrics_path": "/metrics",

    # State management
    "state_backend": "pvc",  # More reliable than configmap
    "state_pvc_mount": "/data",

    # Lifecycle timeouts
    "startup_timeout_sec": 60,  # More time for startup
    "shutdown_timeout_sec": 60,  # More time for graceful shutdown
    "health_check_interval_sec": 5,  # More frequent checks

    # Recovery
    "max_restart_attempts": 5,  # More restart attempts
    "restart_backoff_sec": 15,  # Longer backoff
    "golden_image_threshold": 10,  # Higher threshold

    # Metrics
    "metrics_enabled": True,
    "metrics_prefix": "dory",

    # Retry configuration - more aggressive
    "retry": {
        "max_attempts": 5,  # More retries
        "initial_delay": 0.05,
        "multiplier": 1.5,
        "max_delay": 60.0,
        "jitter": True,
        "budget_percent": 30.0,  # Higher budget
    },

    # Circuit breaker configuration - more sensitive
    "circuit_breaker": {
        "failure_threshold": 3,  # Trip faster
        "success_threshold": 5,  # Need more successes to close
        "timeout": 60.0,  # Longer timeout
        "half_open_max_calls": 5,
    },

    # Error classification
    "error_classification": {
        "enabled": True,
        "unknown_as_transient": True,  # Retry unknown errors
    },

    # OpenTelemetry configuration
    "opentelemetry": {
        "enabled": True,
        "console_export": False,
        "sampling": {"ratio": 1.0},  # Full sampling for debugging
        "otlp": {
            "endpoint": "",
            "console_export": False,
        },
    },

    # Bookkeeping configuration
    "bookkeeping": {
        "request_tracking": {
            "enabled": True,
            "max_concurrent": 2000,
            "timeout": 60.0,
            "collect_metrics": True,
        },
        "request_id": {
            "enabled": True,
            "format": "uuid4",
            "add_to_response": True,
        },
        "connection_tracking": {
            "enabled": True,
            "collect_metrics": True,
        },
    },

    # Middleware configuration
    "middleware": {
        "enabled": True,
        "order": [
            "request_id",
            "request_tracker",
            "opentelemetry",
            "connection_tracker",
        ],
    },
}

PRESETS: Dict[str, Dict[str, Any]] = {
    "development": DEVELOPMENT_PRESET,
    "production": PRODUCTION_PRESET,
    "high-availability": HIGH_AVAILABILITY_PRESET,
}


def get_preset(name: str) -> Dict[str, Any]:
    """
    Get configuration preset by name.

    Args:
        name: Preset name (development, production, high-availability)

    Returns:
        Dictionary with preset configuration

    Raises:
        ValueError: If preset name is unknown
    """
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    return PRESETS[name].copy()


def list_presets() -> list[str]:
    """
    Get list of available preset names.

    Returns:
        List of preset names
    """
    return list(PRESETS.keys())
