"""Core setup functionality for loguru-kit."""

from __future__ import annotations

import sys
import warnings
from typing import Any

from loguru import logger

from ._config import get_config
from ._isolation import IsolatedLogger, create_isolated_logger

# Module-level state
_setup_done: bool = False


def is_setup() -> bool:
    """Check if setup() has been called.

    Returns:
        True if setup() has been called, False otherwise
    """
    return _setup_done


def reset_setup() -> None:
    """Reset setup state.

    Useful for testing. Does NOT reset the underlying loguru configuration.
    """
    global _setup_done
    _setup_done = False


def setup(
    *,
    level: str = "INFO",
    json: bool = False,
    truncate: int = 10000,
    file: str | None = None,
    rotation: str | int | None = None,
    retention: str | int | None = None,
    intercept: list[str] | None = None,
    otel: bool = False,
    force: bool = False,
) -> None:
    """Initialize loguru-kit logging.

    This function is idempotent - calling it multiple times will emit a warning
    and keep the original configuration. Use force=True to override.

    Args:
        level: Log level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL). Default: INFO
        json: Enable JSON output format. Default: False
        truncate: Maximum message length before truncation. Default: 10000
        file: Optional file path for file logging
        rotation: File rotation policy (e.g., "10 MB", "00:00", 1000000)
        retention: File retention policy (e.g., "7 days", 10)
        intercept: List of stdlib logger names to intercept (e.g., ["uvicorn", "sqlalchemy"])
        otel: Enable OpenTelemetry trace injection. Default: False
        force: Force reconfiguration even if already initialized

    Example:
        >>> from loguru_kit import setup
        >>> setup(level="DEBUG", json=True)
        >>> setup(file="logs/app.log", rotation="10 MB", retention="7 days")
        >>> # Later, force reconfigure
        >>> setup(level="INFO", force=True)
    """
    global _setup_done

    # Idempotency check (skip if force=True)
    if _setup_done and not force:
        warnings.warn(
            "loguru-kit is already initialized. Use setup(force=True) to reconfigure.",
            UserWarning,
            stacklevel=2,
        )
        return

    # Build configuration with overrides
    overrides: dict[str, Any] = {
        "level": level,
        "json": json,
        "truncate": truncate,
    }

    config = get_config(**overrides)

    # Build format string
    def formatter(record: dict) -> str:
        """Format log record with truncation."""
        msg = record["message"]
        if len(msg) > config.truncate:
            record["message"] = msg[: config.truncate] + "..."
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>\n{exception}"
        )

    # Configure handlers
    handler_configs: list[dict[str, Any]] = [
        {
            "sink": sys.stderr,
            "level": config.level,
            "format": formatter,
            "serialize": config.json,
            "backtrace": True,
            "diagnose": True,
        }
    ]

    # Add file sink if file path is provided
    if file:
        file_config: dict[str, Any] = {
            "sink": file,
            "level": config.level,
            "format": formatter,
            "serialize": config.json,
        }
        if rotation is not None:
            file_config["rotation"] = rotation
        if retention is not None:
            file_config["retention"] = retention
        handler_configs.append(file_config)

    # Apply configuration using logger.configure()
    # This replaces all existing handlers
    logger.configure(handlers=handler_configs)  # type: ignore[arg-type]

    # Configure intercept_stdlib if requested
    if intercept:
        from .integrations.stdlib import intercept_stdlib

        intercept_stdlib(loggers=intercept)

    # Configure OTEL patcher if requested
    if otel:
        try:
            from .integrations.otel import create_otel_patcher

            patcher = create_otel_patcher()
            logger.configure(patcher=patcher)  # type: ignore[arg-type]
        except ImportError:
            warnings.warn(
                "OpenTelemetry not installed, otel=True ignored",
                UserWarning,
                stacklevel=2,
            )

    _setup_done = True


def get_logger(name: str | None = None) -> IsolatedLogger:
    """Get an isolated logger with optional module context.

    If setup() has not been called, this will automatically call setup()
    with default configuration.

    Args:
        name: Module name to bind as context (typically __name__)

    Returns:
        An IsolatedLogger instance with module context bound

    Example:
        >>> from loguru_kit import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello from my module!")
    """
    # Auto-initialize if not setup
    if not _setup_done:
        setup()

    # Create isolated logger with module context
    if name is not None:
        return create_isolated_logger(module=name)
    return create_isolated_logger()
