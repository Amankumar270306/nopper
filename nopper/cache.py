"""Caching module for Nopper response caching."""

import hashlib
import json
from typing import Any, Dict, Optional, cast

from nopper.config.paths import CONFIG_DIR

CACHE_DIR = CONFIG_DIR / "cache"


def _get_cache_key(
    prompt: str,
    model: str,
    provider: str,
    tools: Optional[Any] = None,
    tool_choice: Optional[Any] = None,
    **kwargs: Any,
) -> str:
    raw_str = f"{provider}:{model}:{prompt}:{tools}:{tool_choice}:{kwargs}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def get_cached_response(
    prompt: str,
    model: str,
    provider: str,
    tools: Optional[Any] = None,
    tool_choice: Optional[Any] = None,
    **kwargs: Any,
) -> Optional[Dict[str, Any]]:
    """Retrieve cached response if available."""
    key = _get_cache_key(prompt, model, provider, tools=tools, tool_choice=tool_choice, **kwargs)
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cast(Dict[str, Any], json.load(f))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def set_cached_response(
    prompt: str,
    model: str,
    provider: str,
    data: Dict[str, Any],
    tools: Optional[Any] = None,
    tool_choice: Optional[Any] = None,
    **kwargs: Any,
) -> None:
    """Save response to cache."""
    key = _get_cache_key(prompt, model, provider, tools=tools, tool_choice=tool_choice, **kwargs)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def clear_cache() -> int:
    """Clear all cached responses and return count of deleted files."""
    if not CACHE_DIR.exists():
        return 0
    count = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
        count += 1
    return count


def get_cache_stats() -> Dict[str, Any]:
    """Get cache stats (entry count and total size in bytes)."""
    if not CACHE_DIR.exists():
        return {"entries": 0, "size_bytes": 0}
    entries = 0
    total_bytes = 0
    for f in CACHE_DIR.glob("*.json"):
        entries += 1
        total_bytes += f.stat().st_size
    return {"entries": entries, "size_bytes": total_bytes}
