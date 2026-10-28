"""AsyncAI class — asynchronous public Wrapper layer."""

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any, cast

from nopper.config.loader import load_config
from nopper.models.arena import ArenaResponse
from nopper.models.messages import Message
from nopper.models.requests import ExecutionRequest
from nopper.models.responses import AIString, ChatResponse, StreamChunk
from nopper.node.base import Node
from nopper.node.config import NodeConfig
from nopper.node.manager import NodeManager
from nopper.observability.tracking import log_usage
from nopper.retry.decorators import retry_async, retry_stream_async
from nopper.wrapper.events import EventBus
from nopper.wrapper.middleware import Middleware, MiddlewarePipeline
from nopper.wrapper.prompt import PromptBuilder


class AsyncAI:
    """Asynchronous SDK Wrapper interface for interacting with AI models."""

    def __init__(
        self,
        wrapper_name: str | None = None,
        provider: str | list[str] | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
        auto_reload: bool = True,
        **kwargs: Any,
    ):
        self.wrapper_name = wrapper_name or "default"
        self.auto_reload = auto_reload
        self.max_retries = max_retries
        self.extra_kwargs = kwargs
        self._timeout = timeout
        save_location = kwargs.pop("save_location", None)
        save_path = kwargs.pop("save_path", None)

        settings = load_config()
        self.track_usage = kwargs.pop("track_usage", settings.track_usage)
        self.track_file = kwargs.pop("track_file", settings.track_file)
        self.track_format = kwargs.pop("track_format", settings.track_format)

        self.event_bus = EventBus()
        self.middleware = MiddlewarePipeline()

        if provider or model or api_key or timeout is not None:
            p = provider[0] if isinstance(provider, list) else provider
            fallbacks = provider[1:] if isinstance(provider, list) else []
            node_timeout = float(timeout) if timeout is not None else float(settings.timeout)
            config = NodeConfig(
                name=self.wrapper_name,
                provider=p or settings.provider,
                model=model or settings.model,
                api_key=api_key or settings.api_keys.get(p or settings.provider),
                fallbacks=fallbacks,
                timeout=node_timeout,
                parameters=kwargs,
            )
            NodeManager.save(config, location=save_location, path=save_path)
            self._node: Node = NodeManager.resolve(self.wrapper_name)
        else:
            self._node = NodeManager.resolve(self.wrapper_name)

    @property
    def node(self) -> Node:
        if self.auto_reload:
            self.reload()
        return self._node

    @property
    def timeout(self) -> float:
        """Return the effective request timeout in seconds."""
        if self._timeout is not None:
            return self._timeout
        return getattr(self.node.config, "timeout", None) or 60.0

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        """Set the request timeout in seconds."""
        self._timeout = value

    @property
    def provider_name(self) -> str:
        return self.node.config.provider

    def reload(self) -> None:
        self._node = NodeManager.resolve(self.wrapper_name)

    def use_middleware(self, mw: Middleware) -> None:
        self.middleware.use(mw)

    def on(self, event: str, handler: Any) -> None:
        self.event_bus.on(event, handler)

    @retry_async
    async def chat(
        self,
        prompt: str | list[str] | list[Message],
        raw: bool = False,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> str | ChatResponse | Any | None:
        """Send a chat completion request asynchronously."""
        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self._timeout)
        messages = PromptBuilder.prepare(prompt)
        request = ExecutionRequest(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            response_model=response_model,
            timeout=effective_timeout,
            kwargs=kwargs,
        )

        request = self.middleware.run_before(request)
        self.event_bus.emit("on_request", request=request)

        start = time.perf_counter()
        response = await self.node.aexecute(request)
        latency = time.perf_counter() - start
        response.latency = latency
        if effective_timeout is not None:
            response.timeout = effective_timeout
        elif response.timeout is None:
            response.timeout = self.timeout

        response = self.middleware.run_after(response)
        self.event_bus.emit("on_response", response=response)

        log_usage(prompt, response, self.track_usage, self.track_file, self.track_format)

        if raw:
            return response

        if response_model:
            parsed = None
            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    if (
                        tc.function.name == "return_structured_output"
                        or tc.function.name == response_model.__name__
                    ):
                        parsed = response_model.model_validate_json(tc.function.arguments)
                        break
            if not parsed and response.message.content:
                parsed = response_model.model_validate_json(response.message.content)

            if not parsed:
                raise ValueError("Failed to parse structured output from response.")

            for attr in ("tokens", "cost", "model", "provider", "latency", "timeout"):
                val = getattr(response, attr, None) if attr != "tokens" else response.total_tokens
                if not hasattr(parsed, attr):
                    object.__setattr__(parsed, attr, val)

            return cast(str | ChatResponse | Any, parsed)

        return AIString(
            response.message.content or "",
            tokens=response.total_tokens,
            cost=response.cost,
            model=response.model,
            provider=response.provider,
            latency=response.latency,
            timeout=response.timeout,
        )

    generate = chat
    response = chat  # Alias for .response()

    @retry_stream_async
    async def stream(
        self,
        prompt: str | list[str] | list[Message],
        raw: bool = False,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str] | AsyncIterator[StreamChunk]:
        """Stream a chat completion response asynchronously."""
        if response_model:
            raise NotImplementedError("Streaming is not supported when response_model is provided.")

        effective_timeout = timeout if timeout is not None else kwargs.pop("timeout", self._timeout)
        messages = PromptBuilder.prepare(prompt)
        request = ExecutionRequest(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
            timeout=effective_timeout,
            kwargs=kwargs,
        )

        request = self.middleware.run_before(request)

        async for chunk in self.node.aexecute_stream(request):
            self.event_bus.emit("on_token", chunk=chunk)
            if raw:
                yield chunk
            else:
                yield chunk.chunk

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        return self.node.execute_embed(text, **kwargs)

    async def models(self) -> list[str]:
        return self.node.list_models()

    def conversation(
        self,
        system_prompt: str | None = None,
        save_file: str | None = None,
        max_history: int | None = None,
    ) -> Any:
        from nopper.conversation.conversation import AsyncConversation
        return AsyncConversation(
            self,
            system_prompt=system_prompt,
            save_file=save_file,
            max_history=max_history,
        )

    async def arena(self, prompt: str, **kwargs: Any) -> ArenaResponse:
        settings = load_config()
        providers = [self.node.config.provider] + self.node.config.fallbacks

        if len(providers) == 1:
            all_p = [p for p, k in settings.api_keys.items() if k]
            if "ollama" not in all_p:
                all_p.append("ollama")
            if len(all_p) > 1:
                providers = all_p

        async def _query_provider(p_name: str) -> tuple[str, ChatResponse | str]:
            try:
                ai = AsyncAI(provider=p_name, max_retries=0)
                resp = await ai.chat(prompt, raw=True, **kwargs)
                return p_name, resp
            except Exception as e:
                return p_name, str(e)

        tasks = [_query_provider(p) for p in providers]
        results = await asyncio.gather(*tasks)

        return ArenaResponse(responses={name: resp for name, resp in results})
