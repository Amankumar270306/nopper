"""Backwards compatibility shim for nopper.retries."""

from nopper.retry.decorators import (
    retry_sync,
    retry_async,
    retry_stream_sync,
    retry_stream_async,
)

__all__ = [
    "retry_sync",
    "retry_async",
    "retry_stream_sync",
    "retry_stream_async",
]
