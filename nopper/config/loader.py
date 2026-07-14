"""Configuration loader and persistence."""

import json
from typing import Any

from nopper.config.paths import CONFIG_DIR, CONFIG_FILE
from nopper.config.settings import NopperSettings


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
