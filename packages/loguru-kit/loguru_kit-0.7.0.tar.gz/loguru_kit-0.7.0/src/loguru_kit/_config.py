"""Configuration management for loguru-kit."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

# Valid log levels
VALID_LEVELS = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}

# Module-level config storage (isolated from global state)
_config: LoguruKitConfig | None = None
_initialized: bool = False


def _env_str(key: str, default: str) -> str:
    """Get string from environment variable."""
    return os.getenv(key, default)


def _env_bool(key: str, default: bool) -> bool:
    """Get boolean from environment variable."""
    val = os.getenv(key, "").lower()
    if val in ("true", "1", "yes", "on"):
        return True
    if val in ("false", "0", "no", "off"):
        return False
    return default


def _env_int(key: str, default: int) -> int:
    """Get integer from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


@dataclass
class LoguruKitConfig:
    """Configuration for loguru-kit.

    Attributes:
        level: Log level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        json: Enable JSON output format
        truncate: Maximum message length before truncation
        intercept_stdlib: Intercept stdlib logging
        otel: Enable OpenTelemetry trace injection
    """

    level: str = "INFO"
    json: bool = False
    truncate: int = 5000
    intercept_stdlib: bool = True
    otel: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.level = self.level.upper()
        if self.level not in VALID_LEVELS:
            raise ValueError(f"Invalid log level: {self.level}. Must be one of {VALID_LEVELS}")
        if self.truncate < 0:
            raise ValueError("truncate must be positive")


def get_config(**overrides: Any) -> LoguruKitConfig:
    """Get the current configuration, applying any overrides.

    Priority: code args > env vars > defaults

    Args:
        **overrides: Configuration overrides

    Returns:
        LoguruKitConfig instance
    """
    global _config, _initialized

    # Build config from env vars if not initialized
    if not _initialized:
        _config = LoguruKitConfig(
            level=_env_str("LOGURU_KIT_LEVEL", "INFO"),
            json=_env_bool("LOGURU_KIT_JSON", False),
            truncate=_env_int("LOGURU_KIT_TRUNCATE", 5000),
            intercept_stdlib=_env_bool("LOGURU_KIT_INTERCEPT", True),
            otel=_env_bool("LOGURU_KIT_OTEL", False),
        )
        _initialized = True

    # Apply overrides if provided
    if overrides and _config is not None:
        config_dict = {
            "level": overrides.get("level", _config.level),
            "json": overrides.get("json", _config.json),
            "truncate": overrides.get("truncate", _config.truncate),
            "intercept_stdlib": overrides.get("intercept_stdlib", _config.intercept_stdlib),
            "otel": overrides.get("otel", _config.otel),
        }
        return LoguruKitConfig(**config_dict)

    # _config is guaranteed to be set after initialization
    assert _config is not None
    return _config


def reset_config() -> None:
    """Reset configuration to uninitialized state.

    Useful for testing and reconfiguration.
    """
    global _config, _initialized
    _config = None
    _initialized = False
