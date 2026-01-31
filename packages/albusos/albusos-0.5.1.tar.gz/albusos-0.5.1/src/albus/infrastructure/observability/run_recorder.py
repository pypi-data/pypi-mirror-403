"""Persist Albus observability events as Studio run summaries + event logs.

This gives Albus a LangSmith-like backbone:
- A stable `run_id` (we use `execution_id`)
- A run summary (status, timestamps)
- An append-only event stream for replay/debugging

Design constraints:
- Best-effort: observability must never break execution.
- Zero new infra: write to the existing `StudioStore` run log APIs when present.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from persistence.domain.contracts.studio import (
    RunStatus,
    StudioRunEvent,
    StudioRunSummary,
)

logger = logging.getLogger(__name__)


def _utc_ms() -> int:
    return int(time.time() * 1000)


def _jsonable(x: Any) -> Any:
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, Enum):
        return x.value
    if is_dataclass(x):
        return _jsonable(asdict(x))
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


class RunRecorder:
    """Subscribe to Albus events and persist them to a StudioStore-like backend."""

    def __init__(self, *, store: Any):
        self._store = store
        self._seq_by_run: dict[str, int] = {}
        # Active spans keyed by (run_id, kind, key)
        # key is pathway_id for pathways, node_id for nodes, and "" for run span.
        self._active_spans: dict[tuple[str, str, str], dict[str, Any]] = {}

    def on_event(self, event: Any) -> None:
        """Event handler (sync) safe to attach via `events.on_all`."""
        try:
            run_id = str(
                getattr(event, "execution_id", None)
                or getattr(event, "turn_id", None)
                or ""
            ).strip()
            if not run_id:
                return

            ts_ms = _utc_ms()
            seq = self._seq_by_run.get(run_id, 0) + 1
            self._seq_by_run[run_id] = seq

            # Upsert summary on first sight of this run.
            if seq == 1:
                self._upsert_summary(
                    run_id=run_id, status=RunStatus.RUNNING, started_at_ms=ts_ms
                )

            ev_type = str(
                getattr(getattr(event, "type", None), "value", None)
                or getattr(event, "type", "")
                or ""
            )
            node_id = getattr(event, "node_id", None)
            payload = _jsonable(event)

            payload_dict = payload if isinstance(payload, dict) else {"event": payload}

            self._append_event(
                run_id=run_id,
                seq=seq,
                ts_ms=ts_ms,
                type_=ev_type or "event",
                node_id=str(node_id) if node_id is not None else None,
                payload=payload_dict,
            )

            # ---- Span synthesis (LangSmith-like tree) ----
            try:
                self._maybe_update_spans(
                    run_id=run_id,
                    ev_type=ev_type,
                    event=event,
                    ts_ms=ts_ms,
                    payload=payload_dict,
                )
            except Exception:
                logger.debug(
                    "RunRecorder span synthesis failed (non-fatal)", exc_info=True
                )

            # Terminal updates
            if ev_type in ("turn_completed", "turn_failed"):
                status = (
                    RunStatus.COMPLETED
                    if ev_type == "turn_completed"
                    else RunStatus.FAILED
                )
                err = (
                    getattr(event, "error", None)
                    if status == RunStatus.FAILED
                    else None
                )
                self._upsert_summary(
                    run_id=run_id,
                    status=status,
                    finished_at_ms=ts_ms,
                    error=str(err) if err else None,
                )
        except Exception:
            logger.debug("RunRecorder dropped event (non-fatal)", exc_info=True)

    def _maybe_update_spans(
        self,
        *,
        run_id: str,
        ev_type: str,
        event: Any,
        ts_ms: int,
        payload: dict[str, Any],
    ) -> None:
        from albus.infrastructure.observability.spans import Span, SpanKind, SpanStatus

        def _emit_span(span: Span, *, phase: str) -> None:
            # Persist spans as run events so they can be queried/replayed.
            self._append_event(
                run_id=run_id,
                seq=self._seq_by_run.get(run_id, 0) + 1,
                ts_ms=ts_ms,
                type_="span",
                node_id=None,
                payload={
                    "phase": str(phase),
                    "span": _jsonable(span),
                },
            )
            self._seq_by_run[run_id] = self._seq_by_run.get(run_id, 0) + 1

        def _active(kind: SpanKind, key: str) -> dict[str, Any] | None:
            return self._active_spans.get((run_id, kind.value, key))

        def _start(
            kind: SpanKind,
            key: str,
            name: str,
            parent_span_id: str | None,
            attrs: dict[str, Any] | None = None,
            *,
            explicit_span_id: str | None = None,
            inputs: dict[str, Any] | None = None,
        ) -> str:
            # Use explicit span_id from VM if provided, otherwise generate
            span_id = explicit_span_id or f"{kind.value}:{key or run_id}"
            self._active_spans[(run_id, kind.value, key)] = {
                "span_id": span_id,
                "start_ms": ts_ms,
                "parent_span_id": parent_span_id,
                "name": name,
                "attrs": attrs or {},
                "inputs": inputs,
            }
            _emit_span(
                Span(
                    span_id=span_id,
                    run_id=run_id,
                    parent_span_id=parent_span_id,
                    kind=kind,
                    name=name,
                    start_ms=ts_ms,
                    attributes=attrs or {},
                    inputs=inputs,
                ),
                phase="start",
            )
            return span_id

        def _end(
            kind: SpanKind,
            key: str,
            *,
            status: SpanStatus = SpanStatus.OK,
            error: str | None = None,
            duration_ms: float | None = None,
            outputs: dict[str, Any] | None = None,
        ) -> None:
            st = _active(kind, key)
            if not st:
                return
            start_ms = int(st.get("start_ms") or ts_ms)
            end_ms = (
                ts_ms if duration_ms is None else int(start_ms + float(duration_ms))
            )
            span_id = str(st.get("span_id") or "")
            parent_span_id = st.get("parent_span_id")
            name = str(st.get("name") or "")
            attrs = dict(st.get("attrs") or {})
            inputs = st.get("inputs")
            _emit_span(
                Span(
                    span_id=span_id,
                    run_id=run_id,
                    parent_span_id=parent_span_id,
                    kind=kind,
                    name=name,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    status=status,
                    error=error,
                    attributes=attrs,
                    inputs=inputs,
                    outputs=outputs,
                ),
                phase="end",
            )
            self._active_spans.pop((run_id, kind.value, key), None)

        # Run span (root) - supports both turn-based and execution-based events
        if ev_type == "turn_started":
            _start(
                SpanKind.RUN,
                "",
                "turn",
                parent_span_id=None,
                attrs={"thread_id": getattr(event, "thread_id", None)},
            )
        if ev_type == "turn_completed":
            _end(
                SpanKind.RUN,
                "",
                status=SpanStatus.OK,
                duration_ms=getattr(event, "duration_ms", None),
            )
        if ev_type == "turn_failed":
            _end(
                SpanKind.RUN,
                "",
                status=SpanStatus.ERROR,
                error=str(getattr(event, "error", "") or ""),
                duration_ms=getattr(event, "duration_ms", None),
            )

        # Execution-based run spans (from PathwayVM direct execution)
        if ev_type == "execution_started":
            explicit_span_id = payload.get("span_id")
            run_inputs = payload.get("inputs")
            pathway_info = payload.get("pathway", {})
            attrs = {}
            if pathway_info:
                attrs["pathway_id"] = pathway_info.get("pathway_id")
                attrs["node_count"] = pathway_info.get("node_count")
            _start(
                SpanKind.RUN,
                "",
                "execution",
                parent_span_id=None,
                attrs=attrs,
                explicit_span_id=explicit_span_id,
                inputs=run_inputs,
            )
        if ev_type == "execution_completed":
            ok = payload.get("success", payload.get("status") == "completed")
            run_outputs = payload.get("outputs")
            metrics = payload.get("metrics", {})
            _end(
                SpanKind.RUN,
                "",
                status=SpanStatus.OK if ok else SpanStatus.ERROR,
                error=payload.get("error"),
                duration_ms=payload.get("duration_ms"),
                outputs=(
                    {"result": run_outputs, "metrics": metrics} if run_outputs else None
                ),
            )

        # Pathway span
        pathway_id = str(getattr(event, "pathway_id", "") or "").strip()
        if ev_type == "pathway_started" and pathway_id:
            parent = (_active(SpanKind.RUN, "") or {}).get("span_id")
            _start(
                SpanKind.PATHWAY,
                pathway_id,
                f"pathway:{pathway_id}",
                parent_span_id=str(parent) if parent else None,
            )
        if ev_type == "pathway_completed" and pathway_id:
            ok = bool(getattr(event, "success", True))
            _end(
                SpanKind.PATHWAY,
                pathway_id,
                status=SpanStatus.OK if ok else SpanStatus.ERROR,
                error=str(getattr(event, "error", "") or "") if not ok else None,
                duration_ms=getattr(event, "duration_ms", None),
            )

        # Node span - use explicit span_id and parent_span_id from VM if available
        nid = str(getattr(event, "node_id", "") or "").strip()
        if ev_type == "node_started" and nid:
            # Try to get explicit span info from payload
            explicit_span_id = (
                payload.get("span_id") if isinstance(payload, dict) else None
            )
            explicit_parent = (
                payload.get("parent_span_id") if isinstance(payload, dict) else None
            )
            node_type = (
                payload.get("node_type", "") if isinstance(payload, dict) else ""
            )
            node_inputs = payload.get("inputs") if isinstance(payload, dict) else None

            # Fall back to synthesized parent if not explicit
            parent = explicit_parent or (
                _active(SpanKind.PATHWAY, pathway_id) or _active(SpanKind.RUN, "") or {}
            ).get("span_id")

            attrs = {"pathway_id": pathway_id} if pathway_id else {}
            if node_type:
                attrs["node_type"] = node_type

            _start(
                SpanKind.NODE,
                nid,
                f"node:{nid}",
                parent_span_id=str(parent) if parent else None,
                attrs=attrs,
                explicit_span_id=explicit_span_id,
                inputs=node_inputs,
            )
        if ev_type == "node_completed" and nid:
            node_outputs = payload.get("outputs") if isinstance(payload, dict) else None
            _end(
                SpanKind.NODE,
                nid,
                status=SpanStatus.OK,
                duration_ms=getattr(event, "duration_ms", None),
                outputs=node_outputs,
            )
        if ev_type == "node_failed" and nid:
            node_outputs = payload.get("outputs") if isinstance(payload, dict) else None
            _end(
                SpanKind.NODE,
                nid,
                status=SpanStatus.ERROR,
                error=str(getattr(event, "error", "") or ""),
                duration_ms=getattr(event, "duration_ms", None),
                outputs=node_outputs,
            )

        # Tool span
        if ev_type in ("tool_called", "tool_completed", "tool_failed"):
            tool_name = str(getattr(event, "tool_name", "") or "")
            call_id = str(getattr(event, "call_id", "") or "") or tool_name
            parent = (
                _active(SpanKind.NODE, nid)
                or _active(SpanKind.PATHWAY, pathway_id)
                or _active(SpanKind.RUN, "")
                or {}
            ).get("span_id")
            if ev_type == "tool_called":
                _start(
                    SpanKind.TOOL,
                    call_id,
                    f"tool:{tool_name}",
                    parent_span_id=str(parent) if parent else None,
                    attrs={"tool": tool_name},
                )
            elif ev_type == "tool_completed":
                _end(
                    SpanKind.TOOL,
                    call_id,
                    status=SpanStatus.OK,
                    duration_ms=getattr(event, "duration_ms", None),
                )
            else:
                _end(
                    SpanKind.TOOL,
                    call_id,
                    status=SpanStatus.ERROR,
                    error=str(getattr(event, "error", "") or ""),
                    duration_ms=getattr(event, "duration_ms", None),
                )

        # LLM span
        if ev_type in ("llm_request", "llm_response"):
            call_id = str(getattr(event, "call_id", "") or "") or "llm"
            model = str(getattr(event, "model", "") or "")
            parent = (
                _active(SpanKind.NODE, nid)
                or _active(SpanKind.PATHWAY, pathway_id)
                or _active(SpanKind.RUN, "")
                or {}
            ).get("span_id")
            if ev_type == "llm_request":
                _start(
                    SpanKind.LLM,
                    call_id,
                    f"llm:{model or 'unknown'}",
                    parent_span_id=str(parent) if parent else None,
                    attrs={"model": model},
                )
            else:
                _end(
                    SpanKind.LLM,
                    call_id,
                    status=SpanStatus.OK,
                    duration_ms=getattr(event, "duration_ms", None),
                )

    def _upsert_summary(
        self,
        *,
        run_id: str,
        status: RunStatus,
        started_at_ms: int | None = None,
        finished_at_ms: int | None = None,
        error: str | None = None,
    ) -> None:
        try:
            # Best-effort merge with existing summary if present.
            existing = None
            try:
                get_fn = getattr(self._store, "get_run_summary", None)
                if callable(get_fn):
                    existing = get_fn(run_id=run_id)
            except Exception:
                existing = None

            summary = StudioRunSummary(
                run_id=run_id,
                workspace_id=(
                    getattr(existing, "workspace_id", None) if existing else None
                ),
                doc_id=getattr(existing, "doc_id", None) if existing else None,
                status=status,
                started_at_ms=started_at_ms
                or (getattr(existing, "started_at_ms", None) if existing else None),
                finished_at_ms=finished_at_ms
                or (getattr(existing, "finished_at_ms", None) if existing else None),
                error=error or (getattr(existing, "error", None) if existing else None),
            )
            upsert_fn = getattr(self._store, "upsert_run_summary", None)
            if callable(upsert_fn):
                upsert_fn(summary=summary)
        except Exception:
            logger.debug(
                "RunRecorder failed to upsert summary (non-fatal)", exc_info=True
            )

    def _append_event(
        self,
        *,
        run_id: str,
        seq: int,
        ts_ms: int,
        type_: str,
        node_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        try:
            append_fn = getattr(self._store, "append_run_event", None)
            if not callable(append_fn):
                return
            append_fn(
                event=StudioRunEvent(
                    run_id=run_id,
                    seq=int(seq),
                    ts_ms=int(ts_ms),
                    type=str(type_),
                    node_id=str(node_id) if node_id else None,
                    payload=dict(payload),
                )
            )
        except Exception:
            logger.debug(
                "RunRecorder failed to append event (non-fatal)", exc_info=True
            )


__all__ = ["RunRecorder"]
