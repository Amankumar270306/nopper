from nopper.provider.registry import registry
from typing import Any

from nopper.provider.adapters.openai import OpenAIAdapter


class GroqAdapter(OpenAIAdapter):
    """Provider implementation for Groq."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("Groq API key is missing.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, *args: Any, **kwargs: Any) -> Any:

        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "llama3-8b-8192"

        response = super().chat(*args, **kwargs)
        response.provider = "groq"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "llama3-8b-8192"

        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "groq"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "llama3-8b-8192"

        response = await super().achat(*args, **kwargs)
        response.provider = "groq"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        if "model" not in kwargs and not self.default_model:
            kwargs["model"] = "llama3-8b-8192"

        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "groq"
            yield chunk


# Self-register
registry.register("groq", GroqAdapter)
