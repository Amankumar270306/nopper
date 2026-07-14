"""Nopper settings models."""


from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class NodeConfig(BaseModel):
    """Legacy node config for backwards compatibility with global config."""
    type: str = "remote"
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout: float | None = None


class NopperSettings(BaseSettings):
    """Global configuration for Nopper."""

    provider: str = Field(default="openai", description="Default AI provider")
    model: str = Field(default="gpt-4o", description="Default model name")
    temperature: float = Field(default=0.7, description="Default temperature")
    max_tokens: int = Field(default=1024, description="Default max tokens")
    timeout: int = Field(default=60, description="Default timeout in seconds")
    aliases: dict[str, str] = Field(default_factory=dict, description="Model aliases")
    api_keys: dict[str, str] = Field(default_factory=dict, description="API Keys")
    base_urls: dict[str, str] = Field(default_factory=dict, description="Custom base URLs")
    nodes: dict[str, NodeConfig] = Field(default_factory=dict, description="Custom nodes")
    templates: dict[str, str] = Field(default_factory=dict, description="Prompt templates")
    cache_enabled: bool = Field(default=False, description="Whether to cache responses")

    track_usage: bool = Field(default=False, description="Whether to globally track AI usage")
    track_file: str = Field(default="usage.csv", description="File path for tracking data")
    track_format: str = Field(default="csv", description="Format of the tracking file (csv/json)")

    default_node: str | None = Field(default=None, description="Default node name")
