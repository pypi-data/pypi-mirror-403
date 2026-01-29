"""loguru-kit: Dead simple loguru setup.

Example:
    >>> from loguru_kit import setup, get_logger
    >>> setup()
    >>> logger = get_logger(__name__)
    >>> logger.info("Hello, world!")
"""

from __future__ import annotations

from ._core import get_logger, setup

__all__ = [
    "setup",
    "get_logger",
]

__version__ = "0.7.0"  # Auto-updated by GitHub Actions when tag is pushed
