from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Function(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Function

class Message(BaseModel):
    """Standardized chat message format across all providers."""
    role: Role
    content: str | None = None
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

class ChatResponse(BaseModel):
    """Standardized chat response format across all providers."""
    message: Message
    finish_reason: str = Field(default="stop")
    provider: str
    model: str
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    cost: float = Field(default=0.0)
    latency: float = Field(default=0.0)

class AIString(str):
    """A string subclass that includes AI metadata."""
    tokens: int
    cost: float
    model: str
    provider: str
    latency: float

    def __new__(cls, value: str, tokens: int = 0, cost: float = 0.0, model: str = "", provider: str = "", latency: float = 0.0):
        obj = str.__new__(cls, value)
        obj.tokens = tokens
        obj.cost = cost
        obj.model = model
        obj.provider = provider
        obj.latency = latency
        return obj

class StreamChunk(BaseModel):
    """Standardized streaming chunk format."""
    chunk: str
    provider: str
    model: str

class ArenaResponse(BaseModel):
    """Response from multiple models side by side."""
    model_config = {"arbitrary_types_allowed": True}
    responses: dict[str, ChatResponse | AIString | str]

    def __str__(self) -> str:
        parts = []
        for provider, response in self.responses.items():
            parts.append(f"{provider.capitalize()}")
            if isinstance(response, ChatResponse):
                parts.append(response.message.content or "")
            elif isinstance(response, str):
                parts.append(response)
            else:
                parts.append(str(response))
            parts.append("")
        return "\n".join(parts)

