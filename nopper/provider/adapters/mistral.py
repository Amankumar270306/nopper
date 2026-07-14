from nopper.provider.registry import registry
from typing import Any

from nopper.provider.adapters.openai import OpenAIAdapter


class MistralAdapter(OpenAIAdapter):
    """Provider implementation for Mistral AI."""

    BASE_URL = "https://api.mistral.ai/v1"

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "mistral-large-latest"

        response = super().chat(*args, **kwargs)
        response.provider = "mistral"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "mistral-large-latest"

        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "mistral"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "mistral-large-latest"

        response = await super().achat(*args, **kwargs)
        response.provider = "mistral"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "mistral-large-latest"

        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "mistral"
            yield chunk


# Self-register
registry.register("mistral", MistralAdapter)
