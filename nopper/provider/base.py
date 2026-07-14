"""Abstract base class for all AI provider adapters."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

from nopper.models.messages import Message
from nopper.models.responses import ChatResponse, StreamChunk


class BaseProvider(ABC):
    """Abstract base class for all AI provider adapters.

    Every provider adapter must implement this interface. The adapter
    translates the common Nopper interface into provider-specific
    HTTP/SDK calls.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ):
        self.api_key = api_key
        self.default_model = model
        self.base_url = base_url
        self.timeout = timeout or 60.0
        self.extra = kwargs

    # ── Chat ──────────────────────────────────────────────────────

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a synchronous chat completion request."""
        ...

    @abstractmethod
    def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Stream a synchronous chat completion response."""
        ...

    @abstractmethod
    def astream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion response from the provider asynchronously."""
        ...

    @abstractmethod
    async def achat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send an asynchronous chat completion request."""
        ...

    @abstractmethod
    async def astream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_model: Any | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream an asynchronous chat completion response."""
        ...

    # ── Embeddings ────────────────────────────────────────────────

    @abstractmethod
    def embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:
        """Get text embeddings."""
        ...

    # ── Model listing ─────────────────────────────────────────────

    @abstractmethod
    def models(self) -> list[str]:
        """List available models for this provider."""
        ...

    # ── Multimodal (optional) ─────────────────────────────────────

    def image(self, prompt: str, **kwargs: Any) -> Any:
        """Generate an image from a prompt."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support image generation.")

    def speech(self, text: str, **kwargs: Any) -> Any:
        """Convert text to speech."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support text-to-speech.")

    def transcribe(self, audio: Any, **kwargs: Any) -> str:
        """Transcribe audio to text."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support transcription.")

    def video(self, prompt: str, **kwargs: Any) -> Any:
        """Generate video from a prompt."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support video generation.")
