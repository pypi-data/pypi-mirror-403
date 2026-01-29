"""Tests for FastAPI middleware extended features."""

from __future__ import annotations

import pytest

pytest.importorskip("starlette")

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from loguru_kit._context import clear_context
from loguru_kit.integrations.fastapi import LoggingMiddleware


@pytest.fixture
def app_with_options():
    def homepage(request):
        return PlainTextResponse("OK")

    routes = [Route("/", homepage)]

    app = Starlette(routes=routes)
    app.add_middleware(LoggingMiddleware, log_request=True, log_response=True)
    return app


@pytest.fixture
def app_no_request_log():
    def homepage(request):
        return PlainTextResponse("OK")

    routes = [Route("/", homepage)]

    app = Starlette(routes=routes)
    app.add_middleware(LoggingMiddleware, log_request=False, log_response=True)
    return app


@pytest.fixture
def app_no_response_log():
    def homepage(request):
        return PlainTextResponse("OK")

    routes = [Route("/", homepage)]

    app = Starlette(routes=routes)
    app.add_middleware(LoggingMiddleware, log_request=True, log_response=False)
    return app


@pytest.fixture(autouse=True)
def clean_context():
    clear_context()
    yield
    clear_context()


class TestMiddlewareLogOptions:
    """Test middleware log_request and log_response options."""

    def test_middleware_with_all_logging(self, app_with_options):
        client = TestClient(app_with_options)
        response = client.get("/")
        assert response.status_code == 200

    def test_middleware_without_request_log(self, app_no_request_log):
        client = TestClient(app_no_request_log)
        response = client.get("/")
        assert response.status_code == 200

    def test_middleware_without_response_log(self, app_no_response_log):
        client = TestClient(app_no_response_log)
        response = client.get("/")
        assert response.status_code == 200


class TestMiddlewareExtraFields:
    """Test that middleware adds extra fields for filtering."""

    def test_middleware_allows_request_with_extra_fields(self, app_with_options):
        client = TestClient(app_with_options)
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "OK"
