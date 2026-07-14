"""CachedNode — Decorator Node that adds caching around an underlying Node."""

from collections.abc import AsyncIterator, Iterator
from typing import Any

from nopper.models.requests import ExecutionRequest
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.node.base import Node
from nopper.node.config import NodeConfig


class CachedNode(Node):
    """CachedNode wraps an inner Node and checks/populates cache on execution."""

    def __init__(self, inner: Node, config: NodeConfig | None = None):
        super().__init__(config or inner.config)
        self.inner = inner

    def execute(self, request: ExecutionRequest) -> ChatResponse:
        from nopper.cache import get_cached_response, set_cached_response

        prompt_str = str([m.model_dump() for m in request.messages])
        cached_dict = get_cached_response(
            prompt_str,
            self.config.model,
            self.config.provider,
            tools=request.tools,
            tool_choice=request.tool_choice,
            **request.kwargs,
        )
        if cached_dict:
            return ChatResponse.model_validate(cached_dict)

        response = self.inner.execute(request)

        set_cached_response(
            prompt_str,
            self.config.model,
            self.config.provider,
            response.model_dump(),
            tools=request.tools,
            tool_choice=request.tool_choice,
            **request.kwargs,
        )
        return response

    def execute_stream(self, request: ExecutionRequest) -> Iterator[StreamChunk]:
        # Caching streaming responses delegates to inner node directly
        yield from self.inner.execute_stream(request)

    async def aexecute(self, request: ExecutionRequest) -> ChatResponse:
        from nopper.cache import get_cached_response, set_cached_response

        prompt_str = str([m.model_dump() for m in request.messages])
        cached_dict = get_cached_response(
            prompt_str,
            self.config.model,
            self.config.provider,
            tools=request.tools,
            tool_choice=request.tool_choice,
            **request.kwargs,
        )
        if cached_dict:
            return ChatResponse.model_validate(cached_dict)

        response = await self.inner.aexecute(request)

        set_cached_response(
            prompt_str,
            self.config.model,
            self.config.provider,
            response.model_dump(),
            tools=request.tools,
            tool_choice=request.tool_choice,
            **request.kwargs,
        )
        return response

    async def aexecute_stream(self, request: ExecutionRequest) -> AsyncIterator[StreamChunk]:
        async for chunk in self.inner.aexecute_stream(request):
            yield chunk

    def execute_embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:
        return self.inner.execute_embed(text, model=model, **kwargs)

    def list_models(self) -> list[str]:
        return self.inner.list_models()
