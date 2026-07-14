"""Response models for the Nopper SDK."""


from pydantic import BaseModel, Field

from nopper.models.messages import Message


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

    def __new__(
        cls,
        value: str,
        tokens: int = 0,
        cost: float = 0.0,
        model: str = "",
        provider: str = "",
        latency: float = 0.0,
    ) -> "AIString":
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
    finish_reason: str | None = None
