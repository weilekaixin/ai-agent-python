"""Retry decorators with exponential backoff for LLM and external API calls."""
from __future__ import annotations

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry a synchronous callable with exponential backoff.

    Usage::

        @with_retry(max_attempts=3, exceptions=(httpx.TransportError,))
        def call_external_api():
            ...
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            "%s gave up after %d attempts: %s",
                            fn.__name__, max_attempts, exc,
                        )
                        raise
                    logger.warning(
                        "%s attempt %d/%d failed (%s); retrying in %.1fs",
                        fn.__name__, attempt, max_attempts, exc, delay,
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)

        return wrapper

    return decorator


def async_with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry an async callable with exponential backoff.

    Usage::

        @async_with_retry(max_attempts=3, base_delay=0.5)
        async def call_llm():
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            "%s gave up after %d attempts: %s",
                            fn.__name__, max_attempts, exc,
                        )
                        raise
                    logger.warning(
                        "%s attempt %d/%d failed (%s); retrying in %.1fs",
                        fn.__name__, attempt, max_attempts, exc, delay,
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)

        return wrapper

    return decorator
