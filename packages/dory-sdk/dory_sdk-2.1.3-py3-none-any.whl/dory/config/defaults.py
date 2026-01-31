"""Default configuration values for Dory SDK."""

from dory.types import StateBackend, LogFormat

# Security defaults
DEFAULT_RATE_LIMIT_RPS = 100  # Requests per second per client IP
DEFAULT_MAX_STATE_SIZE = 10 * 1024 * 1024  # 10MB for state transfers
DEFAULT_HEALTH_HOST = "0.0.0.0"  # Default bind address for health server

# Default configuration dictionary
DEFAULT_CONFIG = {
    # Lifecycle timeouts
    "startup_timeout_sec": 30,
    "shutdown_timeout_sec": 30,
    "health_check_interval_sec": 10,

    # Health server
    "health_port": 8080,
    "health_path": "/healthz",
    "ready_path": "/ready",
    "metrics_path": "/metrics",

    # State management
    "state_backend": StateBackend.CONFIGMAP.value,
    "state_pvc_mount": "/data",
    "state_s3_bucket": None,
    "state_s3_prefix": "dory-state",

    # Recovery
    "max_restart_attempts": 3,
    "restart_backoff_sec": 10,
    "golden_image_threshold": 3,

    # Logging
    "log_level": "INFO",
    "log_format": LogFormat.JSON.value,

    # Metrics
    "metrics_enabled": True,
    "metrics_prefix": "dory",
}


def get_default(key: str, default=None):
    """
    Get a default configuration value.

    Args:
        key: Configuration key
        default: Value to return if key not found

    Returns:
        Default value for the key
    """
    return DEFAULT_CONFIG.get(key, default)
