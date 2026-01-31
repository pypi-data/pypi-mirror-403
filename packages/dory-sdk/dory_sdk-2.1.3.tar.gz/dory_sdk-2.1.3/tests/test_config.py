"""Tests for configuration loading."""

import pytest
from pathlib import Path

from dory.config.schema import DoryConfig
from dory.config.loader import ConfigLoader
from dory.config.defaults import DEFAULT_CONFIG
from dory.utils.errors import DoryConfigError


class TestDoryConfig:
    """Tests for DoryConfig schema."""

    def test_default_values(self):
        """Test that defaults are applied correctly."""
        config = DoryConfig()

        assert config.startup_timeout_sec == DEFAULT_CONFIG["startup_timeout_sec"]
        assert config.health_port == DEFAULT_CONFIG["health_port"]
        assert config.log_level == "INFO"

    def test_custom_values(self):
        """Test setting custom values."""
        config = DoryConfig(
            startup_timeout_sec=60,
            health_port=9090,
            log_level="DEBUG",
        )

        assert config.startup_timeout_sec == 60
        assert config.health_port == 9090
        assert config.log_level == "DEBUG"

    def test_invalid_state_backend(self):
        """Test that invalid state backend raises error."""
        with pytest.raises(ValueError):
            DoryConfig(state_backend="invalid_backend")

    def test_invalid_log_level(self):
        """Test that invalid log level raises error."""
        with pytest.raises(ValueError):
            DoryConfig(log_level="INVALID")

    def test_log_level_case_insensitive(self):
        """Test that log level is case insensitive."""
        config = DoryConfig(log_level="debug")
        assert config.log_level == "DEBUG"

    def test_invalid_port_range(self):
        """Test that invalid port raises error."""
        with pytest.raises(ValueError):
            DoryConfig(health_port=0)

        with pytest.raises(ValueError):
            DoryConfig(health_port=70000)

    def test_model_dump(self):
        """Test config can be dumped to dict."""
        config = DoryConfig()
        data = config.model_dump()

        assert "startup_timeout_sec" in data
        assert "health_port" in data


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_load_defaults(self):
        """Test loading with defaults only."""
        loader = ConfigLoader()
        config = loader.load()

        assert config.health_port == DEFAULT_CONFIG["health_port"]

    def test_load_from_env(self, monkeypatch):
        """Test loading from environment variables."""
        monkeypatch.setenv("DORY_HEALTH_PORT", "9000")
        monkeypatch.setenv("DORY_LOG_LEVEL", "DEBUG")

        loader = ConfigLoader()
        config = loader.load()

        assert config.health_port == 9000
        assert config.log_level == "DEBUG"

    def test_load_from_yaml(self, tmp_path):
        """Test loading from YAML file."""
        config_file = tmp_path / "dory.yaml"
        config_file.write_text("""
startup_timeout_sec: 45
health_port: 8888
log_level: WARNING
""")

        loader = ConfigLoader(config_file=str(config_file))
        config = loader.load()

        assert config.startup_timeout_sec == 45
        assert config.health_port == 8888
        assert config.log_level == "WARNING"

    def test_env_overrides_yaml(self, tmp_path, monkeypatch):
        """Test that environment variables override YAML."""
        config_file = tmp_path / "dory.yaml"
        config_file.write_text("health_port: 8888")

        monkeypatch.setenv("DORY_HEALTH_PORT", "9999")

        loader = ConfigLoader(config_file=str(config_file))
        config = loader.load()

        assert config.health_port == 9999

    def test_missing_config_file_error(self):
        """Test that missing config file raises error."""
        loader = ConfigLoader(config_file="/nonexistent/config.yaml")

        with pytest.raises(DoryConfigError) as exc_info:
            loader.load()

        assert "not found" in str(exc_info.value)

    def test_invalid_yaml_error(self, tmp_path):
        """Test that invalid YAML raises error."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        loader = ConfigLoader(config_file=str(config_file))

        with pytest.raises(DoryConfigError) as exc_info:
            loader.load()

        assert "Invalid YAML" in str(exc_info.value)

    def test_boolean_env_conversion(self, monkeypatch):
        """Test boolean environment variable conversion."""
        monkeypatch.setenv("DORY_METRICS_ENABLED", "false")

        loader = ConfigLoader()
        config = loader.load()

        assert config.metrics_enabled is False

        monkeypatch.setenv("DORY_METRICS_ENABLED", "true")
        config = loader.load()
        assert config.metrics_enabled is True
