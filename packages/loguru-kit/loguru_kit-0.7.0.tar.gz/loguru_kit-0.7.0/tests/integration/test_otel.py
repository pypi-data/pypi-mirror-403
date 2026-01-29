"""Tests for OpenTelemetry integration."""

from __future__ import annotations

from loguru_kit.integrations.otel import create_otel_patcher, get_trace_context


class TestOtelPatcher:
    """Test OTEL patcher."""

    def test_patcher_returns_callable(self):
        """Test that create_otel_patcher returns a callable."""
        patcher = create_otel_patcher()
        assert callable(patcher)

    def test_patcher_adds_trace_fields(self):
        """Test that patcher adds trace_id and span_id."""
        patcher = create_otel_patcher()
        record = {"extra": {}}
        patcher(record)
        assert "trace_id" in record["extra"]
        assert "span_id" in record["extra"]

    def test_patcher_default_values_when_no_span(self):
        """Test that patcher uses '0' when no active span."""
        patcher = create_otel_patcher()
        record = {"extra": {}}
        patcher(record)
        # Without OTEL configured, should be "0"
        assert record["extra"]["trace_id"] == "0"
        assert record["extra"]["span_id"] == "0"


class TestGetTraceContext:
    """Test get_trace_context helper."""

    def test_get_trace_context_returns_dict(self):
        """Test that get_trace_context returns a dict."""
        ctx = get_trace_context()
        assert isinstance(ctx, dict)
        assert "trace_id" in ctx
        assert "span_id" in ctx

    def test_get_trace_context_default_values(self):
        """Test default values when no span."""
        ctx = get_trace_context()
        assert ctx["trace_id"] == "0"
        assert ctx["span_id"] == "0"


class TestOtelOptionalImport:
    """Test that OTEL is optional."""

    def test_import_without_otel_installed(self):
        """Test that module can be imported without opentelemetry."""
        # This test passes if the import doesn't raise
        from loguru_kit.integrations import otel

        assert otel is not None
