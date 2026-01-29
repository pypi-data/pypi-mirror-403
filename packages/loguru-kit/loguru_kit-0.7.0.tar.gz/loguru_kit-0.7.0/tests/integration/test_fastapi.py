"""Tests for FastAPI middleware."""

from __future__ import annotations

import pytest

# Skip if starlette not installed
pytest.importorskip("starlette")

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from loguru_kit._context import clear_context, get_context
from loguru_kit.integrations.fastapi import LoggingMiddleware


@pytest.fixture
def app():
    """Create test Starlette app."""

    def homepage(request):
        return PlainTextResponse("OK")

    def get_context_route(request):
        ctx = get_context()
        return PlainTextResponse(f"request_id={ctx.get('request_id', 'none')}")

    routes = [
        Route("/", homepage),
        Route("/context", get_context_route),
    ]

    app = Starlette(routes=routes)
    app.add_middleware(LoggingMiddleware)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_context():
    """Clear context before each test."""
    clear_context()
    yield
    clear_context()


class TestMiddlewareRequestLogging:
    """Test request/response logging."""

    def test_middleware_allows_request(self, client):
        """Test that middleware allows requests through."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "OK"

    def test_middleware_handles_404(self, client):
        """Test that middleware handles 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404


class TestMiddlewareRequestId:
    """Test request ID generation."""

    def test_middleware_generates_request_id(self, client):
        """Test that middleware generates request_id."""
        response = client.get("/context")
        assert response.status_code == 200
        # Should have a request_id
        assert "request_id=" in response.text
        assert response.text != "request_id=none"

    def test_middleware_uses_provided_request_id(self, client):
        """Test that middleware uses X-Request-ID header if provided."""
        custom_id = "custom-request-123"
        response = client.get("/context", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert f"request_id={custom_id}" in response.text


class TestMiddlewareAsyncContext:
    """Test async context propagation."""

    def test_context_available_in_route(self, client):
        """Test that context is available in route handler."""
        response = client.get("/context")
        assert response.status_code == 200
        # request_id should be set
        assert "request_id=" in response.text
        assert "none" not in response.text
