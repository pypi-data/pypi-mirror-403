"""Tests for public API exports."""

from __future__ import annotations


class TestPublicImports:
    """Test that all public APIs can be imported."""

    def test_import_setup(self):
        """Test that setup can be imported."""
        from loguru_kit import setup

        assert callable(setup)

    def test_import_get_logger(self):
        """Test that get_logger can be imported."""
        from loguru_kit import get_logger

        assert callable(get_logger)

    def test_version_exists(self):
        """Test that version attribute exists."""
        import loguru_kit

        assert hasattr(loguru_kit, "__version__")
        assert isinstance(loguru_kit.__version__, str)


class TestNoPrivateExports:
    """Test that private modules are not exported."""

    def test_no_underscore_in_all(self):
        """Test that __all__ doesn't contain underscore-prefixed names."""
        import loguru_kit

        if hasattr(loguru_kit, "__all__"):
            for name in loguru_kit.__all__:
                assert not name.startswith("_"), f"Private name {name} in __all__"

    def test_all_exports_exist(self):
        """Test that all items in __all__ actually exist."""
        import loguru_kit

        if hasattr(loguru_kit, "__all__"):
            for name in loguru_kit.__all__:
                assert hasattr(loguru_kit, name), f"{name} in __all__ but not in module"

    def test_only_setup_and_get_logger_exported(self):
        """Test that only setup and get_logger are in __all__."""
        import loguru_kit

        assert loguru_kit.__all__ == ["setup", "get_logger"]
