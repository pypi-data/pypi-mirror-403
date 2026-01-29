"""Tests for OpenTelemetry extended features."""

from __future__ import annotations

from loguru_kit.integrations.otel import (
    create_otel_patcher,
    get_trace_context,
    reset_service_name_cache,
)


class TestGetTraceContextExtended:
    """Test get_trace_context with extended options."""

    def test_include_sampled_false_by_default(self):
        ctx = get_trace_context()
        assert "trace_sampled" not in ctx

    def test_include_sampled_when_requested(self):
        ctx = get_trace_context(include_sampled=True)
        assert "trace_sampled" in ctx
        assert ctx["trace_sampled"] is False

    def test_include_service_name_false_by_default(self):
        ctx = get_trace_context()
        assert "service_name" not in ctx

    def test_include_service_name_when_requested(self):
        reset_service_name_cache()
        ctx = get_trace_context(include_service_name=True)
        assert "service_name" in ctx
        assert isinstance(ctx["service_name"], str)

    def test_include_all_fields(self):
        reset_service_name_cache()
        ctx = get_trace_context(include_sampled=True, include_service_name=True)
        assert "trace_id" in ctx
        assert "span_id" in ctx
        assert "trace_sampled" in ctx
        assert "service_name" in ctx


class TestCreateOtelPatcherExtended:
    """Test create_otel_patcher with extended options."""

    def test_patcher_with_sampled(self):
        patcher = create_otel_patcher(include_sampled=True)
        record = {"extra": {}}
        patcher(record)
        assert "trace_sampled" in record["extra"]
        assert record["extra"]["trace_sampled"] is False

    def test_patcher_with_service_name(self):
        reset_service_name_cache()
        patcher = create_otel_patcher(include_service_name=True)
        record = {"extra": {}}
        patcher(record)
        assert "service_name" in record["extra"]

    def test_patcher_with_all_options(self):
        reset_service_name_cache()
        patcher = create_otel_patcher(include_sampled=True, include_service_name=True)
        record = {"extra": {}}
        patcher(record)
        assert "trace_id" in record["extra"]
        assert "span_id" in record["extra"]
        assert "trace_sampled" in record["extra"]
        assert "service_name" in record["extra"]

    def test_patcher_without_options(self):
        patcher = create_otel_patcher()
        record = {"extra": {}}
        patcher(record)
        assert "trace_id" in record["extra"]
        assert "span_id" in record["extra"]
        assert "trace_sampled" not in record["extra"]
        assert "service_name" not in record["extra"]
