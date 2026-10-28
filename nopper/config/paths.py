"""Filesystem paths for Nopper configuration."""

import os
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".nopper"
CONFIG_FILE = CONFIG_DIR / "config.json"
NODES_DIR = CONFIG_DIR / "nodes"
WRAPPERS_DIR = CONFIG_DIR / "wrappers"


def get_venv_dir() -> Path | None:
    """Return the active virtual environment directory if one exists, else None."""
    if "VIRTUAL_ENV" in os.environ and os.environ["VIRTUAL_ENV"]:
        p = Path(os.environ["VIRTUAL_ENV"])
        if p.exists():
            return p

    if getattr(sys, "base_prefix", None) and sys.prefix != sys.base_prefix:
        p = Path(sys.prefix)
        if p.exists():
            return p

    local_venv = Path.cwd() / ".venv"
    if local_venv.is_dir():
        return local_venv

    return None


def get_venv_nodes_dir() -> Path | None:
    """Return the nodes storage directory inside the active virtual environment."""
    venv = get_venv_dir()
    if venv:
        return venv / ".nopper" / "nodes"
    return None


def get_machine_nodes_dir(base_path: Path | str | None = None) -> Path:
    """Return the nodes storage directory for the machine/working directory."""
    base = Path(base_path) if base_path else Path.cwd()
    if base.is_file() or str(base).endswith(".json"):
        return base.parent
    if base.name == "nodes":
        return base
    return base / ".nopper" / "nodes"

