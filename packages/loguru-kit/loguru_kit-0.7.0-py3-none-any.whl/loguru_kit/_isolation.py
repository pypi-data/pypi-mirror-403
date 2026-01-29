"""Logger isolation strategy using loguru bind()."""

from __future__ import annotations

from typing import Any

from loguru import logger as _global_logger


class IsolatedLogger:
    """A logger instance isolated from global state using bind().

    This wraps loguru's logger.bind() to create isolated logger instances
    that don't pollute the global logger state.

    Attributes:
        _context: The bound context dictionary
        _logger: The underlying loguru logger with bound context
    """

    __slots__ = ("_context", "_logger")

    def __init__(self, context: dict[str, Any] | None = None):
        """Initialize an isolated logger.

        Args:
            context: Initial context to bind
        """
        self._context = context or {}
        # Use bind() to create an isolated instance
        self._logger = _global_logger.bind(**self._context)

    @property
    def raw(self) -> Any:
        """Access the underlying loguru logger.

        This provides escape hatch access to the raw loguru logger
        for advanced use cases not covered by IsolatedLogger.

        Returns:
            The underlying loguru Logger instance with bound context.

        Example:
            >>> logger = get_logger(__name__)
            >>> raw_logger = logger.raw
            >>> raw_logger.opt(colors=True).info("Colored message")
        """
        return self._logger

    def bind(self, **kwargs: Any) -> IsolatedLogger:
        """Bind additional context, returning a new IsolatedLogger.

        Args:
            **kwargs: Context key-value pairs to bind

        Returns:
            New IsolatedLogger with merged context
        """
        new_context = {**self._context, **kwargs}
        return IsolatedLogger(new_context)

    def opt(
        self,
        *,
        exception: bool | BaseException | tuple | None = None,
        record: bool = False,
        lazy: bool = False,
        colors: bool = False,
        raw: bool = False,
        capture: bool = True,
        depth: int = 0,
        ansi: bool = False,
    ) -> IsolatedLogger:
        """Return a logger with modified options.

        This is a proxy to loguru's opt() method.
        """
        # Create a new isolated logger that will use opt when logging
        new_logger = IsolatedLogger(self._context.copy())
        new_logger._logger = self._logger.opt(
            exception=exception,
            record=record,
            lazy=lazy,
            colors=colors,
            raw=raw,
            capture=capture,
            depth=depth,
            ansi=ansi,
        )
        return new_logger

    # Proxy logging methods
    def trace(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a TRACE message."""
        self._logger.trace(message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a DEBUG message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an INFO message."""
        self._logger.info(message, *args, **kwargs)

    def success(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a SUCCESS message."""
        self._logger.success(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a WARNING message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an ERROR message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a CRITICAL message."""
        self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception with ERROR level."""
        self._logger.exception(message, *args, **kwargs)

    def log(self, level: str | int, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a message at the specified level."""
        self._logger.log(level, message, *args, **kwargs)


def create_isolated_logger(**initial_context: Any) -> IsolatedLogger:
    """Create a new isolated logger with optional initial context.

    Args:
        **initial_context: Initial context key-value pairs

    Returns:
        A new IsolatedLogger instance

    Example:
        >>> logger = create_isolated_logger(module="mymodule")
        >>> logger.info("Hello")  # Will include module="mymodule" in context
    """
    return IsolatedLogger(initial_context)
