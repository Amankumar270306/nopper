"""Nopper configuration module."""

from nopper.config.loader import load_config, reset_config, save_config, update_config
from nopper.config.paths import CONFIG_DIR, CONFIG_FILE, NODES_DIR, WRAPPERS_DIR
from nopper.config.settings import NodeConfig, NopperSettings

# Backwards compatibility alias
MyAISettings = NopperSettings

__all__ = [
    "CONFIG_DIR",
    "CONFIG_FILE",
    "NODES_DIR",
    "WRAPPERS_DIR",
    "MyAISettings",
    "NodeConfig",
    "NopperSettings",
    "load_config",
    "reset_config",
    "save_config",
    "update_config",
]
