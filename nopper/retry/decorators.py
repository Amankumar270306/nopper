"""Retry and resilience decorators."""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Callable, Generator
from functools import wraps
from typing import Any

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _should_retry(exception: Exception) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in RETRYABLE_STATUS_CODES
    if isinstance(exception, httpx.RequestError):
        return True
    return False


def retry_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        max_retries = getattr(self, "max_retries", 3)
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if attempt == max_retries or not _should_retry(e):
                    raise

                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Request failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay}s (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

    return wrapper


def retry_async(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        max_retries = getattr(self, "max_retries", 3)
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                if attempt == max_retries or not _should_retry(e):
                    raise

                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Request failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay}s (Attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

    return wrapper


def retry_stream_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Generator[Any, None, None]:
        max_retries = getattr(self, "max_retries", 3)
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            first_yield = False
            try:
                gen = func(self, *args, **kwargs)
                for item in gen:
                    first_yield = True
                    yield item
                return
            except Exception as e:
                if first_yield:
                    raise
                if attempt == max_retries or not _should_retry(e):
                    raise

                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Stream failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay}s (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

    return wrapper


def retry_stream_async(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
        max_retries = getattr(self, "max_retries", 3)
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            first_yield = False
            try:
                gen = func(self, *args, **kwargs)
                async for item in gen:
                    first_yield = True
                    yield item
                return
            except Exception as e:
                if first_yield:
                    raise
                if attempt == max_retries or not _should_retry(e):
                    raise

                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Stream failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay}s (Attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

    return wrapper
