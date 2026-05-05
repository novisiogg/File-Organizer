from functools import wraps
import logging
import os

DECORATOR_DIR = os.path.dirname(os.path.abspath(__file__))

log_file_path = os.path.join(DECORATOR_DIR, "app.log")
# logger configuration
logging.basicConfig(
    level=logging.INFO,
    filename=log_file_path,
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
)


logger = logging.getLogger(__name__)


def log(func):
    @wraps(func)
    def inner(*args, **kwargs):
        logger.info(f"{func.__name__} called with args={args}, kwargs={kwargs}")
        
        result = func(*args, **kwargs)
        if result is not None:
            logger.info(f"{func.__name__} returned: {result}")
        return result
    return inner