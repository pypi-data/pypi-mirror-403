"""Context management using contextvars for async-safe storage."""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Callable

# ContextVar to store the current context dictionary
_context_var: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "loguru_kit_context",
    default=None,
)


def _get_current() -> dict[str, Any]:
    """Get the current context dictionary (internal)."""
    ctx = _context_var.get()
    return ctx if ctx is not None else {}


def get_context() -> dict[str, Any]:
    """Get the current context dictionary.

    Returns:
        A copy of the current context dictionary
    """
    return _get_current().copy()


def set_context(**kwargs: Any) -> None:
    """Set context values.

    Merges the provided key-value pairs into the current context.

    Args:
        **kwargs: Context key-value pairs to set
    """
    current = _get_current()
    new_context = {**current, **kwargs}
    _context_var.set(new_context)


def clear_context() -> None:
    """Clear all context values."""
    _context_var.set({})


@contextmanager
def context_scope(**kwargs: Any):
    """Context manager for temporary context values.

    Values set within the scope are automatically removed when the scope exits.

    Args:
        **kwargs: Context key-value pairs for this scope

    Yields:
        None

    Example:
        >>> with context_scope(request_id="req-123"):
        ...     # request_id is available here
        ...     pass
        ... # request_id is removed here
    """
    # Save current context
    token = _context_var.set({**_get_current(), **kwargs})
    try:
        yield
    finally:
        # Restore previous context
        _context_var.reset(token)


def copy_context_to_thread[T](func: Callable[..., T]) -> Callable[..., T]:
    """Wrap a function to copy the current context to a thread.

    Use this when submitting functions to ThreadPoolExecutor
    to propagate the current context.

    Args:
        func: The function to wrap

    Returns:
        A wrapped function that copies context before execution

    Example:
        >>> def my_func():
        ...     ctx = get_context()
        ...     print(ctx)
        ...
        >>> with ThreadPoolExecutor() as executor:
        ...     executor.submit(copy_context_to_thread(my_func))
    """
    # Capture current context
    ctx = contextvars.copy_context()

    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Run function in the copied context
        return ctx.run(func, *args, **kwargs)

    return wrapper
