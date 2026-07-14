"""Backwards compatibility re-export for OllamaProvider."""

from nopper.provider.adapters.ollama import OllamaAdapter as OllamaProvider

__all__ = ["OllamaProvider"]
