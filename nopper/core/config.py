from typing import Any

from pydantic import BaseModel, Field


class WrapperConfig(BaseModel):
    name: str = Field(description="Name of the wrapper")
    provider: str = Field(default="openai", description="Assigned AI provider")
    model: str = Field(default="gpt-4o", description="Assigned AI model")
    node: str | None = Field(default=None, description="Custom node to route to, if any")
    api_key: str | None = Field(default=None, description="Specific API key for this wrapper (overrides global)")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Execution parameters (e.g., temperature)")
    system_prompt: str = Field(default="", description="System prompt to prepend to every chat")
    fallbacks: list[str] = Field(default_factory=list, description="Fallback providers in case of failure")
    memory: dict[str, Any] = Field(default_factory=lambda: {"enabled": False, "max_messages": 10}, description="Conversation memory config")
    tools: list[dict[str, Any]] = Field(default_factory=list, description="List of tool definitions available to this wrapper")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
