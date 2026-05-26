from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resolve_app_base_dir(base_dir: Optional[Path] = None) -> Path:
    if base_dir is not None:
        return Path(base_dir)
    return app_base_dir()


def default_log_path(base_dir: Optional[Path] = None) -> Path:
    return resolve_app_base_dir(base_dir) / "logs" / "editor.log"


def default_settings_path(base_dir: Optional[Path] = None) -> Path:
    return resolve_app_base_dir(base_dir) / "settings.ini"
