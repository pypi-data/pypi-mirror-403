"""Tests for stdlib logging intercept."""

from __future__ import annotations

import logging

import pytest

from loguru_kit.integrations.stdlib import InterceptHandler, intercept_stdlib


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging state after each test."""
    yield
    # Reset root logger
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(logging.WARNING)
    # Reset named loggers
    for name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
        logger.setLevel(logging.NOTSET)


class TestInterceptHandler:
    """Test InterceptHandler class."""

    def test_intercept_handler_is_handler(self):
        """Test that InterceptHandler is a logging.Handler."""
        handler = InterceptHandler()
        assert isinstance(handler, logging.Handler)

    def test_intercept_handler_has_emit(self):
        """Test that InterceptHandler has emit method."""
        handler = InterceptHandler()
        assert hasattr(handler, "emit")
        assert callable(handler.emit)


class TestInterceptSpecificLogger:
    """Test intercepting specific loggers."""

    def test_intercept_specific_logger(self):
        """Test intercepting a specific logger."""
        test_logger = logging.getLogger("test.specific")
        intercept_stdlib(loggers=["test.specific"])

        # Logger should have InterceptHandler
        assert len(test_logger.handlers) == 1
        assert isinstance(test_logger.handlers[0], InterceptHandler)

    def test_intercept_multiple_loggers(self):
        """Test intercepting multiple loggers."""
        intercept_stdlib(loggers=["logger1", "logger2"])

        logger1 = logging.getLogger("logger1")
        logger2 = logging.getLogger("logger2")

        assert len(logger1.handlers) == 1
        assert len(logger2.handlers) == 1


class TestInterceptNoSideEffects:
    """Test that intercept doesn't affect other loggers."""

    def test_other_logger_unaffected(self):
        """Test that non-intercepted loggers are unaffected."""
        other_logger = logging.getLogger("other.logger")
        initial_handlers = len(other_logger.handlers)

        intercept_stdlib(loggers=["intercepted.logger"])

        # Other logger should be unaffected
        assert len(other_logger.handlers) == initial_handlers

    def test_root_logger_unaffected(self):
        """Test that root logger is not modified."""
        root = logging.getLogger()
        initial_handlers = list(root.handlers)

        intercept_stdlib(loggers=["some.logger"])

        # Root logger should be unaffected
        assert root.handlers == initial_handlers
