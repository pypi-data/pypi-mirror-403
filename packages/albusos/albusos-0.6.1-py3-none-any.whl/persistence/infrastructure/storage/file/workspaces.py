"""Workspace CRUD/query operations for the file-backed Studio store."""

from __future__ import annotations

import json
from typing import Any

from persistence.infrastructure.storage.file.io import (
    atomic_write_json,
    read_json_optional,
    safe_segment,
    utcnow_iso,
)
from persistence.infrastructure.storage.file.state import FileStoreState


def workspace_path(state: FileStoreState, workspace_id: str):
    return state.workspaces / f"{safe_segment(workspace_id)}.json"


def get_workspace(state: FileStoreState, workspace_id: str) -> dict[str, Any] | None:
    return read_json_optional(workspace_path(state, workspace_id))


def upsert_workspace(state: FileStoreState, ws: dict[str, Any]) -> dict[str, Any]:
    ws_id = str(ws.get("id") or "")
    if not ws_id:
        raise ValueError("workspace.id is required")
    now = utcnow_iso()
    existing = get_workspace(state, ws_id) or {}
    merged = {
        **existing,
        **ws,
        "id": ws_id,
        "updated_at": now,
        "created_at": existing.get("created_at") or ws.get("created_at") or now,
    }
    atomic_write_json(workspace_path(state, ws_id), merged)
    return merged


def list_workspaces(
    state: FileStoreState, *, include_deleted: bool = False
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in state.workspaces.glob("*.json"):
        try:
            ws = json.loads(path.read_text())
        except Exception:
            continue
        if not include_deleted and ws.get("deleted_at") is not None:
            continue
        if isinstance(ws, dict):
            out.append(ws)
    out.sort(
        key=lambda d: str(d.get("updated_at") or d.get("created_at") or ""),
        reverse=True,
    )
    return out


__all__ = ["get_workspace", "upsert_workspace", "list_workspaces"]
