"""Filesystem paths for Nopper configuration."""

from pathlib import Path

CONFIG_DIR = Path.home() / ".nopper"
CONFIG_FILE = CONFIG_DIR / "config.json"
NODES_DIR = CONFIG_DIR / "nodes"
WRAPPERS_DIR = CONFIG_DIR / "wrappers"
