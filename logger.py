from functools import wraps
import logging
from pathlib import Path
import time

DECORATOR_DIR = Path(__file__).resolve().parent

log_dir = DECORATOR_DIR / "logs"

log_dir.mkdir(exist_ok=True)

log_file_path = log_dir / "app.log"


# logger configuration
logging.basicConfig(
    filename=log_file_path,
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
)


logger = logging.getLogger(__name__)


def log(func):
    @wraps(func)
    def inner(*args, **kwargs):
        time_before = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - time_before

        msg = f"{func.__name__} | Duration: {duration:.2f}s"
        if result is not None:
            msg += f" | Result: {result}"

        logger.info(msg)
        return result

    return inner
