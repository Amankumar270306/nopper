"""Node configuration models."""

from typing import Any

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    """Retry configuration for a node."""
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    base_delay: float = Field(default=1.0, description="Base delay in seconds")
    strategy: str = Field(default="exponential_backoff", description="Retry strategy")


class CachePolicy(BaseModel):
    """Cache configuration for a node."""
    enabled: bool = Field(default=False, description="Whether caching is enabled")
    backend: str = Field(default="memory", description="Cache backend type")
    ttl: int = Field(default=3600, description="Cache TTL in seconds")


class NodeConfig(BaseModel):
    """Configuration for a single execution node.

    A Node owns provider, model, api key, retry policy, fallback chain,
    cache policy, routing, cost/latency tracking, and execution state.
    """
    name: str = Field(description="Unique node name")
    provider: str = Field(default="openai", description="AI provider name")
    model: str = Field(default="gpt-4o", description="Default model")
    api_key: str | None = Field(default=None, description="API key (overrides global)")
    base_url: str | None = Field(default=None, description="Custom base URL")
    temperature: float | None = Field(default=None, description="Default temperature")
    top_p: float | None = Field(default=None, description="Default top_p")
    max_tokens: int | None = Field(default=None, description="Default max tokens")
    timeout: float | None = Field(default=60.0, description="Request timeout seconds")
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    fallbacks: list[str] = Field(default_factory=list, description="Fallback provider:model pairs")
    cache_policy: CachePolicy = Field(default_factory=CachePolicy)
    routing_policy: dict[str, Any] = Field(
        default_factory=lambda: {"strategy": "primary_with_fallback"},
        description="Routing strategy config",
    )
    parameters: dict[str, Any] = Field(default_factory=dict, description="Extra provider params")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
