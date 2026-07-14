"""Backwards compatibility shim for nopper.ai."""

from nopper.wrapper.wrapper import AI
from nopper.wrapper.async_wrapper import AsyncAI

__all__ = ["AI", "AsyncAI"]
