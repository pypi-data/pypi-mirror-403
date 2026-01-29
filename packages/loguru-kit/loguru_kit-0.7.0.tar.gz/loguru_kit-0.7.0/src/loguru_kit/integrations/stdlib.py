"""Selective stdlib logging intercept for loguru-kit."""

from __future__ import annotations

import logging
from typing import Sequence

from loguru import logger


class InterceptHandler(logging.Handler):
    """Handler that intercepts stdlib logging and forwards to loguru.

    This handler captures log records from Python's standard logging
    module and forwards them to loguru.

    Args:
        exclude_messages: List of message substrings to filter out
    """

    def __init__(self, exclude_messages: Sequence[str] | None = None):
        """Initialize the handler.

        Args:
            exclude_messages: List of message substrings to filter out.
                              If a log message contains any of these strings,
                              it will not be forwarded to loguru.
        """
        super().__init__()
        self.exclude_messages = list(exclude_messages) if exclude_messages else []

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by forwarding to loguru.

        Args:
            record: The logging.LogRecord to emit
        """
        # Get the message first
        message = record.getMessage()

        # Filter out excluded messages
        for pattern in self.exclude_messages:
            if pattern in message:
                return

        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, message)


def intercept_stdlib(
    loggers: Sequence[str],
    level: str = "DEBUG",
    exclude_messages: Sequence[str] | None = None,
) -> None:
    """Intercept specific stdlib loggers and forward to loguru.

    This function selectively intercepts named loggers without
    affecting the root logger or other loggers.

    Args:
        loggers: List of logger names to intercept
        level: Minimum level to intercept (default: DEBUG)
        exclude_messages: List of message substrings to filter out.
                          Useful for filtering healthcheck logs, etc.

    Example:
        >>> from loguru_kit.integrations.stdlib import intercept_stdlib
        >>> intercept_stdlib(
        ...     loggers=["uvicorn", "sqlalchemy"],
        ...     exclude_messages=["GET /healthz", "GET /ready"]
        ... )
    """
    handler = InterceptHandler(exclude_messages=exclude_messages)

    for name in loggers:
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.handlers = [handler]
        stdlib_logger.setLevel(getattr(logging, level.upper(), logging.DEBUG))
        stdlib_logger.propagate = False
