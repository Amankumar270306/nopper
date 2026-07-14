import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import httpx

from nopper.models.messages import Message
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.provider.base import BaseProvider
from nopper.provider.registry import registry


class OllamaAdapter(BaseProvider):
    """Provider implementation for Ollama's local API."""

    BASE_URL = "http://localhost:11434/api"

    def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any
    ) -> ChatResponse:
        url = f"{self.BASE_URL}/chat"
        target_model = model or self.default_model or "llama3"

        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": target_model,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": False,
            **kwargs
        }

        if options:
            payload["options"] = options

        response = httpx.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            message=Message(**data["message"]),
            finish_reason="stop" if data.get("done") else "unknown",
            provider="ollama",
            model=data["model"],
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        )

    def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any
    ) -> Iterator[StreamChunk]:
        url = f"{self.BASE_URL}/chat"
        target_model = model or self.default_model or "llama3"

        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": target_model,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": True,
            **kwargs
        }

        if options:
            payload["options"] = options

        with httpx.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield StreamChunk(
                            chunk=data["message"]["content"],
                            provider="ollama",
                            model=data.get("model", target_model)
                        )
                except (json.JSONDecodeError, KeyError):
                    continue

    def models(self) -> list[str]:
        url = f"{self.BASE_URL}/tags"
        response = httpx.get(url)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]

    def embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:

        url = f"{self.BASE_URL}/embeddings"
        payload = {
            "prompt": text,
            "model": model or "nomic-embed-text",
            **kwargs
        }
        response = httpx.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return cast(list[float], data["embedding"])

    async def achat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any
    ) -> ChatResponse:
        url = f"{self.BASE_URL}/chat"
        target_model = model or self.default_model or "llama3"

        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": target_model,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": False,
            **kwargs
        }

        if options:
            payload["options"] = options

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return ChatResponse(
            message=Message(**data["message"]),
            finish_reason="stop" if data.get("done") else "unknown",
            provider="ollama",
            model=data["model"],
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        )

    async def astream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        url = f"{self.BASE_URL}/chat"
        target_model = model or self.default_model or "llama3"

        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": target_model,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": True,
            **kwargs
        }

        if options:
            payload["options"] = options

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield StreamChunk(
                                chunk=data["message"]["content"],
                                provider="ollama",
                                model=data.get("model", target_model)
                            )
                    except (json.JSONDecodeError, KeyError):
                        continue


# Self-register
registry.register("ollama", OllamaAdapter)
