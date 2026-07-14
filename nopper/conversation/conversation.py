"""Conversation and AsyncConversation classes."""

import json
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

from nopper.models.messages import Message, Role
from nopper.models.responses import ChatResponse, StreamChunk


class Conversation:
    """Stateful synchronous conversation session."""

    def __init__(
        self,
        ai: Any,
        system_prompt: str | None = None,
        save_file: str | None = None,
        max_history: int | None = None,
    ):
        self.ai = ai
        self.save_file = save_file
        self.max_history = max_history
        self.history: list[Message] = []

        if system_prompt:
            self.history.append(Message(role=Role.SYSTEM, content=system_prompt))

        if save_file:
            self._load_history()

    def _load_history(self) -> None:
        if not self.save_file:
            return
        path = Path(self.save_file)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = [Message(**m) for m in data]
            except Exception:
                pass

    def _save_history(self) -> None:
        if not self.save_file:
            return
        path = Path(self.save_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([m.model_dump(exclude_none=True) for m in self.history], f, indent=2)

    def _trim_history(self) -> None:
        if self.max_history and len(self.history) > self.max_history:
            system_msgs = [m for m in self.history if m.role == Role.SYSTEM]
            other_msgs = [m for m in self.history if m.role != Role.SYSTEM]
            other_msgs = other_msgs[-self.max_history:]
            self.history = system_msgs + other_msgs

    def ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> str | ChatResponse:
        self.history.append(Message(role=Role.USER, content=prompt))
        self._trim_history()

        response = self.ai.chat(self.history, raw=True, **kwargs)

        if isinstance(response, ChatResponse):
            self.history.append(response.message)
            self._save_history()
            if raw:
                return response
            return response.message.content or ""

        content = str(response)
        self.history.append(Message(role=Role.ASSISTANT, content=content))
        self._save_history()
        return content

    def stream_ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> Iterator[str | StreamChunk]:
        self.history.append(Message(role=Role.USER, content=prompt))
        self._trim_history()

        chunks: list[str] = []
        for chunk in self.ai.stream(self.history, raw=True, **kwargs):
            if isinstance(chunk, StreamChunk):
                chunks.append(chunk.chunk)
                if raw:
                    yield chunk
                else:
                    yield chunk.chunk
            else:
                chunks.append(str(chunk))
                yield str(chunk)

        full_content = "".join(chunks)
        self.history.append(Message(role=Role.ASSISTANT, content=full_content))
        self._save_history()

    def clear(self) -> None:
        self.history = [m for m in self.history if m.role == Role.SYSTEM]
        if self.save_file:
            path = Path(self.save_file)
            if path.exists():
                path.unlink()


class AsyncConversation:
    """Stateful asynchronous conversation session."""

    def __init__(
        self,
        ai: Any,
        system_prompt: str | None = None,
        save_file: str | None = None,
        max_history: int | None = None,
    ):
        self.ai = ai
        self.save_file = save_file
        self.max_history = max_history
        self.history: list[Message] = []

        if system_prompt:
            self.history.append(Message(role=Role.SYSTEM, content=system_prompt))

        if save_file:
            self._load_history()

    def _load_history(self) -> None:
        if not self.save_file:
            return
        path = Path(self.save_file)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = [Message(**m) for m in data]
            except Exception:
                pass

    def _save_history(self) -> None:
        if not self.save_file:
            return
        path = Path(self.save_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([m.model_dump(exclude_none=True) for m in self.history], f, indent=2)

    def _trim_history(self) -> None:
        if self.max_history and len(self.history) > self.max_history:
            system_msgs = [m for m in self.history if m.role == Role.SYSTEM]
            other_msgs = [m for m in self.history if m.role != Role.SYSTEM]
            other_msgs = other_msgs[-self.max_history:]
            self.history = system_msgs + other_msgs

    async def ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> str | ChatResponse:
        self.history.append(Message(role=Role.USER, content=prompt))
        self._trim_history()

        response = await self.ai.chat(self.history, raw=True, **kwargs)

        if isinstance(response, ChatResponse):
            self.history.append(response.message)
            self._save_history()
            if raw:
                return response
            return response.message.content or ""

        content = str(response)
        self.history.append(Message(role=Role.ASSISTANT, content=content))
        self._save_history()
        return content

    async def stream_ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> AsyncIterator[str | StreamChunk]:
        self.history.append(Message(role=Role.USER, content=prompt))
        self._trim_history()

        chunks: list[str] = []
        async for chunk in self.ai.stream(self.history, raw=True, **kwargs):
            if isinstance(chunk, StreamChunk):
                chunks.append(chunk.chunk)
                if raw:
                    yield chunk
                else:
                    yield chunk.chunk
            else:
                chunks.append(str(chunk))
                yield str(chunk)

        full_content = "".join(chunks)
        self.history.append(Message(role=Role.ASSISTANT, content=full_content))
        self._save_history()

    def clear(self) -> None:
        self.history = [m for m in self.history if m.role == Role.SYSTEM]
        if self.save_file:
            path = Path(self.save_file)
            if path.exists():
                path.unlink()
