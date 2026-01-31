"""Configuration loading and schema definitions."""

from dory.config.schema import DoryConfig
from dory.config.loader import ConfigLoader
from dory.config.defaults import DEFAULT_CONFIG
from dory.config.presets import (
    get_preset,
    list_presets,
    DEVELOPMENT_PRESET,
    PRODUCTION_PRESET,
    HIGH_AVAILABILITY_PRESET,
)

__all__ = [
    "DoryConfig",
    "ConfigLoader",
    "DEFAULT_CONFIG",
    "get_preset",
    "list_presets",
    "DEVELOPMENT_PRESET",
    "PRODUCTION_PRESET",
    "HIGH_AVAILABILITY_PRESET",
]
