"""Folder CRUD/query operations for the file-backed Studio store."""

from __future__ import annotations

from typing import Any

from persistence.infrastructure.storage.file.io import (
    atomic_write_json,
    read_json_optional,
    safe_segment,
    utcnow_iso,
)
from persistence.infrastructure.storage.file.state import FileStoreState


def folder_path(state: FileStoreState, folder_id: str):
    return state.folders / f"{safe_segment(folder_id)}.json"


def folder_path_ws(state: FileStoreState, workspace_id: str, folder_id: str):
    return state.ws_folders_dir(workspace_id) / f"{safe_segment(folder_id)}.json"


def get_folder(state: FileStoreState, folder_id: str) -> dict[str, Any] | None:
    folder = read_json_optional(folder_path(state, folder_id))
    if not folder:
        return None
    ws_id = str(folder.get("workspace_id") or "")
    if ws_id:
        ws_folder = read_json_optional(folder_path_ws(state, ws_id, folder_id))
        if ws_folder:
            return ws_folder
    return folder


def upsert_folder(state: FileStoreState, folder: dict[str, Any]) -> dict[str, Any]:
    folder_id = str(folder.get("id") or "")
    if not folder_id:
        raise ValueError("folder.id is required")
    ws_id = str(folder.get("workspace_id") or "")
    if not ws_id:
        raise ValueError("folder.workspace_id is required")

    now = utcnow_iso()
    existing_global = read_json_optional(folder_path(state, folder_id)) or {}
    existing_ws = read_json_optional(folder_path_ws(state, ws_id, folder_id)) or {}
    merged = {
        **existing_global,
        **existing_ws,
        **folder,
        "id": folder_id,
        "workspace_id": ws_id,
        "updated_at": now,
        "created_at": existing_global.get("created_at")
        or existing_ws.get("created_at")
        or folder.get("created_at")
        or now,
    }
    atomic_write_json(folder_path(state, folder_id), merged)
    atomic_write_json(folder_path_ws(state, ws_id, folder_id), merged)
    return merged


def list_folders(
    state: FileStoreState,
    *,
    workspace_id: str,
    parent_id: str | None = None,
    include_deleted: bool = False,
) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for path in state.ws_folders_dir(workspace_id).glob("*.json"):
        f = read_json_optional(path)
        if not f:
            continue
        fid = str(f.get("id") or "")
        if fid:
            by_id[fid] = f
    for path in state.folders.glob("*.json"):
        f = read_json_optional(path)
        if not f:
            continue
        if f.get("workspace_id") != workspace_id:
            continue
        fid = str(f.get("id") or "")
        if fid:
            by_id.setdefault(fid, f)

    out: list[dict[str, Any]] = []
    for f in by_id.values():
        if not include_deleted and f.get("deleted_at") is not None:
            continue
        if parent_id is not None and f.get("parent_id") != parent_id:
            continue
        if parent_id is None and f.get("parent_id") is not None:
            continue
        out.append(f)
    out.sort(
        key=lambda d: str(d.get("updated_at") or d.get("created_at") or ""),
        reverse=True,
    )
    return out


def list_all_folders(
    state: FileStoreState, *, workspace_id: str, include_deleted: bool = False
) -> list[dict[str, Any]]:
    """List all folders in a workspace (ignores parent filtering)."""

    by_id: dict[str, dict[str, Any]] = {}
    for path in state.ws_folders_dir(workspace_id).glob("*.json"):
        f = read_json_optional(path)
        if not f:
            continue
        fid = str(f.get("id") or "")
        if fid:
            by_id[fid] = f
    for path in state.folders.glob("*.json"):
        f = read_json_optional(path)
        if not f:
            continue
        if f.get("workspace_id") != workspace_id:
            continue
        fid = str(f.get("id") or "")
        if fid:
            by_id.setdefault(fid, f)
    out = [f for f in by_id.values() if include_deleted or f.get("deleted_at") is None]
    out.sort(
        key=lambda d: str(d.get("updated_at") or d.get("created_at") or ""),
        reverse=True,
    )
    return out


__all__ = ["get_folder", "upsert_folder", "list_folders", "list_all_folders"]
