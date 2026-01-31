"""File-backed run summaries + append-only run event log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persistence.domain.contracts.studio import StudioRunEvent, StudioRunSummary
from persistence.infrastructure.storage.file.io import (
    atomic_write_json,
    read_json_optional,
    safe_segment,
    utcnow_iso,
)
from persistence.infrastructure.storage.file.state import FileStoreState


def _summary_path(state: FileStoreState, run_id: str) -> Path:
    return state.runs / f"{safe_segment(run_id)}.summary.json"


def _events_path(state: FileStoreState, run_id: str) -> Path:
    return state.runs / f"{safe_segment(run_id)}.events.jsonl"


def _ws_summary_path(state: FileStoreState, workspace_id: str, run_id: str) -> Path:
    return state.ws_runs_dir(workspace_id) / f"{safe_segment(run_id)}.summary.json"


def upsert_run_summary(
    state: FileStoreState, *, summary: StudioRunSummary
) -> StudioRunSummary:
    data = summary.model_dump(mode="json")
    data["updated_at"] = utcnow_iso()

    atomic_write_json(_summary_path(state, summary.run_id), data)
    if summary.workspace_id:
        ws_path = _ws_summary_path(state, summary.workspace_id, summary.run_id)
        ws_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(ws_path, data)
    return StudioRunSummary.model_validate(data)


def get_run_summary(state: FileStoreState, *, run_id: str) -> StudioRunSummary | None:
    data = read_json_optional(_summary_path(state, run_id))
    if not data:
        return None
    try:
        return StudioRunSummary.model_validate(data)
    except Exception:
        return None


def list_run_summaries(
    state: FileStoreState,
    *,
    workspace_id: str | None = None,
    doc_id: str | None = None,
    limit: int = 50,
) -> list[StudioRunSummary]:
    # Prefer workspace-scoped directory when possible (avoids cross-tenant scanning on disk).
    scan_dir = state.ws_runs_dir(workspace_id) if workspace_id else state.runs
    if not scan_dir.exists():
        return []
    out: list[StudioRunSummary] = []
    for p in scan_dir.glob("*.summary.json"):
        data = read_json_optional(p)
        if not data:
            continue
        try:
            s = StudioRunSummary.model_validate(data)
        except Exception:
            continue
        if workspace_id and (s.workspace_id != workspace_id):
            continue
        if doc_id and (s.doc_id != doc_id):
            continue
        out.append(s)
    # Sort newest-ish by finished/start time then truncate.
    out.sort(key=lambda s: (s.finished_at_ms or 0, s.started_at_ms or 0), reverse=True)
    return out[: max(1, int(limit or 50))]


def append_run_event(state: FileStoreState, *, event: StudioRunEvent) -> StudioRunEvent:
    line = json.dumps(event.model_dump(mode="json"), ensure_ascii=False)
    path = _events_path(state, event.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return event


def list_run_events(
    state: FileStoreState,
    *,
    run_id: str,
    after_seq: int | None = None,
    limit: int = 500,
) -> list[StudioRunEvent]:
    path = _events_path(state, run_id)
    if not path.exists():
        return []
    out: list[StudioRunEvent] = []
    after = int(after_seq) if isinstance(after_seq, int) else None
    max_n = max(1, int(limit or 500))
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                raw: Any = json.loads(line)
                ev = StudioRunEvent.model_validate(raw)
            except Exception:
                continue
            if after is not None and ev.seq <= after:
                continue
            out.append(ev)
            if len(out) >= max_n:
                break
    return out


__all__ = [
    "append_run_event",
    "get_run_summary",
    "list_run_events",
    "list_run_summaries",
    "upsert_run_summary",
]
