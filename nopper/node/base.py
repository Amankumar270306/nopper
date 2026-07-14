"""Abstract base class for all node types."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

from nopper.models.requests import ExecutionRequest
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.node.config import NodeConfig


class Node(ABC):
    """Abstract execution engine.

    The Node decides HOW requests are executed. The Wrapper only
    decides WHAT should happen — it delegates all execution to
    its Node.
    """

    def __init__(self, config: NodeConfig):
        self._config = config

    @property
    def config(self) -> NodeConfig:
        return self._config

    @property
    def name(self) -> str:
        return self._config.name

    @abstractmethod
    def execute(self, request: ExecutionRequest) -> ChatResponse:
        """Execute a chat completion request."""
        ...

    @abstractmethod
    def execute_stream(self, request: ExecutionRequest) -> Iterator[StreamChunk]:
        """Execute a streaming chat completion request."""
        ...

    @abstractmethod
    async def aexecute(self, request: ExecutionRequest) -> ChatResponse:
        """Execute a chat completion request asynchronously."""
        ...

    @abstractmethod
    def aexecute_stream(self, request: ExecutionRequest) -> AsyncIterator[StreamChunk]:
        """Execute a streaming chat completion request asynchronously."""
        ...

    @abstractmethod
    def execute_embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:
        """Execute an embedding request."""
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this node's provider."""
        ...

    def reload(self, config: NodeConfig) -> None:
        """Hot-reload the node configuration."""
        self._config = config
