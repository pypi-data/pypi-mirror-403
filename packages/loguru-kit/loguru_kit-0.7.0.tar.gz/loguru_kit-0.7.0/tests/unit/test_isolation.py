"""Tests for logger isolation strategy."""

from __future__ import annotations

from loguru import logger as global_logger

from loguru_kit._isolation import create_isolated_logger


class TestIsolatedLoggerBind:
    """Test that IsolatedLogger properly binds context."""

    def test_isolated_logger_has_context(self):
        """Test that isolated logger has bound context."""
        isolated = create_isolated_logger(module="test_module")
        # Verify the context is bound
        assert isolated._context.get("module") == "test_module"

    def test_isolated_logger_bind_additional(self):
        """Test that additional context can be bound."""
        isolated = create_isolated_logger(module="test")
        bound = isolated.bind(user_id=123)
        assert bound._context.get("user_id") == 123
        assert bound._context.get("module") == "test"

    def test_bind_returns_new_instance(self):
        """Test that bind returns a new IsolatedLogger instance."""
        isolated = create_isolated_logger(module="test")
        bound = isolated.bind(extra="value")
        assert isolated is not bound
        assert "extra" not in isolated._context


class TestNoGlobalPollution:
    """Test that isolated logger doesn't pollute global state."""

    def test_global_logger_unaffected(self, capsys):
        """Test that global loguru logger is not modified."""
        # Get initial state of global logger
        initial_handlers = len(global_logger._core.handlers)

        # Create and use isolated logger
        _ = create_isolated_logger(module="isolated_test")

        # Global logger should be unaffected
        assert len(global_logger._core.handlers) == initial_handlers

    def test_multiple_isolated_loggers_independent(self):
        """Test that multiple isolated loggers are independent."""
        logger1 = create_isolated_logger(module="module1")
        logger2 = create_isolated_logger(module="module2")

        # Bind different context to each
        logger1_bound = logger1.bind(request_id="req1")
        logger2_bound = logger2.bind(request_id="req2")

        # They should have different contexts
        assert logger1_bound._context.get("module") == "module1"
        assert logger2_bound._context.get("module") == "module2"
        assert logger1_bound._context.get("request_id") == "req1"
        assert logger2_bound._context.get("request_id") == "req2"


class TestLoggerAPICompatibility:
    """Test that IsolatedLogger has compatible API with loguru logger."""

    def test_has_info_method(self):
        """Test that isolated logger has info method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "info")
        assert callable(isolated.info)

    def test_has_debug_method(self):
        """Test that isolated logger has debug method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "debug")
        assert callable(isolated.debug)

    def test_has_warning_method(self):
        """Test that isolated logger has warning method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "warning")
        assert callable(isolated.warning)

    def test_has_error_method(self):
        """Test that isolated logger has error method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "error")
        assert callable(isolated.error)

    def test_has_exception_method(self):
        """Test that isolated logger has exception method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "exception")
        assert callable(isolated.exception)

    def test_has_critical_method(self):
        """Test that isolated logger has critical method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "critical")
        assert callable(isolated.critical)

    def test_has_bind_method(self):
        """Test that isolated logger has bind method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "bind")
        assert callable(isolated.bind)

    def test_has_opt_method(self):
        """Test that isolated logger has opt method."""
        isolated = create_isolated_logger()
        assert hasattr(isolated, "opt")
        assert callable(isolated.opt)
