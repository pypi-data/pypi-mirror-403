"""Tests for setup() function."""

from __future__ import annotations

import warnings

import pytest

from loguru_kit._config import reset_config
from loguru_kit._core import is_setup, reset_setup, setup


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before each test."""
    reset_setup()
    reset_config()
    yield
    reset_setup()
    reset_config()


class TestSetupDefault:
    """Test default setup behavior."""

    def test_setup_initializes(self):
        """Test that setup() initializes the logger."""
        assert not is_setup()
        setup()
        assert is_setup()

    def test_setup_returns_none(self):
        """Test that setup() returns None."""
        result = setup()
        assert result is None


class TestSetupIdempotent:
    """Test setup() idempotency."""

    def test_setup_twice_warns(self):
        """Test that calling setup() twice emits a warning."""
        setup()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            setup()
            assert len(w) == 1
            assert "already initialized" in str(w[0].message).lower()

    def test_setup_twice_keeps_original(self):
        """Test that second setup() keeps original configuration."""
        setup(level="DEBUG")
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            setup(level="ERROR")  # This should be ignored
        # Original config should be kept (DEBUG)
        assert is_setup()

    def test_setup_force_reconfigures(self):
        """Test that setup(force=True) allows reconfiguration."""
        setup(level="DEBUG")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            setup(level="ERROR", force=True)
            # No warning when force=True
            assert len(w) == 0
        assert is_setup()

    def test_setup_force_no_warning(self):
        """Test that force=True does not emit warning."""
        setup()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            setup(force=True)
            assert len(w) == 0


class TestSetupWithConfig:
    """Test setup() with configuration options."""

    def test_setup_with_level(self):
        """Test setup with custom level."""
        setup(level="DEBUG")
        assert is_setup()

    def test_setup_with_json(self):
        """Test setup with JSON output."""
        setup(json=True)
        assert is_setup()

    def test_setup_with_truncate(self):
        """Test setup with custom truncate."""
        setup(truncate=1000)
        assert is_setup()


class TestSetupExtensionFailure:
    """Test graceful handling of extension failures."""

    def test_setup_with_file_logging(self):
        """Test that file logging can be configured."""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup(file=log_file, rotation="1 MB", retention="7 days")
            assert is_setup()
