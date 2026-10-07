"""Configuration and JSON helpers shared by every script."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CLASS_NAMES = ["dry", "normal", "oily"]


def load_config(path: str | Path) -> dict[str, Any]:
    """Load config.yaml; entries under `paths` are resolved relative to the config file."""
    path = Path(path).resolve()
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    base = path.parent
    cfg["paths"] = {key: str((base / value).resolve()) for key, value in cfg.get("paths", {}).items()}
    cfg["_config_path"] = str(path)
    return cfg


def meta_path_for(model_path: str | Path) -> Path:
    """model_meta.json always sits next to the model file."""
    return Path(model_path).with_name("model_meta.json")


def save_json(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)
