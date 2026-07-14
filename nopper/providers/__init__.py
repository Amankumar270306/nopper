"""Provider adapters package (forwarding to new provider.adapters module)."""

from nopper.provider.registry import registry
from nopper.provider.adapters.openai import OpenAIAdapter as OpenAIProvider
from nopper.provider.adapters.anthropic import AnthropicAdapter as AnthropicProvider
from nopper.provider.adapters.gemini import GeminiAdapter as GeminiProvider
from nopper.provider.adapters.ollama import OllamaAdapter as OllamaProvider
from nopper.provider.adapters.groq import GroqAdapter as GroqProvider
from nopper.provider.adapters.mistral import MistralAdapter as MistralProvider
from nopper.provider.adapters.openrouter import OpenRouterAdapter as OpenRouterProvider
from nopper.provider.adapters.together import TogetherAdapter as TogetherProvider
from nopper.provider.adapters.local import LocalAdapter as LocalProvider
from nopper.provider.base import BaseProvider


def list_providers() -> list[str]:
    """Return list of all registered provider names."""
    return registry.list()


__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "OllamaProvider",
    "GroqProvider",
    "MistralProvider",
    "OpenRouterProvider",
    "TogetherProvider",
    "LocalProvider",
    "list_providers",
]
