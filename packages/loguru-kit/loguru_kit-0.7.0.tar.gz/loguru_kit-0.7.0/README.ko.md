# loguru-kit

충돌 없는 안전하고 확장 가능한 loguru 설정 kit.

**Language:** 한국어 | [English](./README.md)

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/bestend/loguru-kit/actions/workflows/tests.yml/badge.svg)](https://github.com/bestend/loguru-kit/actions/workflows/tests.yml)

## 설치

```bash
pip install loguru-kit
```

## 빠른 시작

```python
from loguru_kit import setup, get_logger

setup()
logger = get_logger(__name__)
logger.info("Hello, world!")
```

## 특징

- **충돌 없음**: `logger.remove()` 미사용 - 다른 loguru 사용자와 안전하게 공존
- **격리된 로거**: 각 모듈이 `logger.bind()`를 통해 자체 컨텍스트 보유
- **비동기 안전**: contextvars 기반 컨텍스트 전파
- **단순화된 API**: 일반적인 유스케이스(JSON, File, OTEL)를 위한 한 줄 설정
- **통합**: FastAPI 미들웨어, OpenTelemetry, stdlib 인터셉트

<details>
<summary>설정 (Configuration)</summary>

### `setup()` 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|-----------|------|---------|-------------|
| `level` | `str` | `"INFO"` | 로그 레벨 |
| `json` | `bool` | `False` | JSON 출력 활성화 |
| `truncate` | `int` | `10000` | 메시지 최대 길이 |
| `file` | `str \| None` | `None` | 로그 파일 경로 |
| `rotation` | `str \| int \| None` | `None` | 파일 로테이션 (예: "10 MB", "1 day") |
| `retention` | `str \| int \| None` | `None` | 파일 보관 기간 (예: "7 days") |
| `intercept` | `list[str] \| None` | `None` | 인터셉트할 stdlib 로거 목록 |
| `otel` | `bool` | `False` | OpenTelemetry 트레이스 주입 활성화 |
| `force` | `bool` | `False` | 재설정 강제 실행 |

### 환경 변수

| 변수명 | 기본값 | 설명 |
|----------|---------|-------------|
| `LOGURU_KIT_LEVEL` | `INFO` | 로그 레벨 |
| `LOGURU_KIT_JSON` | `false` | JSON 출력 여부 |

우선순위: 코드 > 환경 변수 > 기본값
</details>

<details>
<summary>파일 로깅 (File Logging)</summary>

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
<summary>FastAPI 통합</summary>

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

# OTEL 트레이스 주입 활성화
setup(otel=True)
logger = get_logger(__name__)

logger.info("이 로그는 trace_id와 span_id를 포함합니다")
```
</details>

<details>
<summary>stdlib 인터셉트</summary>

```python
from loguru_kit import setup

# 특정 stdlib 로거 인터셉트
setup(intercept=["uvicorn", "sqlalchemy"])
```
</details>

## 라이선스

MIT License - 자세한 내용은 [LICENSE](./LICENSE)를 참조하세요.
