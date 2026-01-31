"""Document CRUD/query operations for the file-backed Studio store."""

from __future__ import annotations

from typing import Any

from persistence.infrastructure.storage.file.io import (
    atomic_write_json,
    read_json_optional,
    safe_segment,
    utcnow_iso,
)
from persistence.infrastructure.storage.file.state import FileStoreState


def doc_path(state: FileStoreState, doc_id: str):
    return state.docs / f"{safe_segment(doc_id)}.json"


def doc_path_ws(state: FileStoreState, workspace_id: str, doc_id: str):
    return state.ws_docs_dir(workspace_id) / f"{safe_segment(doc_id)}.json"


def get_document(state: FileStoreState, doc_id: str) -> dict[str, Any] | None:
    doc = read_json_optional(doc_path(state, doc_id))
    if not doc:
        return None
    ws_id = str(doc.get("workspace_id") or "")
    if ws_id:
        ws_doc = read_json_optional(doc_path_ws(state, ws_id, doc_id))
        if ws_doc:
            return ws_doc
    return doc


def upsert_document(state: FileStoreState, doc: dict[str, Any]) -> dict[str, Any]:
    doc_id = str(doc.get("id") or "")
    if not doc_id:
        raise ValueError("document.id is required")

    now = utcnow_iso()
    existing = read_json_optional(doc_path(state, doc_id)) or {}
    ws_hint = str(doc.get("workspace_id") or existing.get("workspace_id") or "")
    existing_ws = (
        read_json_optional(doc_path_ws(state, ws_hint, doc_id)) if ws_hint else None
    )
    existing_ws = existing_ws or {}
    merged = {
        **existing,
        **existing_ws,
        **doc,
        "id": doc_id,
        "updated_at": now,
        "created_at": existing.get("created_at")
        or existing_ws.get("created_at")
        or doc.get("created_at")
        or now,
    }

    # Global index: always maintained for O(1) doc lookup by id.
    atomic_write_json(doc_path(state, doc_id), merged)

    # Workspace mirror: best-effort physical scoping on disk.
    ws_id = str(merged.get("workspace_id") or "")
    if ws_id:
        atomic_write_json(doc_path_ws(state, ws_id, doc_id), merged)
    return merged


def list_documents(
    state: FileStoreState,
    *,
    workspace_id: str | None = None,
    parent_id: str | None = None,
    include_deleted: bool = False,
) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}

    # Prefer workspace mirrors when a workspace is specified.
    if workspace_id:
        for path in state.ws_docs_dir(workspace_id).glob("*.json"):
            doc = read_json_optional(path)
            if not doc:
                continue
            did = str(doc.get("id") or "")
            if did:
                by_id[did] = doc

    # Always include global index (dedupe safety).
    for path in state.docs.glob("*.json"):
        doc = read_json_optional(path)
        if not doc:
            continue
        did = str(doc.get("id") or "")
        if not did:
            continue
        if workspace_id is not None and doc.get("workspace_id") != workspace_id:
            continue
        by_id.setdefault(did, doc)

    out: list[dict[str, Any]] = []
    for doc in by_id.values():
        if not include_deleted and doc.get("deleted_at") is not None:
            continue
        if parent_id is not None and doc.get("parent_id") != parent_id:
            continue
        if parent_id is None and doc.get("parent_id") is not None:
            continue
        out.append(doc)

    out.sort(
        key=lambda d: str(d.get("updated_at") or d.get("created_at") or ""),
        reverse=True,
    )
    return out


def list_all_documents(
    state: FileStoreState, *, workspace_id: str, include_deleted: bool = False
) -> list[dict[str, Any]]:
    """List all documents in a workspace (ignores folder parent filtering)."""

    by_id: dict[str, dict[str, Any]] = {}
    for path in state.ws_docs_dir(workspace_id).glob("*.json"):
        doc = read_json_optional(path)
        if not doc:
            continue
        did = str(doc.get("id") or "")
        if did:
            by_id[did] = doc
    for path in state.docs.glob("*.json"):
        doc = read_json_optional(path)
        if not doc:
            continue
        if doc.get("workspace_id") != workspace_id:
            continue
        did = str(doc.get("id") or "")
        if did:
            by_id.setdefault(did, doc)
    out = [d for d in by_id.values() if include_deleted or d.get("deleted_at") is None]
    out.sort(
        key=lambda d: str(d.get("updated_at") or d.get("created_at") or ""),
        reverse=True,
    )
    return out


__all__ = ["get_document", "upsert_document", "list_documents", "list_all_documents"]
