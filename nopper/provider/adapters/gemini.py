import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import httpx

from nopper.models.messages import Function, Message, Role, ToolCall
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.provider.base import BaseProvider
from nopper.provider.registry import registry


class GeminiAdapter(BaseProvider):
    """Provider implementation for Google's Gemini API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def _prepare_payload(self, messages: list[Message], temperature: float | None, max_tokens: int | None, tools: list[dict[str, Any]] | None = None, tool_choice: str | dict[str, Any] | None = None, response_model: Any | None = None, **kwargs: Any) -> dict[str, Any]:
        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_instruction = {
                    "role": "user",
                    "parts": [{"text": msg.content or ""}]
                }
            elif msg.role == Role.TOOL:
                contents.append({
                    "role": "function",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.name or msg.tool_call_id or "unknown",
                            "response": {"result": msg.content or ""}
                        }
                    }]
                })
            else:
                role = "model" if msg.role == Role.ASSISTANT else "user"
                parts: list[dict[str, Any]] = []
                if msg.content:
                    parts.append({"text": msg.content})
                    
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append({
                            "functionCall": {
                                "name": tc.function.name,
                                "args": json.loads(tc.function.arguments) if tc.function.arguments else {}
                            }
                        })
                
                if not parts:
                    parts.append({"text": msg.content or ""})
                    
                contents.append({
                    "role": role,
                    "parts": parts
                })

        payload = {
            "contents": contents,
            **kwargs
        }

        if system_instruction:
            payload["systemInstruction"] = system_instruction

        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if response_model is not None:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = response_model.model_json_schema()

        if generation_config:
            payload["generationConfig"] = generation_config

        if tools:
            gemini_funcs = []
            for t in tools:
                if t.get("type") == "function":
                    gemini_funcs.append(t["function"])
            payload["tools"] = [{"functionDeclarations": gemini_funcs}]
            
        if tool_choice:
            if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
                payload["toolConfig"] = {
                    "functionCallingConfig": {
                        "mode": "ANY",
                        "allowedFunctionNames": [tool_choice["function"]["name"]]
                    }
                }
            elif isinstance(tool_choice, str) and tool_choice in ["auto", "any"]:
                payload["toolConfig"] = {
                    "functionCallingConfig": {
                        "mode": tool_choice.upper()
                    }
                }

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
        **kwargs: Any
    ) -> ChatResponse:
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")

        target_model = model or self.default_model or "gemini-1.5-pro"

        model_path = target_model if target_model.startswith("models/") else f"models/{target_model}"

        url = f"{self.BASE_URL}/{model_path.split('/')[-1]}:generateContent?key={self.api_key}"
        payload = self._prepare_payload(messages, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)

        response = httpx.post(url, headers={"Content-Type": "application/json"}, json=payload)
        response.raise_for_status()
        data = response.json()

        candidate = data.get("candidates", [{}])[0]
        content_parts = candidate.get("content", {}).get("parts", [])
        
        text = ""
        tool_calls = []
        for part in content_parts:
            if "text" in part:
                text += part["text"]
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(ToolCall(
                    id=fc.get("name", "call_1"),
                    type="function",
                    function=Function(
                        name=fc.get("name", ""),
                        arguments=json.dumps(fc.get("args", {}))
                    )
                ))

        usage = data.get("usageMetadata", {})
        
        msg_kwargs: dict[str, Any] = {"role": Role.ASSISTANT}
        if text:
            msg_kwargs["content"] = text
        if tool_calls:
            msg_kwargs["tool_calls"] = tool_calls

        return ChatResponse(
            message=Message(**msg_kwargs),
            finish_reason=candidate.get("finishReason", "stop"),
            provider="gemini",
            model=target_model,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0)
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
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")

        target_model = model or self.default_model or "gemini-1.5-pro"
        model_path = target_model if target_model.startswith("models/") else f"models/{target_model}"

        url = f"{self.BASE_URL}/{model_path.split('/')[-1]}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = self._prepare_payload(messages, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)

        with httpx.stream("POST", url, headers={"Content-Type": "application/json"}, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        candidate = data.get("candidates", [{}])[0]
                        content_parts = candidate.get("content", {}).get("parts", [])
                        for part in content_parts:
                            if "text" in part:
                                yield StreamChunk(
                                    chunk=part["text"],
                                    provider="gemini",
                                    model=target_model
                                )
                    except json.JSONDecodeError:
                        continue

    def models(self) -> list[str]:
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")

        url = f"{self.BASE_URL}?key={self.api_key}"
        response = httpx.get(url)
        response.raise_for_status()
        data = response.json()

        return [model["name"].replace("models/", "") for model in data.get("models", [])]

    def embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")

        target_model = model or "text-embedding-004"
        model_path = target_model if target_model.startswith("models/") else f"models/{target_model}"

        url = f"{self.BASE_URL}/{model_path.split('/')[-1]}:embedContent?key={self.api_key}"

        payload = {
            "model": model_path,
            "content": {
                "parts": [{"text": text}]
            },
            **kwargs
        }

        response = httpx.post(url, headers={"Content-Type": "application/json"}, json=payload)
        response.raise_for_status()
        data = response.json()

        return cast(list[float], data.get("embedding", {}).get("values", []))

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
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")

        target_model = model or self.default_model or "gemini-1.5-pro"
        model_path = target_model if target_model.startswith("models/") else f"models/{target_model}"

        url = f"{self.BASE_URL}/{model_path.split('/')[-1]}:generateContent?key={self.api_key}"
        payload = self._prepare_payload(messages, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers={"Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            data = response.json()

        candidate = data.get("candidates", [{}])[0]
        content_parts = candidate.get("content", {}).get("parts", [])
        
        text = ""
        tool_calls = []
        for part in content_parts:
            if "text" in part:
                text += part["text"]
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(ToolCall(
                    id=fc.get("name", "call_1"),
                    type="function",
                    function=Function(
                        name=fc.get("name", ""),
                        arguments=json.dumps(fc.get("args", {}))
                    )
                ))

        usage = data.get("usageMetadata", {})
        
        msg_kwargs: dict[str, Any] = {"role": Role.ASSISTANT}
        if text:
            msg_kwargs["content"] = text
        if tool_calls:
            msg_kwargs["tool_calls"] = tool_calls

        return ChatResponse(
            message=Message(**msg_kwargs),
            finish_reason=candidate.get("finishReason", "stop"),
            provider="gemini",
            model=target_model,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0)
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
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")

        target_model = model or self.default_model or "gemini-1.5-pro"
        model_path = target_model if target_model.startswith("models/") else f"models/{target_model}"

        url = f"{self.BASE_URL}/{model_path.split('/')[-1]}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = self._prepare_payload(messages, temperature, max_tokens, tools=tools, tool_choice=tool_choice, response_model=response_model, **kwargs)

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers={"Content-Type": "application/json"}, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            candidate = data.get("candidates", [{}])[0]
                            content_parts = candidate.get("content", {}).get("parts", [])
                            for part in content_parts:
                                if "text" in part:
                                    yield StreamChunk(
                                        chunk=part["text"],
                                        provider="gemini",
                                        model=target_model
                                    )
                        except json.JSONDecodeError:
                            continue


# Self-register
registry.register("gemini", GeminiAdapter)
