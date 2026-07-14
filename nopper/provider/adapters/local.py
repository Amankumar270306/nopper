from nopper.provider.registry import registry
from typing import Any

from nopper.provider.adapters.openai import OpenAIAdapter


class LocalAdapter(OpenAIAdapter):
    """Generic provider for local OpenAI-compatible servers (e.g., text-generation-webui)."""

    BASE_URL = "http://localhost:8000/v1"

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        response = super().chat(*args, **kwargs)
        response.provider = "local"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "local"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        response = await super().achat(*args, **kwargs)
        response.provider = "local"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "local"
            yield chunk

class LMStudioAdapter(OpenAIAdapter):
    """Provider specifically targeted at LM Studio."""

    BASE_URL = "http://localhost:1234/v1"

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        response = super().chat(*args, **kwargs)
        response.provider = "lm_studio"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "lm_studio"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        response = await super().achat(*args, **kwargs)
        response.provider = "lm_studio"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "lm_studio"
            yield chunk

class VLLMAdapter(OpenAIAdapter):
    """Provider specifically targeted at vLLM servers."""

    BASE_URL = "http://localhost:8000/v1"

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        response = super().chat(*args, **kwargs)
        response.provider = "vllm"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "vllm"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        response = await super().achat(*args, **kwargs)
        response.provider = "vllm"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "vllm"
            yield chunk

class CustomAdapter(OpenAIAdapter):
    """Generic provider for custom OpenAI-compatible remote nodes."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if not self.base_url:
            raise ValueError("CustomProvider requires a base_url")
            
    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        response = super().chat(*args, **kwargs)
        response.provider = "custom"
        return response

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        for chunk in super().stream(*args, **kwargs):
            chunk.provider = "custom"
            yield chunk

    async def achat(self, *args: Any, **kwargs: Any) -> Any:
        response = await super().achat(*args, **kwargs)
        response.provider = "custom"
        return response

    async def astream(self, *args: Any, **kwargs: Any) -> Any:
        async for chunk in super().astream(*args, **kwargs):
            chunk.provider = "custom"
            yield chunk


# Self-register
registry.register("local", LocalAdapter)
registry.register("lm_studio", LMStudioAdapter)
registry.register("vllm", VLLMAdapter)
registry.register("custom", CustomAdapter)
