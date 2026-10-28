"""Abstract base class for all AI provider adapters."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx

from nopper.models.messages import Message
from nopper.models.responses import ChatResponse, StreamChunk


class BaseProvider(ABC):
    """Abstract base class for all AI provider adapters.

    Every provider adapter must implement this interface. The adapter
    translates the common Nopper interface into provider-specific
    HTTP/SDK calls.
    """

    @staticmethod
    def check_response(response: httpx.Response) -> None:
        """Inspect HTTP response and raise httpx.HTTPStatusError with provider error details if error."""
        if response.is_error:
            try:
                response.read()
            except Exception:
                pass

            detail = None
            try:
                data = response.json()
                if isinstance(data, dict):
                    err = data.get("error")
                    if isinstance(err, dict):
                        metadata = err.get("metadata")
                        raw = metadata.get("raw") if isinstance(metadata, dict) else None
                        detail = raw or err.get("message")
                    elif isinstance(err, str):
                        detail = err
                    elif "message" in data:
                        detail = data["message"]
            except Exception:
                pass

            if not detail and response.text:
                text = response.text.strip()
                if len(text) < 300:
                    detail = text

            if detail:
                msg = f"Client error '{response.status_code} {response.reason_phrase}' for url '{response.url}': {detail}"
                raise httpx.HTTPStatusError(msg, request=response.request, response=response)

            response.raise_for_status()

    @staticmethod
    def resolve_timeout(timeout: float | None) -> float | None:
        """Resolve timeout for HTTP requests. -1 (or < 0) means unlimited (None in httpx)."""
        if timeout is not None and timeout < 0:
            return None
        return timeout

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
        self.timeout = timeout if timeout is not None else 60.0
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
        timeout: float | None = None,
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
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Stream a synchronous chat completion response."""
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
        timeout: float | None = None,
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
        timeout: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream an asynchronous chat completion response."""
        ...

    # ── Embeddings ────────────────────────────────────────────────

    @abstractmethod
    def embed(
        self,
        text: str,
        model: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> list[float]:
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
