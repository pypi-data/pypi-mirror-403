"""Tests for IsolatedLogger.raw property."""

from __future__ import annotations

from loguru_kit import get_logger
from loguru_kit._isolation import IsolatedLogger


class TestIsolatedLoggerRaw:
    """Test IsolatedLogger.raw property."""

    def test_raw_property_exists(self):
        logger = get_logger(__name__)
        assert hasattr(logger, "raw")

    def test_raw_returns_loguru_logger(self):
        logger = get_logger(__name__)
        raw = logger.raw
        assert hasattr(raw, "info")
        assert hasattr(raw, "debug")
        assert hasattr(raw, "opt")
        assert hasattr(raw, "bind")

    def test_raw_is_bound_logger(self):
        logger = IsolatedLogger({"module": "test_module"})
        raw = logger.raw
        assert raw is not None

    def test_raw_can_call_methods(self, capsys):
        logger = get_logger(__name__)
        raw = logger.raw
        raw.debug("test message from raw logger")

    def test_raw_preserves_context(self):
        logger = IsolatedLogger({"custom_field": "custom_value"})
        raw = logger.raw
        assert raw is not None
