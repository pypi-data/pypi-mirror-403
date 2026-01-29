from loguru_kit import get_logger, setup

# Enable OTEL trace injection
setup(otel=True)
logger = get_logger(__name__)

logger.info("This log will have trace_id and span_id")
