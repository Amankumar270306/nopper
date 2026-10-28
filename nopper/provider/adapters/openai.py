"""OpenAI provider adapter."""

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import httpx

from nopper.models.messages import Message
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.provider.base import BaseProvider
from nopper.provider.registry import registry


class OpenAIAdapter(BaseProvider):
    """Provider adapter for OpenAI's API."""

    BASE_URL = "https://api.openai.com/v1"

    @property
    def _url(self) -> str:
        return self.base_url or self.BASE_URL

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        url = f"{self._url}/chat/completions"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)

        payload: dict[str, Any] = {
            "model": model or self.default_model or "gpt-4o",
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            **kwargs,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if response_model is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                    "strict": True,
                },
            }

        response = httpx.post(url, headers=self._get_headers(), json=payload, timeout=httpx_timeout)
        self.check_response(response)
        data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return ChatResponse(
            message=Message(**choice["message"]),
            finish_reason=choice.get("finish_reason", "stop"),
            provider="openai",
            model=data["model"],
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            timeout=effective_timeout,
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
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        url = f"{self._url}/chat/completions"
        target_model = model or self.default_model or "gpt-4o"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": True,
            **kwargs,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        with httpx.stream("POST", url, headers=self._get_headers(), json=payload, timeout=httpx_timeout) as response:
            self.check_response(response)
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if delta.get("content"):
                            yield StreamChunk(
                                chunk=delta["content"],
                                provider="openai",
                                model=data.get("model", target_model),
                            )
                    except (json.JSONDecodeError, KeyError):
                        continue

    def models(self) -> list[str]:
        url = f"{self._url}/models"
        response = httpx.get(url, headers=self._get_headers(), timeout=self.timeout)
        self.check_response(response)
        data = response.json()
        return [m["id"] for m in data.get("data", [])]

    def embed(self, text: str, model: str | None = None, timeout: float | None = None, **kwargs: Any) -> list[float]:
        url = f"{self._url}/embeddings"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)
        payload = {
            "input": text,
            "model": model or "text-embedding-3-small",
            **kwargs,
        }
        response = httpx.post(url, headers=self._get_headers(), json=payload, timeout=httpx_timeout)
        self.check_response(response)
        data = response.json()
        return cast(list[float], data["data"][0]["embedding"])

    async def achat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        url = f"{self._url}/chat/completions"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)

        payload: dict[str, Any] = {
            "model": model or self.default_model or "gpt-4o",
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            **kwargs,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if response_model is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                    "strict": True,
                },
            }

        async with httpx.AsyncClient(timeout=httpx_timeout) as client:
            response = await client.post(url, headers=self._get_headers(), json=payload)
            self.check_response(response)
            data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return ChatResponse(
            message=Message(**choice["message"]),
            finish_reason=choice.get("finish_reason", "stop"),
            provider="openai",
            model=data["model"],
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            timeout=effective_timeout,
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
        timeout: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        url = f"{self._url}/chat/completions"
        target_model = model or self.default_model or "gpt-4o"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": True,
            **kwargs,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        async with httpx.AsyncClient(timeout=httpx_timeout) as client:
            async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                self.check_response(response)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            if delta.get("content"):
                                yield StreamChunk(
                                    chunk=delta["content"],
                                    provider="openai",
                                    model=data.get("model", target_model),
                                )
                        except (json.JSONDecodeError, KeyError):
                            continue


# Self-register
registry.register("openai", OpenAIAdapter)
