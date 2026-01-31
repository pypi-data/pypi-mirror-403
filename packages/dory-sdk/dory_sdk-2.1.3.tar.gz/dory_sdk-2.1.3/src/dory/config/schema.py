"""
Configuration schema for Dory SDK.

Uses Pydantic for validation and type coercion.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from dory.types import StateBackend, LogFormat
from dory.config.defaults import (
    DEFAULT_CONFIG,
    DEFAULT_RATE_LIMIT_RPS,
    DEFAULT_MAX_STATE_SIZE,
    DEFAULT_HEALTH_HOST,
)


class DoryConfig(BaseModel):
    """
    Dory SDK configuration schema.

    All configuration can be set via:
    1. YAML config file
    2. Environment variables (DORY_ prefix)
    3. Constructor arguments
    """

    # Lifecycle timeouts
    startup_timeout_sec: int = Field(
        default=DEFAULT_CONFIG["startup_timeout_sec"],
        ge=1,
        le=300,
        description="Maximum time for startup in seconds",
    )
    shutdown_timeout_sec: int = Field(
        default=DEFAULT_CONFIG["shutdown_timeout_sec"],
        ge=1,
        le=300,
        description="Maximum time for shutdown in seconds",
    )
    health_check_interval_sec: int = Field(
        default=DEFAULT_CONFIG["health_check_interval_sec"],
        ge=1,
        le=60,
        description="Interval between health checks",
    )

    # Health server
    health_port: int = Field(
        default=DEFAULT_CONFIG["health_port"],
        ge=1,
        le=65535,
        description="Port for health/metrics HTTP server",
    )
    health_host: str = Field(
        default=DEFAULT_HEALTH_HOST,
        description="Host address to bind health server (env: DORY_HEALTH_HOST)",
    )
    health_path: str = Field(
        default=DEFAULT_CONFIG["health_path"],
        description="Path for liveness probe",
    )
    ready_path: str = Field(
        default=DEFAULT_CONFIG["ready_path"],
        description="Path for readiness probe",
    )
    metrics_path: str = Field(
        default=DEFAULT_CONFIG["metrics_path"],
        description="Path for Prometheus metrics",
    )

    # State management
    state_backend: str = Field(
        default=DEFAULT_CONFIG["state_backend"],
        description="Backend for state persistence",
    )
    state_pvc_mount: str = Field(
        default=DEFAULT_CONFIG["state_pvc_mount"],
        description="Mount path for PVC state backend",
    )
    state_s3_bucket: Optional[str] = Field(
        default=DEFAULT_CONFIG["state_s3_bucket"],
        description="S3 bucket for state (if using S3 backend)",
    )
    state_s3_prefix: str = Field(
        default=DEFAULT_CONFIG["state_s3_prefix"],
        description="S3 key prefix for state objects",
    )

    # Recovery
    max_restart_attempts: int = Field(
        default=DEFAULT_CONFIG["max_restart_attempts"],
        ge=1,
        le=10,
        description="Max restarts before golden image reset",
    )
    restart_backoff_sec: int = Field(
        default=DEFAULT_CONFIG["restart_backoff_sec"],
        ge=0,
        le=300,
        description="Backoff delay between restarts",
    )
    golden_image_threshold: int = Field(
        default=DEFAULT_CONFIG["golden_image_threshold"],
        ge=1,
        le=10,
        description="Restart count triggering golden image reset",
    )

    # Logging
    log_level: str = Field(
        default=DEFAULT_CONFIG["log_level"],
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    log_format: str = Field(
        default=DEFAULT_CONFIG["log_format"],
        description="Log format (json or text)",
    )

    # Metrics
    metrics_enabled: bool = Field(
        default=DEFAULT_CONFIG["metrics_enabled"],
        description="Enable Prometheus metrics",
    )
    metrics_prefix: str = Field(
        default=DEFAULT_CONFIG["metrics_prefix"],
        description="Prefix for metric names",
    )

    # Security
    state_token: Optional[str] = Field(
        default=None,
        description="Token for authenticating state transfer requests (env: DORY_STATE_TOKEN)",
    )
    rate_limit_rps: int = Field(
        default=DEFAULT_RATE_LIMIT_RPS,
        ge=0,
        description="Rate limit in requests per second (0 to disable, env: DORY_RATE_LIMIT)",
    )
    max_state_size: int = Field(
        default=DEFAULT_MAX_STATE_SIZE,
        ge=1024,
        description="Maximum state payload size in bytes (env: DORY_MAX_STATE_SIZE)",
    )

    @field_validator("state_backend")
    @classmethod
    def validate_state_backend(cls, v: str) -> str:
        """Validate state backend value."""
        valid_backends = [b.value for b in StateBackend]
        if v not in valid_backends:
            raise ValueError(f"state_backend must be one of {valid_backends}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = [f.value for f in LogFormat]
        if v not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v

    model_config = {
        "extra": "ignore",  # Ignore unknown fields
    }
