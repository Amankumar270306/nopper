"""Request models for the Nopper SDK."""

from typing import Any

from pydantic import BaseModel, Field

from nopper.models.messages import Message


class ExecutionRequest(BaseModel):
    """Encapsulates a complete execution request passed from Wrapper to Node."""
    messages: list[Message]
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any | None = None
    response_model: Any | None = None
    stream: bool = False
    timeout: float | None = None
    kwargs: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


class EmbedRequest(BaseModel):
    """Encapsulates an embedding request."""
    text: str
    model: str | None = None
    kwargs: dict[str, Any] = Field(default_factory=dict)
