"""OpenTelemetry integration for loguru-kit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

# Try to import opentelemetry, but make it optional
try:
    from opentelemetry.trace import (
        INVALID_SPAN,
        INVALID_SPAN_CONTEXT,
        get_current_span,
        get_tracer_provider,
    )

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    # Dummy values for type checking
    if TYPE_CHECKING:
        from opentelemetry.trace import (
            INVALID_SPAN,
            INVALID_SPAN_CONTEXT,
            get_current_span,
            get_tracer_provider,
        )

# Cached service name (resolved once)
_cached_service_name: str | None = None


def _get_service_name() -> str:
    """Get service name from OpenTelemetry tracer provider resource.

    Returns:
        Service name or empty string if not available.
    """
    global _cached_service_name

    if _cached_service_name is not None:
        return _cached_service_name

    if not _OTEL_AVAILABLE:
        _cached_service_name = ""
        return _cached_service_name

    try:
        provider = get_tracer_provider()
        resource = getattr(provider, "resource", None)
        if resource:
            _cached_service_name = str(resource.attributes.get("service.name", "") or "")
        else:
            _cached_service_name = ""
    except Exception:
        _cached_service_name = ""

    return _cached_service_name or ""


def get_trace_context(
    *,
    include_sampled: bool = False,
    include_service_name: bool = False,
) -> dict[str, str | bool]:
    """Get current trace context.

    Args:
        include_sampled: Include trace_sampled field (whether trace is sampled)
        include_service_name: Include service_name field from OTEL resource

    Returns:
        Dictionary with trace_id, span_id, and optionally trace_sampled, service_name.
        Returns "0" for trace/span IDs if no active span or OTEL not installed.

    Example:
        >>> ctx = get_trace_context(include_sampled=True, include_service_name=True)
        >>> # {"trace_id": "abc...", "span_id": "def...", "trace_sampled": True, "service_name": "my-service"}
    """
    result: dict[str, str | bool] = {"trace_id": "0", "span_id": "0"}

    if include_sampled:
        result["trace_sampled"] = False
    if include_service_name:
        result["service_name"] = _get_service_name()

    if not _OTEL_AVAILABLE:
        return result

    span = get_current_span()
    if span == INVALID_SPAN:
        return result

    ctx = span.get_span_context()
    if ctx == INVALID_SPAN_CONTEXT:
        return result

    result["trace_id"] = format(ctx.trace_id, "032x")
    result["span_id"] = format(ctx.span_id, "016x")

    if include_sampled:
        result["trace_sampled"] = ctx.trace_flags.sampled

    return result


def create_otel_patcher(
    *,
    include_sampled: bool = False,
    include_service_name: bool = False,
) -> Callable[[dict[str, Any]], None]:
    """Create a loguru patcher that injects OTEL trace context.

    Args:
        include_sampled: Include trace_sampled field in logs
        include_service_name: Include service_name field in logs

    Returns:
        A patcher function for use with logger.configure(patcher=...)

    Example:
        >>> from loguru import logger
        >>> from loguru_kit.integrations.otel import create_otel_patcher
        >>> logger.configure(patcher=create_otel_patcher(include_sampled=True))
    """

    def patcher(record: dict[str, Any]) -> None:
        """Inject trace context into log record."""
        trace_ctx = get_trace_context(
            include_sampled=include_sampled,
            include_service_name=include_service_name,
        )
        record["extra"]["trace_id"] = trace_ctx["trace_id"]
        record["extra"]["span_id"] = trace_ctx["span_id"]

        if include_sampled:
            record["extra"]["trace_sampled"] = trace_ctx["trace_sampled"]
        if include_service_name:
            record["extra"]["service_name"] = trace_ctx["service_name"]

    return patcher


def reset_service_name_cache() -> None:
    """Reset cached service name. Useful for testing."""
    global _cached_service_name
    _cached_service_name = None
