"""Message and role models for the Nopper SDK."""

from enum import Enum

from pydantic import BaseModel


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
