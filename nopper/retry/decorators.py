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
    curr: BaseException | None = exception
    seen: set[int] = set()
    while curr is not None and id(curr) not in seen:
        seen.add(id(curr))
        if isinstance(curr, httpx.HTTPStatusError):
            return curr.response.status_code in RETRYABLE_STATUS_CODES
        if isinstance(curr, httpx.RequestError):
            return True
        if hasattr(curr, "status_code") and getattr(curr, "status_code") in RETRYABLE_STATUS_CODES:
            return True
        curr = curr.__cause__ or curr.__context__
    return False


def _get_retry_delay(exception: Exception, attempt: int, base_delay: float = 1.0) -> float:
    curr: BaseException | None = exception
    seen: set[int] = set()
    while curr is not None and id(curr) not in seen:
        seen.add(id(curr))
        response = getattr(curr, "response", None)
        if response is not None and hasattr(response, "headers"):
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    return max(float(retry_after), 0.5)
                except ValueError:
                    pass
        curr = curr.__cause__ or curr.__context__
    return base_delay * (2**attempt)


def _get_retry_params(target: Any) -> tuple[int, float]:
    node = getattr(target, "node", None)
    config = getattr(node, "config", None)
    retry_policy = getattr(config, "retry_policy", None)
    base_delay = getattr(retry_policy, "base_delay", 1.0) if retry_policy else 1.0
    max_retries = getattr(target, "max_retries", None)
    if max_retries is None and retry_policy:
        max_retries = retry_policy.max_retries
    if max_retries is None:
        max_retries = 3
    return max_retries, base_delay


def retry_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        max_retries, base_delay = _get_retry_params(self)

        for attempt in range(max_retries + 1):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if attempt == max_retries or not _should_retry(e):
                    raise

                delay = _get_retry_delay(e, attempt, base_delay)
                logger.warning(
                    f"Request failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

    return wrapper


def retry_async(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        max_retries, base_delay = _get_retry_params(self)

        for attempt in range(max_retries + 1):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                if attempt == max_retries or not _should_retry(e):
                    raise

                delay = _get_retry_delay(e, attempt, base_delay)
                logger.warning(
                    f"Request failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s (Attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

    return wrapper


def retry_stream_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Generator[Any, None, None]:
        max_retries, base_delay = _get_retry_params(self)

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

                delay = _get_retry_delay(e, attempt, base_delay)
                logger.warning(
                    f"Stream failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

    return wrapper


def retry_stream_async(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
        max_retries, base_delay = _get_retry_params(self)

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

                delay = _get_retry_delay(e, attempt, base_delay)
                logger.warning(
                    f"Stream failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s (Attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

    return wrapper
