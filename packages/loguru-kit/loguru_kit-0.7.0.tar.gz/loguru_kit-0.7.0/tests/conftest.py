"""Shared fixtures for loguru-kit tests."""

from __future__ import annotations

import pytest
from loguru import logger


@pytest.fixture(autouse=True)
def reset_logger():
    """Reset loguru logger state before each test."""
    # Store original handlers
    original_handlers = logger._core.handlers.copy()

    yield

    # Restore original handlers after test
    logger._core.handlers = original_handlers


@pytest.fixture
def capture_logs(capsys):
    """Fixture to capture log output."""
    import sys

    handler_id = logger.add(sys.stderr, format="{level}: {message}")

    yield capsys

    logger.remove(handler_id)
