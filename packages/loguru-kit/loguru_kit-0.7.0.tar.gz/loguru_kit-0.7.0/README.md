# loguru-kit

Safe & extensible loguru setup with conflict-free isolation.

**Language:** [한국어](./README.ko.md) | English

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/bestend/loguru-kit/actions/workflows/tests.yml/badge.svg)](https://github.com/bestend/loguru-kit/actions/workflows/tests.yml)

## Installation

```bash
pip install loguru-kit
```

## Quick Start

```python
from loguru_kit import setup, get_logger

setup()
logger = get_logger(__name__)
logger.info("Hello, world!")
```

## Features

- **Conflict-free**: No `logger.remove()` - safe to use alongside other loguru users
- **Isolated loggers**: Each module gets its own context via `logger.bind()`
- **Async-safe**: contextvars-based context propagation
- **Simplified API**: One-line setup for common use cases (JSON, File, OTEL)
- **Integrations**: FastAPI middleware, OpenTelemetry, stdlib intercept

<details>
<summary>Configuration</summary>

### Parameters for `setup()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | `str` | `"INFO"` | Log level |
| `json` | `bool` | `False` | Enable JSON output |
| `truncate` | `int` | `10000` | Max message length |
| `file` | `str \| None` | `None` | File path for file logging |
| `rotation` | `str \| int \| None` | `None` | File rotation (e.g., "10 MB", "1 day") |
| `retention` | `str \| int \| None` | `None` | File retention (e.g., "7 days") |
| `intercept` | `list[str] \| None` | `None` | stdlib loggers to intercept |
| `otel` | `bool` | `False` | Enable OpenTelemetry trace injection |
| `force` | `bool` | `False` | Force reconfiguration |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGURU_KIT_LEVEL` | `INFO` | Log level |
| `LOGURU_KIT_JSON` | `false` | JSON output |

Priority: code > env > defaults
</details>

<details>
<summary>File Logging</summary>

```python
from loguru_kit import setup

setup(
    file="logs/app.log",
    rotation="10 MB",
    retention="7 days"
)
```
</details>

<details>
<summary>FastAPI Integration</summary>

```bash
pip install loguru-kit[fastapi]
```

```python
from fastapi import FastAPI
from loguru_kit import setup, get_logger
from loguru_kit.integrations.fastapi import LoggingMiddleware

setup()
app = FastAPI()
app.add_middleware(LoggingMiddleware, exclude_paths=["/healthz"])

logger = get_logger(__name__)

@app.get("/")
async def root():
    logger.info("Request received")
    return {"status": "ok"}
```
</details>

<details>
<summary>OpenTelemetry</summary>

```bash
pip install loguru-kit[otel]
```

```python
from loguru_kit import setup, get_logger

# Enable OTEL trace injection
setup(otel=True)
logger = get_logger(__name__)

logger.info("This log will have trace_id and span_id")
```
</details>

<details>
<summary>stdlib Intercept</summary>

```python
from loguru_kit import setup

# Intercept specific stdlib loggers
setup(intercept=["uvicorn", "sqlalchemy"])
```
</details>

## License

MIT License - See [LICENSE](./LICENSE) for details.
