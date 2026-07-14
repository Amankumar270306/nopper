"""NodeManager — resolves, creates, updates, and deletes execution nodes on disk."""

import json
from pathlib import Path

from nopper.config.loader import load_config
from nopper.config.paths import NODES_DIR
from nopper.node.base import Node
from nopper.node.cached import CachedNode
from nopper.node.config import NodeConfig
from nopper.node.fallback import FallbackNode
from nopper.node.local import LocalNode


class NodeManager:
    """Manages Node configurations stored in ~/.nopper/nodes/*.json."""

    _cache: dict[str, Node] = {}

    @staticmethod
    def _get_path(name: str) -> Path:
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
    def save(cls, config: NodeConfig) -> None:
        """Save a NodeConfig to disk and invalidate cache."""
        NODES_DIR.mkdir(parents=True, exist_ok=True)
        path = cls._get_path(config.name)
        with open(path, "w") as f:
            f.write(config.model_dump_json(indent=2))

        # Invalidate in-memory cache
        cls._cache.pop(config.name, None)

    @classmethod
    def delete(cls, name: str) -> bool:
        """Delete a Node configuration from disk."""
        path = cls._get_path(name)
        cls._cache.pop(name, None)
        if path.exists():
            path.unlink()
            return True
        return False

    @classmethod
    def list(cls) -> list[str]:
        """List all node names saved on disk."""
        if not NODES_DIR.exists():
            return []
        return sorted([f.stem for f in NODES_DIR.glob("*.json")])

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
