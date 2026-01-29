from InlinePlaylink.logger import logger
from InlinePlaylink.custom_exception import InvalidURLException
logger.info("This is a test log messasge from test.py")

try:
    raise InvalidURLException("The provided URL is invalid")
except Exception as e:
    logger.error(f"Caught an exception: {e}")