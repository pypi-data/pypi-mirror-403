from loguru_kit import get_logger, setup

setup()
logger = get_logger(__name__)
logger.info("Hello, world!")
