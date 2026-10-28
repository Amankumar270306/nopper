"""LocalNode — standard single-provider execution node."""

from collections.abc import AsyncIterator, Iterator
from typing import Any

from nopper.errors.exceptions import NodeError
from nopper.models.requests import ExecutionRequest
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.node.base import Node
from nopper.node.config import NodeConfig
from nopper.provider.base import BaseProvider
from nopper.provider.factory import ProviderFactory


class LocalNode(Node):
    """LocalNode executes requests directly through a single provider adapter."""

    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self._provider_instance: BaseProvider | None = None

    def _get_provider(self) -> BaseProvider:
        if self._provider_instance is None:
            params = self._config.parameters.copy()
            if self._config.temperature is not None:
                params["temperature"] = self._config.temperature
            if self._config.top_p is not None:
                params["top_p"] = self._config.top_p
            if self._config.max_tokens is not None:
                params["max_tokens"] = self._config.max_tokens

            self._provider_instance = ProviderFactory.create(
                provider_name=self._config.provider,
                api_key=self._config.api_key,
                model=self._config.model,
                base_url=self._config.base_url,
                timeout=self._config.timeout,
                **params,
            )
        return self._provider_instance

    def reload(self, config: NodeConfig) -> None:
        super().reload(config)
        self._provider_instance = None  # Reset provider cache on reload

    def execute(self, request: ExecutionRequest) -> ChatResponse:
        provider = self._get_provider()
        effective_timeout = request.timeout if request.timeout is not None else self._config.timeout
        try:
            response = provider.chat(
                messages=request.messages,
                model=self._config.model,
                tools=request.tools,
                tool_choice=request.tool_choice,
                response_model=request.response_model,
                timeout=effective_timeout,
                **request.kwargs,
            )
            response.timeout = effective_timeout
            return response
        except Exception as e:
            raise NodeError(f"Node '{self.name}' execution failed: {e}") from e

    def execute_stream(self, request: ExecutionRequest) -> Iterator[StreamChunk]:
        provider = self._get_provider()
        effective_timeout = request.timeout if request.timeout is not None else self._config.timeout
        try:
            yield from provider.stream(
                messages=request.messages,
                model=self._config.model,
                tools=request.tools,
                tool_choice=request.tool_choice,
                response_model=request.response_model,
                timeout=effective_timeout,
                **request.kwargs,
            )
        except Exception as e:
            raise NodeError(f"Node '{self.name}' streaming failed: {e}") from e

    async def aexecute(self, request: ExecutionRequest) -> ChatResponse:
        provider = self._get_provider()
        effective_timeout = request.timeout if request.timeout is not None else self._config.timeout
        try:
            response = await provider.achat(
                messages=request.messages,
                model=self._config.model,
                tools=request.tools,
                tool_choice=request.tool_choice,
                response_model=request.response_model,
                timeout=effective_timeout,
                **request.kwargs,
            )
            response.timeout = effective_timeout
            return response
        except Exception as e:
            raise NodeError(f"Node '{self.name}' async execution failed: {e}") from e

    async def aexecute_stream(self, request: ExecutionRequest) -> AsyncIterator[StreamChunk]:
        provider = self._get_provider()
        effective_timeout = request.timeout if request.timeout is not None else self._config.timeout
        try:
            async for chunk in provider.astream(
                messages=request.messages,
                model=self._config.model,
                tools=request.tools,
                tool_choice=request.tool_choice,
                response_model=request.response_model,
                timeout=effective_timeout,
                **request.kwargs,
            ):
                yield chunk
        except Exception as e:
            raise NodeError(f"Node '{self.name}' async streaming failed: {e}") from e

    def execute_embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:
        provider = self._get_provider()
        return provider.embed(text, model=model or self._config.model, **kwargs)

    def list_models(self) -> list[str]:
        provider = self._get_provider()
        return provider.models()
