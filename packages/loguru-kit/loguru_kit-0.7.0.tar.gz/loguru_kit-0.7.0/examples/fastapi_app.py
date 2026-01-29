from fastapi import FastAPI

from loguru_kit import get_logger, setup
from loguru_kit.integrations.fastapi import LoggingMiddleware

setup(json=True)
logger = get_logger(__name__)

app = FastAPI()
app.add_middleware(LoggingMiddleware)


@app.get("/")
async def root():
    logger.info("Request received")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
