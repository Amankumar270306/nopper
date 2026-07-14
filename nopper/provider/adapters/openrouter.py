from nopper.provider.registry import registry
from typing import Any

from nopper.provider.adapters.openai import OpenAIAdapter


class OpenRouterAdapter(OpenAIAdapter):
    """Provider implementation for OpenRouter."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("OpenRouter API key is missing.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/nopper/nopper",
            "X-Title": "Nopper CLI",
        }

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        response = super().chat(*args, **kwargs)
        response.provider = "openrouter"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "openrouter"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        response = await super().achat(*args, **kwargs)
        response.provider = "openrouter"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "openrouter"
            yield chunk


# Self-register
registry.register("openrouter", OpenRouterAdapter)
