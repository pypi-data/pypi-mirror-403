"""Tests for get_logger() function."""

from __future__ import annotations

import pytest

from loguru_kit._config import reset_config
from loguru_kit._core import get_logger, is_setup, reset_setup, setup
from loguru_kit._isolation import IsolatedLogger


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before each test."""
    reset_setup()
    reset_config()
    yield
    reset_setup()
    reset_config()


class TestGetLoggerWithName:
    """Test get_logger() with module name."""

    def test_get_logger_returns_isolated_logger(self):
        """Test that get_logger returns an IsolatedLogger."""
        logger = get_logger(__name__)
        assert isinstance(logger, IsolatedLogger)

    def test_get_logger_has_module_context(self):
        """Test that logger has module context bound."""
        logger = get_logger("my.module.name")
        assert logger._context.get("module") == "my.module.name"

    def test_get_logger_without_name(self):
        """Test get_logger without name uses default."""
        logger = get_logger()
        assert isinstance(logger, IsolatedLogger)
        # Should have some default or no module context
        assert "module" not in logger._context or logger._context.get("module") is None


class TestGetLoggerAutoSetup:
    """Test that get_logger auto-initializes if needed."""

    def test_get_logger_before_setup_auto_initializes(self):
        """Test that get_logger calls setup() if not initialized."""
        assert not is_setup()
        logger = get_logger(__name__)
        assert is_setup()  # Should have auto-initialized
        assert isinstance(logger, IsolatedLogger)

    def test_get_logger_after_setup_uses_existing(self):
        """Test that get_logger uses existing setup."""
        setup(level="DEBUG")
        assert is_setup()
        logger = get_logger(__name__)
        assert isinstance(logger, IsolatedLogger)


class TestGetLoggerTypeHints:
    """Test type hints for IDE autocomplete."""

    def test_logger_has_info_method(self):
        """Test that returned logger has info method."""
        logger = get_logger(__name__)
        assert hasattr(logger, "info")
        assert callable(logger.info)

    def test_logger_has_debug_method(self):
        """Test that returned logger has debug method."""
        logger = get_logger(__name__)
        assert hasattr(logger, "debug")
        assert callable(logger.debug)

    def test_logger_has_bind_method(self):
        """Test that returned logger has bind method."""
        logger = get_logger(__name__)
        assert hasattr(logger, "bind")
        bound = logger.bind(extra="value")
        assert isinstance(bound, IsolatedLogger)
