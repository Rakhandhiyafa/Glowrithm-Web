"""Runtime settings read from environment variables (see backend/.env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value) if value else default


@dataclass(frozen=True)
class Settings:
    model_path: Path = field(default_factory=lambda: _env_path("GLOWRITHM_MODEL_PATH", BACKEND_DIR / "models" / "model.keras"))
    meta_path: Path | None = field(default_factory=lambda: Path(os.environ["GLOWRITHM_META_PATH"]) if os.getenv("GLOWRITHM_META_PATH") else None)
    kb_path: Path = field(default_factory=lambda: _env_path("GLOWRITHM_KB_PATH", BACKEND_DIR / "app" / "data" / "knowledge_base.json"))
    demo_mode: bool = field(default_factory=lambda: _env_bool("GLOWRITHM_DEMO_MODE"))
    require_face: bool = field(default_factory=lambda: _env_bool("GLOWRITHM_REQUIRE_FACE"))
    quality_gate: str = field(default_factory=lambda: os.getenv("GLOWRITHM_QUALITY_GATE", "reject").strip().lower())
    max_upload_mb: float = field(default_factory=lambda: float(os.getenv("GLOWRITHM_MAX_UPLOAD_MB", "8")))
    low_confidence: float = field(default_factory=lambda: float(os.getenv("GLOWRITHM_LOW_CONFIDENCE", "0.60")))
    display_size: int = field(default_factory=lambda: int(os.getenv("GLOWRITHM_DISPLAY_SIZE", "384")))
    api_key: str | None = field(default_factory=lambda: os.getenv("GLOWRITHM_API_KEY") or None)
    serve_web: bool = field(default_factory=lambda: _env_bool("GLOWRITHM_SERVE_WEB", True))
    web_dir: Path = field(default_factory=lambda: _env_path("GLOWRITHM_WEB_DIR", BACKEND_DIR.parent / "web"))
    cors_origins: list[str] = field(default_factory=lambda: [
        origin.strip() for origin in os.getenv("GLOWRITHM_CORS_ORIGINS", "*").split(",") if origin.strip()])

    @property
    def resolved_meta_path(self) -> Path:
        return self.meta_path or self.model_path.with_name("model_meta.json")


def get_settings() -> Settings:
    return Settings()
