"""Tests for stdlib intercept extended features."""

from __future__ import annotations

import logging

from loguru_kit.integrations.stdlib import InterceptHandler, intercept_stdlib


class TestInterceptHandlerExcludeMessages:
    """Test InterceptHandler exclude_messages feature."""

    def test_exclude_messages_attribute(self):
        handler = InterceptHandler(exclude_messages=["GET /healthz"])
        assert handler.exclude_messages == ["GET /healthz"]

    def test_exclude_messages_empty_by_default(self):
        handler = InterceptHandler()
        assert handler.exclude_messages == []

    def test_exclude_multiple_messages(self):
        patterns = ["GET /healthz", "GET /ready", "HEAD /ping"]
        handler = InterceptHandler(exclude_messages=patterns)
        assert handler.exclude_messages == patterns


class TestInterceptStdlibExcludeMessages:
    """Test intercept_stdlib with exclude_messages."""

    def test_intercept_with_exclude_messages(self):
        test_logger_name = "test_exclude_logger"
        intercept_stdlib(
            loggers=[test_logger_name],
            exclude_messages=["GET /healthz"],
        )

        test_logger = logging.getLogger(test_logger_name)
        assert len(test_logger.handlers) == 1
        handler = test_logger.handlers[0]
        assert isinstance(handler, InterceptHandler)
        assert handler.exclude_messages == ["GET /healthz"]

    def test_intercept_without_exclude_messages(self):
        test_logger_name = "test_no_exclude_logger"
        intercept_stdlib(loggers=[test_logger_name])

        test_logger = logging.getLogger(test_logger_name)
        handler = test_logger.handlers[0]
        assert isinstance(handler, InterceptHandler)
        assert handler.exclude_messages == []

    def test_shared_handler_for_multiple_loggers(self):
        logger_names = ["shared_logger_1", "shared_logger_2"]
        intercept_stdlib(
            loggers=logger_names,
            exclude_messages=["pattern1", "pattern2"],
        )

        for name in logger_names:
            test_logger = logging.getLogger(name)
            handler = test_logger.handlers[0]
            assert handler.exclude_messages == ["pattern1", "pattern2"]
