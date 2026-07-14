"""Backwards compatibility re-export for LocalProvider."""

from nopper.provider.adapters.local import (
    LocalAdapter as LocalProvider,
    LMStudioAdapter as LMStudioProvider,
    VLLMAdapter as VLLMProvider,
    CustomAdapter as CustomProvider,
)

__all__ = [
    "LocalProvider",
    "LMStudioProvider",
    "VLLMProvider",
    "CustomProvider",
]
