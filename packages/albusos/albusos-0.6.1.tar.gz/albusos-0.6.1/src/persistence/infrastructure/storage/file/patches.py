"""Patch idempotency + commit operations for the file-backed Studio store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from persistence.infrastructure.storage.file.io import (
    atomic_write_json,
    read_json_optional,
    safe_segment,
)
from persistence.infrastructure.storage.file.state import FileStoreState


def idempotency_path(state: FileStoreState, doc_id: str) -> Path:
    return state.idempotency / f"{safe_segment(doc_id)}.json"


def idempotency_path_ws(state: FileStoreState, workspace_id: str, doc_id: str) -> Path:
    return state.ws_idempotency_dir(workspace_id) / f"{safe_segment(doc_id)}.json"


def get_patch_idempotency(
    state: FileStoreState,
    *,
    doc: dict[str, Any] | None,
    doc_id: str,
    client_patch_id: str,
) -> dict[str, Any] | None:
    ws_id = str((doc or {}).get("workspace_id") or "")

    paths: list[Path] = []
    if ws_id:
        paths.append(idempotency_path_ws(state, ws_id, doc_id))
    paths.append(idempotency_path(state, doc_id))

    for path in paths:
        payload = read_json_optional(path)
        if not payload:
            continue
        rec = (payload.get("records") or {}).get(str(client_patch_id))
        return rec if isinstance(rec, dict) else None
    return None


def put_patch_idempotency(
    state: FileStoreState,
    *,
    doc: dict[str, Any] | None,
    doc_id: str,
    client_patch_id: str,
    record: dict[str, Any],
) -> dict[str, Any]:
    ws_id = str((doc or {}).get("workspace_id") or "")

    target_paths: list[Path] = []
    if ws_id:
        target_paths.append(idempotency_path_ws(state, ws_id, doc_id))
    target_paths.append(idempotency_path(state, doc_id))

    # Read from the first existing location (prefer workspace), then write to all targets.
    payload: dict[str, Any] = {"doc_id": str(doc_id), "records": {}}
    for p in target_paths:
        existing_payload = read_json_optional(p)
        if existing_payload:
            payload = existing_payload
            break

    records = payload.get("records")
    if not isinstance(records, dict):
        records = {}
    cid = str(client_patch_id)
    existing = records.get(cid)
    if isinstance(existing, dict):
        return existing
    records[cid] = dict(record)
    payload["records"] = records

    for p in target_paths:
        atomic_write_json(p, payload)
    return dict(record)


__all__ = ["get_patch_idempotency", "put_patch_idempotency"]
