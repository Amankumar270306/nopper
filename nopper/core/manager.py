import json
from pathlib import Path

from nopper.config import CONFIG_DIR
from nopper.core.config import WrapperConfig
from nopper.core.exceptions import WrapperNotFoundError

WRAPPERS_DIR = CONFIG_DIR / "wrappers"

class WrapperManager:
    @staticmethod
    def _get_path(name: str) -> Path:
        return WRAPPERS_DIR / f"{name}.json"

    @staticmethod
    def get(name: str) -> WrapperConfig:
        path = WrapperManager._get_path(name)
        if not path.exists():
            raise WrapperNotFoundError(f"Wrapper '{name}' not found at {path}")
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return WrapperConfig(**data)
        except Exception as e:
            raise ValueError(f"Failed to load wrapper '{name}': {e}")

    @staticmethod
    def save(config: WrapperConfig) -> None:
        WRAPPERS_DIR.mkdir(parents=True, exist_ok=True)
        path = WrapperManager._get_path(config.name)
        with open(path, "w") as f:
            f.write(config.model_dump_json(indent=2))

    @staticmethod
    def delete(name: str) -> bool:
        path = WrapperManager._get_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    @staticmethod
    def list() -> list[str]:
        if not WRAPPERS_DIR.exists():
            return []
        wrappers = []
        for file in WRAPPERS_DIR.glob("*.json"):
            wrappers.append(file.stem)
        return sorted(wrappers)
