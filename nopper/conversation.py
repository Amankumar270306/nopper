import json
import os
from collections.abc import AsyncIterator, Iterator
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from nopper.models import ChatResponse, Message, Role, StreamChunk

if TYPE_CHECKING:
    from nopper.ai import AI, AsyncAI

class Conversation:
    """A stateful conversation that tracks history across multiple turns."""

    def __init__(self, ai: "AI", system_prompt: str | None = None, save_file: str | None = None, max_history: int | None = None):
        self.ai = ai
        self.save_file = save_file
        self.max_history = max_history
        self.history: list[Message] = []
        
        if self.save_file and os.path.exists(self.save_file):
            self._load_history()
            
        if not self.history and system_prompt:
            self.history.append(Message(role=Role.SYSTEM, content=system_prompt))
            self._save_history()

    def _load_history(self):
        if not self.save_file:
            return
        try:
            with open(self.save_file, "r") as f:
                data = json.load(f)
                self.history = [Message.model_validate(m) for m in data]
        except Exception:
            pass

    def _save_history(self):
        if not self.save_file:
            return
        try:
            with open(self.save_file, "w") as f:
                data = [m.model_dump() for m in self.history]
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _get_context(self) -> list[Message]:
        if self.max_history is None or self.max_history <= 0:
            return self.history
            
        if not self.history:
            return []
            
        context = []
        start_idx = 0
        if self.history[0].role == Role.SYSTEM:
            context.append(self.history[0])
            start_idx = 1
            
        recent = self.history[start_idx:]
        if len(recent) > self.max_history:
            recent = recent[-self.max_history:]
            
        context.extend(recent)
        return context

    def ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> str | ChatResponse | Any:
        """Send a message and append the response to the conversation history."""
        self.history.append(Message(role=Role.USER, content=prompt))
        self._save_history()
        
        response = self.ai.chat(self._get_context(), raw=True, **kwargs)

        if isinstance(response, ChatResponse):
            self.history.append(response.message)
            self._save_history()
            return response if raw else (response.message.content or "")
        else:
            self.history.append(Message(role=Role.ASSISTANT, content=str(response)))
            self._save_history()
            return cast(str | ChatResponse | Any, response)

    def stream_ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> Iterator[str] | Iterator[StreamChunk]:
        """Stream a message and append the final concatenated response to the conversation history."""
        self.history.append(Message(role=Role.USER, content=prompt))
        self._save_history()
        
        full_content = ""
        for chunk in self.ai.stream(self._get_context(), raw=True, **kwargs):
            if isinstance(chunk, StreamChunk):
                if chunk.chunk:
                    full_content += chunk.chunk
                yield chunk if raw else chunk.chunk
            else:
                yield chunk
                
        self.history.append(Message(role=Role.ASSISTANT, content=full_content))
        self._save_history()


class AsyncConversation:
    """An asynchronous stateful conversation that tracks history across multiple turns."""

    def __init__(self, ai: "AsyncAI", system_prompt: str | None = None, save_file: str | None = None, max_history: int | None = None):
        self.ai = ai
        self.save_file = save_file
        self.max_history = max_history
        self.history: list[Message] = []
        
        if self.save_file and os.path.exists(self.save_file):
            self._load_history()
            
        if not self.history and system_prompt:
            self.history.append(Message(role=Role.SYSTEM, content=system_prompt))
            self._save_history()

    def _load_history(self):
        if not self.save_file:
            return
        try:
            with open(self.save_file, "r") as f:
                data = json.load(f)
                self.history = [Message.model_validate(m) for m in data]
        except Exception:
            pass

    def _save_history(self):
        if not self.save_file:
            return
        try:
            with open(self.save_file, "w") as f:
                data = [m.model_dump() for m in self.history]
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _get_context(self) -> list[Message]:
        if self.max_history is None or self.max_history <= 0:
            return self.history
            
        if not self.history:
            return []
            
        context = []
        start_idx = 0
        if self.history[0].role == Role.SYSTEM:
            context.append(self.history[0])
            start_idx = 1
            
        recent = self.history[start_idx:]
        if len(recent) > self.max_history:
            recent = recent[-self.max_history:]
            
        context.extend(recent)
        return context

    async def ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> str | ChatResponse | Any:
        """Asynchronously send a message and append the response to the conversation history."""
        self.history.append(Message(role=Role.USER, content=prompt))
        self._save_history()
        
        response = await self.ai.chat(self._get_context(), raw=True, **kwargs)

        if isinstance(response, ChatResponse):
            self.history.append(response.message)
            self._save_history()
            return response if raw else (response.message.content or "")
        else:
            self.history.append(Message(role=Role.ASSISTANT, content=str(response)))
            self._save_history()
            return cast(str | ChatResponse | Any, response)

    async def stream_ask(self, prompt: str, raw: bool = False, **kwargs: Any) -> AsyncIterator[str] | AsyncIterator[StreamChunk]:
        """Asynchronously stream a message and append the final response to the conversation history."""
        self.history.append(Message(role=Role.USER, content=prompt))
        self._save_history()
        
        full_content = ""
        async for chunk in self.ai.stream(self._get_context(), raw=True, **kwargs):
            if isinstance(chunk, StreamChunk):
                if chunk.chunk:
                    full_content += chunk.chunk
                yield chunk if raw else chunk.chunk
            else:
                yield chunk
                
        self.history.append(Message(role=Role.ASSISTANT, content=full_content))
        self._save_history()
