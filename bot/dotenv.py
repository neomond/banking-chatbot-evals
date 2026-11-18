"""Load repo-root .env into os.environ without overriding variables already set."""
from __future__ import annotations

import os
from pathlib import Path

from .kb import ROOT

_LOADED = False


def load_dotenv(path: Path | None = None) -> None:
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    env_path = path or (ROOT / ".env")
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value
