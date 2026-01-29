"""Tests for configuration management."""

from __future__ import annotations

import pytest

from loguru_kit._config import LoguruKitConfig, get_config, reset_config


class TestLoguruKitConfig:
    """Test LoguruKitConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LoguruKitConfig()
        assert config.level == "INFO"
        assert config.json is False
        assert config.truncate == 5000
        assert config.intercept_stdlib is True
        assert config.otel is False

    def test_custom_config(self):
        """Test custom configuration values."""
        config = LoguruKitConfig(level="DEBUG", json=True, truncate=1000)
        assert config.level == "DEBUG"
        assert config.json is True
        assert config.truncate == 1000


class TestEnvOverride:
    """Test environment variable overrides."""

    def test_env_override_level(self, monkeypatch):
        """Test LOGURU_KIT_LEVEL env var."""
        monkeypatch.setenv("LOGURU_KIT_LEVEL", "DEBUG")
        reset_config()
        config = get_config()
        assert config.level == "DEBUG"

    def test_env_override_json(self, monkeypatch):
        """Test LOGURU_KIT_JSON env var."""
        monkeypatch.setenv("LOGURU_KIT_JSON", "true")
        reset_config()
        config = get_config()
        assert config.json is True

    def test_env_override_truncate(self, monkeypatch):
        """Test LOGURU_KIT_TRUNCATE env var."""
        monkeypatch.setenv("LOGURU_KIT_TRUNCATE", "2000")
        reset_config()
        config = get_config()
        assert config.truncate == 2000

    def test_code_args_override_env(self, monkeypatch):
        """Test that code arguments take precedence over env vars."""
        monkeypatch.setenv("LOGURU_KIT_LEVEL", "DEBUG")
        reset_config()
        config = get_config(level="ERROR")
        assert config.level == "ERROR"


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_level(self):
        """Test invalid log level raises error."""
        with pytest.raises(ValueError, match="Invalid log level"):
            LoguruKitConfig(level="INVALID")

    def test_invalid_truncate(self):
        """Test negative truncate raises error."""
        with pytest.raises(ValueError, match="truncate must be positive"):
            LoguruKitConfig(truncate=-1)
