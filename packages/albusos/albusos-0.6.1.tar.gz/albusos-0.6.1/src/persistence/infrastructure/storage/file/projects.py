"""Project CRUD/query operations for the file-backed Studio store."""

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


def project_path(state: FileStoreState, project_id: str):
    return state.projects / f"{safe_segment(project_id)}.json"


def project_path_ws(state: FileStoreState, workspace_id: str, project_id: str):
    return state.ws_projects_dir(workspace_id) / f"{safe_segment(project_id)}.json"


def get_project(state: FileStoreState, project_id: str) -> dict[str, Any] | None:
    proj = read_json_optional(project_path(state, project_id))
    if not proj:
        return None
    ws_id = str(proj.get("workspace_id") or "")
    if ws_id:
        ws_proj = read_json_optional(project_path_ws(state, ws_id, project_id))
        if ws_proj:
            return ws_proj
    return proj


def upsert_project(state: FileStoreState, project: dict[str, Any]) -> dict[str, Any]:
    pid = str(project.get("id") or "")
    if not pid:
        raise ValueError("project.id is required")
    ws_id = str(project.get("workspace_id") or "")
    if not ws_id:
        raise ValueError("project.workspace_id is required")

    now = utcnow_iso()
    existing = get_project(state, pid) or {}
    merged = {
        **existing,
        **project,
        "id": pid,
        "workspace_id": ws_id,
        "updated_at": now,
        "created_at": existing.get("created_at") or project.get("created_at") or now,
    }

    # Global index + workspace mirror (same pattern as docs/folders).
    atomic_write_json(project_path(state, pid), merged)
    state.ws_projects_dir(ws_id).mkdir(parents=True, exist_ok=True)
    atomic_write_json(project_path_ws(state, ws_id, pid), merged)
    return merged


def list_projects(
    state: FileStoreState, *, workspace_id: str, include_deleted: bool = False
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ws_dir = state.ws_projects_dir(workspace_id)
    ws_dir.mkdir(parents=True, exist_ok=True)
    for path in ws_dir.glob("*.json"):
        try:
            p = json.loads(path.read_text())
        except Exception:
            continue
        if not include_deleted and p.get("deleted_at") is not None:
            continue
        if isinstance(p, dict):
            out.append(p)
    out.sort(
        key=lambda d: str(d.get("updated_at") or d.get("created_at") or ""),
        reverse=True,
    )
    return out


__all__ = ["get_project", "upsert_project", "list_projects"]
