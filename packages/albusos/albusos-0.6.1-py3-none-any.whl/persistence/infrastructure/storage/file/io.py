"""Low-level filesystem/JSON helpers for the file-backed Studio store."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


def utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


def safe_segment(s: str) -> str:
    return str(s).replace("/", "_").replace("\\", "_").replace(":", "_")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write JSON to `path` (best-effort).

    Uses a temp file in the same directory and `os.replace` for atomic swap.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), prefix=path.name, suffix=".tmp"
    ) as f:
        f.write(data)
        tmp_name = f.name
    os.replace(tmp_name, str(path))


def read_json_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        v = json.loads(path.read_text())
        return v if isinstance(v, dict) else None
    except Exception:
        return None


__all__ = ["utcnow_iso", "safe_segment", "atomic_write_json", "read_json_optional"]
