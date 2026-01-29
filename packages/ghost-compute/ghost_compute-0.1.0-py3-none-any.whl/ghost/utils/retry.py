"""
Retry utilities for Ghost Compute.
"""

from __future__ import annotations

import asyncio
import functools
import random
from typing import Any, Callable, Type, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ghost.core.exceptions import RateLimitError, PlatformError


T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    exceptions: tuple[Type[Exception], ...] = (PlatformError, RateLimitError),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_attempts=5)
        def call_api():
            return api.get_data()
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )


def jitter(value: float, factor: float = 0.1) -> float:
    """
    Add random jitter to a value.

    Args:
        value: Base value
        factor: Jitter factor (0.1 = ±10%)

    Returns:
        Value with random jitter applied
    """
    jitter_range = value * factor
    return value + random.uniform(-jitter_range, jitter_range)


async def async_retry_with_backoff(
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    exceptions: tuple[Type[Exception], ...] = (PlatformError, RateLimitError),
    **kwargs: Any,
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Positional arguments for the function
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries
        max_wait: Maximum wait time between retries
        exceptions: Exception types to retry on
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function call

    Raises:
        The last exception if all retries fail
    """
    last_exception: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                wait_time = min(min_wait * (2 ** attempt), max_wait)
                wait_time = jitter(wait_time)
                await asyncio.sleep(wait_time)

    if last_exception:
        raise last_exception
