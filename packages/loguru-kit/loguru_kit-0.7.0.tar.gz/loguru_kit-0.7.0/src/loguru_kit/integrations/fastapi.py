"""FastAPI/Starlette middleware for loguru-kit."""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable

from loguru import logger

from .._context import context_scope, get_context


def get_request_id() -> str | None:
    """Get the current request ID from context.

    Returns:
        The request ID if set, None otherwise
    """
    ctx = get_context()
    return ctx.get("request_id")


class LoggingMiddleware:
    """ASGI middleware for request logging with context.

    Features:
    - Generates or extracts request ID
    - Sets request context using contextvars
    - Logs request/response with timing
    - Adds extra fields for log filtering (message_type, status_code, etc.)

    Example:
        >>> from fastapi import FastAPI
        >>> from loguru_kit.integrations.fastapi import LoggingMiddleware
        >>>
        >>> app = FastAPI()
        >>> app.add_middleware(LoggingMiddleware)

    Extra fields in logs:
        - message_type: "request" or "response"
        - method: HTTP method (GET, POST, etc.)
        - path: Request path
        - status_code: Response status code (response only)
        - duration_ms: Request duration in milliseconds (response only)
    """

    def __init__(
        self,
        app: Callable[..., Any],
        header_name: str = "X-Request-ID",
        log_request: bool = True,
        log_response: bool = True,
    ):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            header_name: Header name for request ID extraction
            log_request: Whether to log incoming requests
            log_response: Whether to log responses
        """
        self.app = app
        self.header_name = header_name.lower()
        self.log_request = log_request
        self.log_response = log_response

    async def __call__(
        self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract or generate request ID
        headers = dict(scope.get("headers", []))
        request_id = headers.get(self.header_name.encode(), b"").decode() or str(uuid.uuid4())

        # Get request info
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        start_time = time.perf_counter()
        status_code = 500  # Default in case of error

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        # Use context_scope to set request context
        with context_scope(request_id=request_id, method=method, path=path):
            # Log request with extra fields for filtering
            if self.log_request:
                logger.bind(
                    message_type="request",
                    method=method,
                    path=path,
                ).info(f"{method} {path}")

            try:
                await self.app(scope, receive, send_wrapper)
            finally:
                # Log response with extra fields including status_code
                if self.log_response:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    logger.bind(
                        message_type="response",
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=round(duration_ms, 2),
                    ).info(f"{method} {path} | {status_code} | {duration_ms:.0f}ms")
