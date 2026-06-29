import time
import functools
from src.utils.logger import get_logger

logger = get_logger("timer")


def timed(func):
    """
    Decorator that logs wall-clock execution time of a function.
    Critical for monitoring the 5-minute CPU budget.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
        return result
    return wrapper


class StageTimer:
    """
    Context manager for timing pipeline stages.

    Usage:
        with StageTimer("feature_extraction"):
            ...
    """
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.start = None
        self.elapsed = None

    def __enter__(self):
        self.start = time.perf_counter()
        logger.info(f"[START] {self.stage_name}")
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
        logger.info(f"[DONE]  {self.stage_name} — {self.elapsed:.2f}s")
