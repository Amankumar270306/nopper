"""NodeManager — resolves, creates, updates, and deletes execution nodes on disk."""

import json
from pathlib import Path
from typing import Any

from nopper.config.loader import load_config, save_config
from nopper.config.paths import (
    NODES_DIR,
    get_machine_nodes_dir,
    get_venv_nodes_dir,
)
from nopper.node.base import Node
from nopper.node.cached import CachedNode
from nopper.node.config import NodeConfig
from nopper.node.fallback import FallbackNode
from nopper.node.local import LocalNode


def prompt_save_location(default_dir: Path | str | None = None) -> tuple[str, Path]:
    """Interactively prompt user where to save the node: venv or machine.

    If machine is selected, asks for the path with default=current working directory.
    Returns (location_type, resolved_directory_path).
    """
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()
    console.print("\n[bold cyan]Where do you want to save the node?[/bold cyan]")
    console.print("  [bold]1[/bold] - Virtual environment (.venv)")
    console.print("  [bold]2[/bold] - In the machine")

    choice = Prompt.ask(
        "Select storage location",
        choices=["1", "2", "venv", "machine"],
        default="2",
        show_choices=False,
    )

    if choice in ("1", "venv"):
        venv_nodes_dir = get_venv_nodes_dir()
        if venv_nodes_dir is None:
            console.print("[yellow]Warning: No active virtual environment (.venv) detected.[/yellow]")
            local_venv = Path.cwd() / ".venv"
            if local_venv.is_dir():
                venv_nodes_dir = local_venv / ".nopper" / "nodes"
            else:
                fallback = Prompt.ask(
                    "Create local .venv directory or save to machine?",
                    choices=["venv", "machine"],
                    default="machine",
                )
                if fallback == "venv":
                    venv_nodes_dir = local_venv / ".nopper" / "nodes"
                else:
                    choice = "machine"

        if venv_nodes_dir is not None:
            venv_nodes_dir.mkdir(parents=True, exist_ok=True)
            return ("venv", venv_nodes_dir)

    # Machine option (choice 2 or fallback)
    cwd_str = str(default_dir or Path.cwd())
    target_input = Prompt.ask(
        "Enter path to save the node",
        default=cwd_str,
    )
    chosen_path = Path(target_input).expanduser().resolve()
    machine_nodes_dir = get_machine_nodes_dir(chosen_path)
    machine_nodes_dir.mkdir(parents=True, exist_ok=True)
    return ("machine", machine_nodes_dir)


class NodeManager:
    """Manages Node configurations stored in machine, venv, or global directories."""

    _cache: dict[str, Node] = {}

    @classmethod
    def find_node_path(cls, name: str) -> Path | None:
        """Locate the .json configuration file for the given node name."""
        # 1. Check known locations recorded in settings.node_locations
        try:
            settings = load_config()
            if name in settings.node_locations:
                p = Path(settings.node_locations[name])
                if p.exists():
                    return p
        except Exception:
            pass

        # 2. Check current working directory (.nopper/nodes, nodes, ./)
        cwd = Path.cwd()
        candidates = [
            cwd / ".nopper" / "nodes" / f"{name}.json",
            cwd / "nodes" / f"{name}.json",
            cwd / f"{name}.json",
        ]
        for c in candidates:
            if c.exists():
                return c

        # 3. Check active virtual environment
        venv_nodes = get_venv_nodes_dir()
        if venv_nodes and (venv_nodes / f"{name}.json").exists():
            return venv_nodes / f"{name}.json"
        local_venv_nodes = cwd / ".venv" / ".nopper" / "nodes" / f"{name}.json"
        if local_venv_nodes.exists():
            return local_venv_nodes

        # 4. Check global machine directory (~/.nopper/nodes/)
        global_path = NODES_DIR / f"{name}.json"
        if global_path.exists():
            return global_path

        return None

    @classmethod
    def _get_path(cls, name: str) -> Path:
        found = cls.find_node_path(name)
        if found:
            return found
        return NODES_DIR / f"{name}.json"

    @classmethod
    def resolve(cls, name: str | None = None) -> Node:
        """Resolve a Node instance by name (or return default node).

        If node is not found on disk, returns a default LocalNode constructed
        from global settings.
        """
        settings = load_config()
        target_name = name or settings.default_node or "default"

        if target_name in cls._cache:
            return cls._cache[target_name]

        config = cls.get_config(target_name)
        node = cls._build_node(config)
        cls._cache[target_name] = node
        return node

    @classmethod
    def get_config(cls, name: str) -> NodeConfig:
        """Load NodeConfig from disk or generate default."""
        path = cls._get_path(name)
        settings = load_config()

        if not path.exists():
            # Check legacy nodes dict in settings
            if name in settings.nodes:
                legacy_node = settings.nodes[name]
                return NodeConfig(
                    name=name,
                    provider=legacy_node.type or settings.provider,
                    model=legacy_node.model or settings.model,
                    api_key=legacy_node.api_key,
                    base_url=legacy_node.base_url,
                    timeout=legacy_node.timeout or float(settings.timeout),
                )
            # Default fallback config
            api_key = settings.api_keys.get(settings.provider)
            return NodeConfig(
                name=name,
                provider=settings.provider,
                model=settings.model,
                api_key=api_key,
                timeout=float(settings.timeout),
            )

        try:
            with open(path, "r") as f:
                data = json.load(f)
                return NodeConfig(**data)
        except Exception as e:
            raise ValueError(f"Failed to load node '{name}': {e}") from e

    @classmethod
    def save(
        cls,
        config: NodeConfig,
        location: str | None = None,
        path: Path | str | None = None,
    ) -> Path:
        """Save a NodeConfig to disk and invalidate cache.

        Arguments:
            config: The NodeConfig instance.
            location: 'venv' or 'machine' (defaults to cwd if path omitted).
            path: Target directory or file path.
        """
        if path is not None:
            p = Path(path).expanduser().resolve()
            if p.is_file() or str(p).endswith(".json"):
                file_path = p
            else:
                nodes_dir = get_machine_nodes_dir(p)
                file_path = nodes_dir / f"{config.name}.json"
        elif location == "venv":
            venv_nodes_dir = get_venv_nodes_dir() or (Path.cwd() / ".venv" / ".nopper" / "nodes")
            file_path = venv_nodes_dir / f"{config.name}.json"
        elif location == "machine":
            machine_dir = get_machine_nodes_dir(Path.cwd())
            file_path = machine_dir / f"{config.name}.json"
        else:
            NODES_DIR.mkdir(parents=True, exist_ok=True)
            file_path = NODES_DIR / f"{config.name}.json"

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(config.model_dump_json(indent=2))

        # Invalidate in-memory cache
        cls._cache.pop(config.name, None)

        # Record location in config so it is always discoverable across directories
        try:
            settings = load_config()
            settings.node_locations[config.name] = str(file_path.resolve())
            save_config(settings)
        except Exception:
            pass

        return file_path

    @classmethod
    def delete(cls, name: str) -> bool:
        """Delete a Node configuration from disk and configuration registry."""
        path = cls.find_node_path(name) or cls._get_path(name)
        cls._cache.pop(name, None)
        deleted = False
        if path and path.exists():
            path.unlink()
            deleted = True

        try:
            settings = load_config()
            if name in settings.node_locations:
                del settings.node_locations[name]
                save_config(settings)
            if name in settings.nodes:
                del settings.nodes[name]
                save_config(settings)
        except Exception:
            pass

        return deleted

    @classmethod
    def list(cls) -> list[str]:
        """List all unique node names across discoverable locations."""
        names: set[str] = set()

        # From settings.node_locations
        try:
            settings = load_config()
            for name, path_str in settings.node_locations.items():
                if Path(path_str).exists():
                    names.add(name)
            for name in settings.nodes.keys():
                names.add(name)
        except Exception:
            pass

        # From cwd
        for d in [Path.cwd() / ".nopper" / "nodes", Path.cwd() / "nodes"]:
            if d.exists():
                for f in d.glob("*.json"):
                    names.add(f.stem)

        # From venv
        venv_dir = get_venv_nodes_dir()
        if venv_dir and venv_dir.exists():
            for f in venv_dir.glob("*.json"):
                names.add(f.stem)
        local_venv = Path.cwd() / ".venv" / ".nopper" / "nodes"
        if local_venv.exists():
            for f in local_venv.glob("*.json"):
                names.add(f.stem)

        # From global ~/.nopper/nodes/
        if NODES_DIR.exists():
            for f in NODES_DIR.glob("*.json"):
                names.add(f.stem)

        return sorted(list(names))

    @classmethod
    def list_detailed(cls) -> list[dict[str, Any]]:
        """List all discoverable nodes with location and path information."""
        details: list[dict[str, Any]] = []
        for name in cls.list():
            path = cls.find_node_path(name)
            location_type = "unknown"
            if path:
                path_str = str(path)
                venv_dir = get_venv_nodes_dir()
                if venv_dir and str(venv_dir) in path_str:
                    location_type = "venv"
                elif ".venv" in path_str:
                    location_type = "venv"
                elif str(NODES_DIR) in path_str:
                    location_type = "global"
                elif str(Path.cwd()) in path_str:
                    location_type = "machine (working dir)"
                else:
                    location_type = "machine"

            try:
                config = cls.get_config(name)
                details.append({
                    "name": name,
                    "provider": config.provider,
                    "model": config.model,
                    "timeout": config.timeout,
                    "base_url": config.base_url,
                    "location_type": location_type,
                    "path": str(path) if path else "legacy (config.json)",
                })
            except Exception:
                details.append({
                    "name": name,
                    "provider": "unknown",
                    "model": "unknown",
                    "timeout": None,
                    "base_url": None,
                    "location_type": location_type,
                    "path": str(path) if path else "error",
                })
        return details

    @classmethod
    def _build_node(cls, config: NodeConfig) -> Node:
        """Construct the appropriate Node implementation for a config."""
        if config.fallbacks:
            base_node: Node = FallbackNode(config)
        else:
            base_node = LocalNode(config)

        if config.cache_policy.enabled:
            return CachedNode(base_node, config)

        return base_node
