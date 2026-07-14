import json
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings

CONFIG_DIR = Path.home() / ".nopper"
CONFIG_FILE = CONFIG_DIR / "config.json"

from pydantic import BaseModel


class NodeConfig(BaseModel):
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

# Alias for backwards compatibility
MyAISettings = NopperSettings

def load_config() -> NopperSettings:
    """Load the configuration from the global config file."""
    if not CONFIG_FILE.exists():
        return NopperSettings()

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return NopperSettings(**data)
    except (json.JSONDecodeError, ValueError):

        return NopperSettings()

def save_config(settings: NopperSettings) -> None:
    """Save the configuration to the global config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:

        f.write(settings.model_dump_json(indent=2))

def update_config(key: str, value: Any) -> None:
    """Update a specific configuration key."""
    settings = load_config()
    if hasattr(settings, key):

        field_info = NopperSettings.model_fields.get(key)
        if field_info:
            expected_type = field_info.annotation
            try:
                if expected_type is int:
                    value = int(value)
                elif expected_type is float:
                    value = float(value)
                elif expected_type is str:
                    value = str(value)
            except ValueError:
                raise ValueError(f"Invalid type for {key}. Expected {expected_type}")

        setattr(settings, key, value)
        save_config(settings)
    else:
        raise KeyError(f"Configuration key '{key}' not found.")

def reset_config() -> None:
    """Reset configuration to defaults."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

