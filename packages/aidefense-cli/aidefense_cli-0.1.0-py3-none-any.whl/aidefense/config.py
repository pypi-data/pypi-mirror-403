from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from .models import ProviderConfig


def default_config_path() -> Path:
    return Path.home() / ".aidefense" / "config.json"


def load_provider_config(path: Path | None = None) -> ProviderConfig:
    cfg = ProviderConfig(
        name=os.getenv("AIDEF_PROVIDER", "moonshot"),
        api_key=os.getenv("AIDEF_API_KEY"),
        api_base=os.getenv("AIDEF_API_BASE", "https://api.moonshot.cn/v1"),
        model=os.getenv("AIDEF_MODEL", "moonshot-v1-8k"),
    )

    file_path = path or default_config_path()
    if file_path.exists():
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            cfg = ProviderConfig(**{**asdict(cfg), **data})
        except Exception:
            pass

    return cfg


def save_provider_config(cfg: ProviderConfig, path: Path | None = None) -> None:
    file_path = path or default_config_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
