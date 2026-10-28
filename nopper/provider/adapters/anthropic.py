import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx

from nopper.models.messages import Function, Message, Role, ToolCall
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.provider.base import BaseProvider
from nopper.provider.registry import registry


class AnthropicAdapter(BaseProvider):
    """Provider implementation for Anthropic's Claude API."""

    BASE_URL = "https://api.openai.com/v1"
    BASE_URL = "https://api.anthropic.com/v1"

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("Anthropic API key is missing.")
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _prepare_payload(self, messages: list[Message], model: str | None, temperature: float | None, max_tokens: int | None, tools: list[dict[str, Any]] | None = None, tool_choice: str | dict[str, Any] | None = None, response_model: Any | None = None, **kwargs: Any) -> dict[str, Any]:
        """Extracts system message and formats payload for Anthropic."""
        target_model = model or self.default_model or "claude-3-5-sonnet-20240620"

        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_prompt += (msg.content or "") + "\n"
            elif msg.role == Role.TOOL:
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content or ""
                        }
                    ]
                })
            else:
                content: list[dict[str, Any]] = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        content.append({
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.function.name,
                            "input": json.loads(tc.function.arguments) if tc.function.arguments else {}
                        })
                
                if not content:
                    content.append({"type": "text", "text": msg.content or ""})
                    
                anthropic_messages.append({"role": msg.role.value, "content": content})

        payload = {
            "model": target_model,
            "messages": anthropic_messages,

            "max_tokens": max_tokens or 1024,
            **kwargs
        }

        if system_prompt:
            payload["system"] = system_prompt.strip()

        if temperature is not None:
            payload["temperature"] = temperature

        if response_model:
            schema = response_model.model_json_schema()
            tools = tools or []
            tools.append({
                "type": "function",
                "function": {
                    "name": response_model.__name__,
                    "description": "Return the structured output based on the provided schema.",
                    "parameters": schema
                }
            })
            tool_choice = {"type": "function", "function": {"name": response_model.__name__}}

        if tools:
            anthropic_tools = []
            for t in tools:
                if t.get("type") == "function":
                    func = t.get("function", {})
                    anthropic_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {"type": "object", "properties": {}})
                    })
            payload["tools"] = anthropic_tools
            
        if tool_choice:
            if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
                payload["tool_choice"] = {"type": "tool", "name": tool_choice["function"]["name"]}
            elif isinstance(tool_choice, str) and tool_choice in ["auto", "any"]:
                payload["tool_choice"] = {"type": tool_choice}

        return payload

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
        **kwargs: Any
    ) -> ChatResponse:
        url = f"{self.BASE_URL}/messages"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)
        payload = self._prepare_payload(messages, model, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)

        response = httpx.post(url, headers=self._get_headers(), json=payload, timeout=httpx_timeout)
        self.check_response(response)
        data = response.json()

        content = ""
        tool_calls = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    type="function",
                    function=Function(
                        name=block["name"],
                        arguments=json.dumps(block["input"])
                    )
                ))

        usage = data.get("usage", {})
        
        msg_kwargs: dict[str, Any] = {"role": Role.ASSISTANT}
        if content:
            msg_kwargs["content"] = content
        if tool_calls:
            msg_kwargs["tool_calls"] = tool_calls

        return ChatResponse(
            message=Message(**msg_kwargs),
            finish_reason=data.get("stop_reason", "stop"),
            provider="anthropic",
            model=data["model"],
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
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
        **kwargs: Any
    ) -> Iterator[StreamChunk]:
        url = f"{self.BASE_URL}/messages"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)
        payload = self._prepare_payload(messages, model, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)
        payload["stream"] = True

        with httpx.stream("POST", url, headers=self._get_headers(), json=payload, timeout=httpx_timeout) as response:
            self.check_response(response)
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield StreamChunk(
                                    chunk=delta.get("text", ""),
                                    provider="anthropic",
                                    model=payload["model"]
                                )
                    except json.JSONDecodeError:
                        continue

    def models(self) -> list[str]:

        return [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]

    def embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:
        raise NotImplementedError("Anthropic does not natively support embeddings. They recommend using Voyage AI.")

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
        **kwargs: Any
    ) -> ChatResponse:
        url = f"{self.BASE_URL}/messages"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)
        payload = self._prepare_payload(messages, model, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)

        async with httpx.AsyncClient(timeout=httpx_timeout) as client:
            response = await client.post(url, headers=self._get_headers(), json=payload)
            self.check_response(response)
            data = response.json()

        content = ""
        tool_calls = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    type="function",
                    function=Function(
                        name=block["name"],
                        arguments=json.dumps(block["input"])
                    )
                ))

        usage = data.get("usage", {})
        
        msg_kwargs: dict[str, Any] = {"role": Role.ASSISTANT}
        if content:
            msg_kwargs["content"] = content
        if tool_calls:
            msg_kwargs["tool_calls"] = tool_calls

        return ChatResponse(
            message=Message(**msg_kwargs),
            finish_reason=data.get("stop_reason", "stop"),
            provider="anthropic",
            model=data["model"],
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
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
        **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        url = f"{self.BASE_URL}/messages"
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self.timeout)
        httpx_timeout = self.resolve_timeout(effective_timeout)
        payload = self._prepare_payload(messages, model, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=httpx_timeout) as client:
            async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                self.check_response(response)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield StreamChunk(
                                        chunk=delta.get("text", ""),
                                        provider="anthropic",
                                        model=payload.get("model", "claude-3")
                                    )
                        except json.JSONDecodeError:
                            continue


# Self-register
registry.register("anthropic", AnthropicAdapter)
