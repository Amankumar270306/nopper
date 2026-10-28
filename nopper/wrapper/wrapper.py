"""The AI class — the public Wrapper layer of the Nopper SDK.

The Wrapper is the object the user directly interacts with.
It owns:
  - Public API methods: chat(), stream(), embed(), conversation(), arena()
  - Prompt construction & memory context
  - Middleware & event bus
  - Tracking & log usage

The Wrapper KNOWS NOTHING about providers (OpenAI, Gemini, Anthropic).
It delegates all execution to its assigned Node.
"""

import time
from collections.abc import Iterator
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
from nopper.retry.decorators import retry_stream_sync, retry_sync
from nopper.wrapper.events import EventBus
from nopper.wrapper.middleware import Middleware, MiddlewarePipeline
from nopper.wrapper.prompt import PromptBuilder


class AI:
    """Main SDK Wrapper interface for interacting with AI models.

    Example:
        coding = AI("coding")
        response = coding.chat("Write a fast sort in Python")
    """

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

        # Resolve the underlying Node
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
        """Access the underlying execution Node."""
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
        """Return assigned provider name."""
        return self.node.config.provider

    def reload(self) -> None:
        """Reload node configuration from disk."""
        self._node = NodeManager.resolve(self.wrapper_name)

    def use_middleware(self, mw: Middleware) -> None:
        """Register a custom middleware."""
        self.middleware.use(mw)

    def on(self, event: str, handler: Any) -> None:
        """Register an event listener on the event bus."""
        self.event_bus.on(event, handler)

    # ── Chat completion ───────────────────────────────────────────

    @retry_sync
    def chat(
        self,
        prompt: str | list[str] | list[Message],
        raw: bool = False,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> str | ChatResponse | Any | None:
        """Send a chat completion request.

        Args:
            prompt: Text prompt, list of prompts, or Message objects.
            raw: If True, return raw ChatResponse instead of AIString.
            tools: Tool definitions for function calling.
            tool_choice: Tool selection policy.
            response_model: Pydantic model for structured outputs.
            timeout: Request timeout in seconds. If omitted, uses default.
            **kwargs: Extra parameters passed to the provider adapter.
        """
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
        response = self.node.execute(request)
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

    generate = chat  # Alias for backward compatibility
    response = chat  # Alias for .response()

    # ── Streaming completion ──────────────────────────────────────

    @retry_stream_sync
    def stream(
        self,
        prompt: str | list[str] | list[Message],
        raw: bool = False,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Iterator[str] | Iterator[StreamChunk]:
        """Stream a chat completion response."""
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

        for chunk in self.node.execute_stream(request):
            self.event_bus.emit("on_token", chunk=chunk)
            if raw:
                yield chunk
            else:
                yield chunk.chunk

    # ── Embeddings ────────────────────────────────────────────────

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Get text embeddings."""
        return self.node.execute_embed(text, **kwargs)

    # ── Model listing ─────────────────────────────────────────────

    def models(self) -> list[str]:
        """List available models."""
        return self.node.list_models()

    # ── Conversation ──────────────────────────────────────────────

    def conversation(
        self,
        system_prompt: str | None = None,
        save_file: str | None = None,
        max_history: int | None = None,
    ) -> Any:
        """Start a new stateful conversation."""
        from nopper.conversation.conversation import Conversation
        return Conversation(
            self,
            system_prompt=system_prompt,
            save_file=save_file,
            max_history=max_history,
        )

    # ── Arena comparison ──────────────────────────────────────────

    def arena(self, prompt: str, **kwargs: Any) -> ArenaResponse:
        """Run a prompt across multiple models concurrently."""
        import asyncio

        from nopper.wrapper.async_wrapper import AsyncAI

        async def _run_arena():
            async_ai = AsyncAI(
                wrapper_name=self.wrapper_name,
                max_retries=self.max_retries,
            )
            return await async_ai.arena(prompt, **kwargs)

        return asyncio.run(_run_arena())

    # ── Multimodal stubs ──────────────────────────────────────────

    def image(self, prompt: str, **kwargs: Any) -> Any:
        raise NotImplementedError("Image generation is not supported by this provider.")

    def speech(self, text: str, **kwargs: Any) -> Any:
        raise NotImplementedError("Text-to-speech is not supported by this provider.")

    def transcribe(self, audio: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Speech-to-text is not supported by this provider.")

    def vision(self, image: Any, prompt: str, **kwargs: Any) -> Any:
        raise NotImplementedError("Vision is not supported by this provider.")

    def function_call(self, **kwargs: Any) -> Any:
        raise NotImplementedError("Function calling is not supported by this provider.")

    def batch(self, **kwargs: Any) -> Any:
        raise NotImplementedError("Batch processing is not supported by this provider.")
