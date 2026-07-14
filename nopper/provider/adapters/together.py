from nopper.provider.registry import registry
from typing import Any

from nopper.provider.adapters.openai import OpenAIAdapter


class TogetherAdapter(OpenAIAdapter):
    """Provider implementation for Together AI."""

    BASE_URL = "https://api.together.xyz/v1"

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("Together API key is missing.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, *args: Any, **kwargs: Any) -> Any:

        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "meta-llama/Llama-3-8b-chat-hf"

        response = super().chat(*args, **kwargs)
        response.provider = "together"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "meta-llama/Llama-3-8b-chat-hf"

        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "together"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "meta-llama/Llama-3-8b-chat-hf"

        response = await super().achat(*args, **kwargs)
        response.provider = "together"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "meta-llama/Llama-3-8b-chat-hf"

        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "together"
            yield chunk


# Self-register
registry.register("together", TogetherAdapter)
