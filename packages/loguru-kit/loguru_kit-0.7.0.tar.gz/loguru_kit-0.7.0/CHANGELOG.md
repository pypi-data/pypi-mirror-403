# Changelog

All notable changes to this project will be documented in this file.

## [0.5.0] - 2025-01-17

### Added
- Initial release
- `setup()` function with environment variable support
- `InterceptHandler` for stdlib logging interception
- `LoggingMiddleware` for FastAPI request/response logging
- OpenTelemetry trace context injection with `otel=True` option
- Environment variables: `LOGURU_LEVEL`, `LOGURU_JSON`, `LOGURU_INTERCEPT`, `LOGURU_TRUNCATE`, `LOGURU_OTEL`

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

Versions follow [Semantic Versioning](https://semver.org/) (Major.Minor.Patch).
