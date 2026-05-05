import logging
import functools
import time
from pathlib import Path

LOG_DIR = Path.home() / ".file_organizer" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.INFO,
    filename=str(LOG_FILE),
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
)

logger = logging.getLogger("File Organizer")


def log(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        msg = f"{func.__name__} | Duration: {duration:.4f}s"
        if result is not None:
            msg += f" | Result: {result}"
        logger.info(msg)
        return result

    return inner
