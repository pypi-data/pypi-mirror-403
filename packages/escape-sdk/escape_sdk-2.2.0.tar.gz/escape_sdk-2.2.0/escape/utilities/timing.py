"""Timing utilities - delays, waits, retries."""

import random
import time
from collections.abc import Callable
from typing import Any

import escape.globals as globals
from escape._internal.logger import logger


def current_time() -> float:
    """Get the current time in seconds since the epoch."""
    return time.time()


def current_tick() -> int:
    """Get the current tick count from the game client."""
    client = globals.get_client()
    return client.cache.tick or 0


def wait_ticks(ticks: int):
    """Wait for a specified number of game ticks."""
    start_tick = current_tick()
    while current_tick() - start_tick < ticks:
        time.sleep(0.01)


def sleep(min_seconds: float, max_seconds: float | None = None):
    """Sleep for a random duration between min and max seconds."""
    if max_seconds is None:
        time.sleep(min_seconds)
    else:
        duration = random.uniform(min_seconds, max_seconds)
        time.sleep(duration)


def wait_until(
    condition: Callable[[], bool], timeout: float = 10.0, poll_interval: float = 0.1
) -> bool:
    """Wait until a condition becomes true or timeout occurs."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(poll_interval)

    return False


def retry(
    func: Callable[[], Any],
    max_attempts: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = False,
) -> Any | None:
    """Retry a function multiple times if it fails."""
    current_delay = delay

    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                logger.error(f"All {max_attempts} attempts failed: {e}")
                return None

            logger.error(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s")
            time.sleep(current_delay)

            if exponential_backoff:
                current_delay *= 2

    return None


def measure_time(func: Callable[[], Any]) -> tuple[Any, float]:
    """Measure execution time of a function."""
    start = time.time()
    result = func()
    elapsed = time.time() - start
    return result, elapsed
