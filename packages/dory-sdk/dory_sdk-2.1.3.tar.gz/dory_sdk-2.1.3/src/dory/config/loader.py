"""
Configuration loader for Dory SDK.

Supports loading from:
1. YAML configuration file
2. Environment variables (DORY_ prefix)
3. Configuration presets
4. Auto-detection (service name, version, environment)
5. Default values
"""

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from dory.config.schema import DoryConfig
from dory.config.defaults import DEFAULT_CONFIG
from dory.config.presets import get_preset, list_presets, DEVELOPMENT_PRESET
from dory.utils.errors import DoryConfigError

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Smart configuration loader with:
    - Auto-detection of service name/version
    - Preset support (development, production, high-availability)
    - Zero-config mode
    - Progressive disclosure

    Priority order:
    1. Environment variables (highest)
    2. Config file
    3. Preset (if specified)
    4. Auto-detected defaults
    5. Default values (lowest)
    """

    ENV_PREFIX = "DORY_"
    DEFAULT_CONFIG_PATHS = [
        "/etc/dory/config.yaml",
        "/app/config/dory.yaml",
        "./dory.yaml",
    ]

    def __init__(self, config_file: str | None = None):
        """
        Initialize config loader.

        Args:
            config_file: Optional path to YAML config file
        """
        self._config_file = config_file

    def load(self) -> DoryConfig:
        """
        Load and validate configuration with smart defaults.

        Priority:
        1. Environment variables (DORY_*)
        2. Config file (dory.yaml)
        3. Preset (if specified)
        4. Auto-detected defaults
        5. Default values

        Returns:
            Validated DoryConfig instance

        Raises:
            DoryConfigError: If configuration is invalid
        """
        # Try to load config file
        file_config = self._load_from_file()

        # Determine which preset to use
        preset_name = self._determine_preset(file_config)

        # Start with preset or development defaults
        if preset_name in list_presets():
            config_dict = get_preset(preset_name)
            logger.info(f"Using configuration preset: {preset_name}")
        else:
            config_dict = DEVELOPMENT_PRESET.copy()
            if preset_name:
                logger.warning(f"Unknown preset '{preset_name}', using development defaults")
            else:
                logger.info("No preset specified, using development mode with auto-detection")

        # Auto-detect application info
        app_config = self._auto_detect_app_info(file_config.get("app", {}) if file_config else {})
        config_dict["app"] = app_config

        # Deep merge file config (overrides preset)
        if file_config:
            config_dict = self._deep_merge(config_dict, file_config)

        # Apply environment variable overrides (highest priority)
        env_config = self._load_from_env()
        config_dict = self._deep_merge(config_dict, env_config)

        # Validate and create config object
        try:
            config = DoryConfig(**config_dict)
            logger.info(f"Configuration loaded: {app_config.get('name', 'unknown')} v{app_config.get('version', 'unknown')}")
            logger.debug(f"Full configuration: {config.model_dump()}")
            return config
        except Exception as e:
            raise DoryConfigError(f"Invalid configuration: {e}", cause=e)

    def _load_from_file(self) -> dict[str, Any] | None:
        """Load configuration from YAML file."""
        config_path = self._find_config_file()

        if not config_path:
            logger.debug("No config file found, using defaults")
            return None

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

            logger.info(f"Loaded config from {config_path}")
            return config

        except yaml.YAMLError as e:
            raise DoryConfigError(f"Invalid YAML in {config_path}: {e}", cause=e)
        except Exception as e:
            raise DoryConfigError(f"Failed to read {config_path}: {e}", cause=e)

    def _find_config_file(self) -> Path | None:
        """Find config file from explicit path or default locations."""
        # Check explicit path first
        if self._config_file:
            path = Path(self._config_file)
            if path.exists():
                return path
            raise DoryConfigError(f"Config file not found: {self._config_file}")

        # Check environment variable
        env_path = os.environ.get("DORY_CONFIG_FILE")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            logger.warning(f"DORY_CONFIG_FILE set but not found: {env_path}")

        # Check default locations
        for default_path in self.DEFAULT_CONFIG_PATHS:
            path = Path(default_path)
            if path.exists():
                return path

        return None

    def _load_from_env(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        # Map of config keys to environment variable names
        env_mapping = {
            "startup_timeout_sec": "DORY_STARTUP_TIMEOUT_SEC",
            "shutdown_timeout_sec": "DORY_SHUTDOWN_TIMEOUT_SEC",
            "health_check_interval_sec": "DORY_HEALTH_CHECK_INTERVAL_SEC",
            "health_port": "DORY_HEALTH_PORT",
            "health_path": "DORY_HEALTH_PATH",
            "ready_path": "DORY_READY_PATH",
            "metrics_path": "DORY_METRICS_PATH",
            "state_backend": "DORY_STATE_BACKEND",
            "state_pvc_mount": "DORY_STATE_PVC_MOUNT",
            "state_s3_bucket": "DORY_STATE_S3_BUCKET",
            "state_s3_prefix": "DORY_STATE_S3_PREFIX",
            "max_restart_attempts": "DORY_MAX_RESTART_ATTEMPTS",
            "restart_backoff_sec": "DORY_RESTART_BACKOFF_SEC",
            "golden_image_threshold": "DORY_GOLDEN_IMAGE_THRESHOLD",
            "log_level": "DORY_LOG_LEVEL",
            "log_format": "DORY_LOG_FORMAT",
            "metrics_enabled": "DORY_METRICS_ENABLED",
            "metrics_prefix": "DORY_METRICS_PREFIX",
        }

        for config_key, env_var in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert to appropriate type
                config[config_key] = self._convert_env_value(config_key, value)

        return config

    def _convert_env_value(self, key: str, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Integer fields
        int_fields = {
            "startup_timeout_sec",
            "shutdown_timeout_sec",
            "health_check_interval_sec",
            "health_port",
            "max_restart_attempts",
            "restart_backoff_sec",
            "golden_image_threshold",
        }

        # Boolean fields
        bool_fields = {"metrics_enabled"}

        if key in int_fields:
            try:
                return int(value)
            except ValueError:
                raise DoryConfigError(f"Invalid integer for {key}: {value}")

        if key in bool_fields:
            return value.lower() in ("true", "1", "yes", "on")

        return value

    def _determine_preset(self, file_config: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Determine which preset to use.

        Priority:
        1. DORY_PRESET environment variable
        2. preset field in config file
        3. None (uses development preset)

        Args:
            file_config: Configuration loaded from file

        Returns:
            Preset name or None
        """
        # Check environment variable first
        preset = os.environ.get("DORY_PRESET")
        if preset:
            logger.debug(f"Preset from environment: {preset}")
            return preset

        # Check config file
        if file_config and "preset" in file_config:
            preset = file_config["preset"]
            logger.debug(f"Preset from config file: {preset}")
            return preset

        # No preset specified
        return None

    def _auto_detect_app_info(self, user_app: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-detect service name, version, and environment.

        Args:
            user_app: User-provided app configuration

        Returns:
            Dictionary with app configuration
        """
        app = {}

        # Auto-detect service name
        if "name" in user_app:
            app["name"] = user_app["name"]
        else:
            # Try to detect from directory name
            cwd = Path.cwd()
            app["name"] = cwd.name
            logger.debug(f"Auto-detected service name: {app['name']}")

        # Auto-detect version
        if "version" in user_app:
            app["version"] = user_app["version"]
        else:
            # Try to detect from git tag, pyproject.toml, or use default
            app["version"] = self._detect_version()
            logger.debug(f"Auto-detected version: {app['version']}")

        # Auto-detect environment
        if "environment" in user_app:
            app["environment"] = user_app["environment"]
        else:
            app["environment"] = os.environ.get("ENVIRONMENT", "development")
            logger.debug(f"Auto-detected environment: {app['environment']}")

        # Copy any other user-provided app config
        for key, value in user_app.items():
            if key not in app:
                app[key] = value

        return app

    def _detect_version(self) -> str:
        """
        Try to detect version from various sources.

        Returns:
            Version string
        """
        # Try git tag
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            logger.debug("Git not found, skipping git tag detection")
        except subprocess.TimeoutExpired:
            logger.debug("Git describe timed out")
        except subprocess.SubprocessError as e:
            logger.debug(f"Git describe failed: {e}")

        # Try pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            try:
                with open(pyproject_path) as f:
                    content = f.read()
                    # Simple regex to extract version
                    match = re.search(r'version\s*=\s*"([^"]+)"', content)
                    if match:
                        return match.group(1)
            except FileNotFoundError:
                logger.debug("pyproject.toml not found")
            except (OSError, IOError) as e:
                logger.debug(f"Failed to read pyproject.toml: {e}")

        # Try package.json (for Node.js projects)
        package_json_path = Path("package.json")
        if package_json_path.exists():
            try:
                with open(package_json_path) as f:
                    import json
                    data = json.load(f)
                    if "version" in data:
                        return data["version"]
            except FileNotFoundError:
                logger.debug("package.json not found")
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse package.json: {e}")
            except KeyError:
                logger.debug("No version field in package.json")
            except (OSError, IOError) as e:
                logger.debug(f"Failed to read package.json: {e}")

        # Default
        return "0.1.0-dev"

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary with override values

        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
