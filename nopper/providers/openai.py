"""Backwards compatibility re-export for OpenAIProvider."""

from nopper.provider.adapters.openai import OpenAIAdapter as OpenAIProvider

__all__ = ["OpenAIProvider"]
