"""Revision operations for the file-backed Studio store."""

from __future__ import annotations

from typing import Any

from persistence.infrastructure.storage.file.io import (
    atomic_write_json,
    read_json_optional,
    safe_segment,
    utcnow_iso,
)
from persistence.infrastructure.storage.file.state import FileStoreState


def rev_path(state: FileStoreState, doc_id: str, rev_id: str):
    return state.revs / safe_segment(doc_id) / f"{safe_segment(rev_id)}.json"


def rev_path_ws(state: FileStoreState, workspace_id: str, doc_id: str, rev_id: str):
    return (
        state.ws_revs_dir(workspace_id)
        / safe_segment(doc_id)
        / f"{safe_segment(rev_id)}.json"
    )


def write_revision(
    state: FileStoreState,
    *,
    doc: dict[str, Any] | None,
    doc_id: str,
    rev_id: str,
    content: dict[str, Any],
) -> dict[str, Any]:
    if not doc_id:
        raise ValueError("doc_id is required")
    if not rev_id:
        raise ValueError("rev_id is required")
    now = utcnow_iso()
    payload = {
        "doc_id": doc_id,
        "rev_id": rev_id,
        "created_at": now,
        "content": content,
    }
    base = state.revs / safe_segment(doc_id)
    base.mkdir(parents=True, exist_ok=True)
    atomic_write_json(base / f"{safe_segment(rev_id)}.json", payload)

    # Workspace-scoped mirror (preferred).
    ws_id = str((doc or {}).get("workspace_id") or "")
    if ws_id:
        ws_base = state.ws_revs_dir(ws_id) / safe_segment(doc_id)
        ws_base.mkdir(parents=True, exist_ok=True)
        atomic_write_json(ws_base / f"{safe_segment(rev_id)}.json", payload)
    return payload


def get_revision(
    state: FileStoreState, *, doc: dict[str, Any] | None, doc_id: str, rev_id: str
) -> dict[str, Any] | None:
    ws_id = str((doc or {}).get("workspace_id") or "")
    if ws_id:
        ws_path = rev_path_ws(state, ws_id, doc_id, rev_id)
        v = read_json_optional(ws_path)
        if v:
            return v
    return read_json_optional(rev_path(state, doc_id, rev_id))


__all__ = ["write_revision", "get_revision"]
