"""Run inspection endpoint handlers.

These endpoints enable Studio to act as a debugger:
- List recent runs
- Get run summary with inputs/outputs
- Inspect span tree (hierarchical execution trace)
- View event stream (append-only log)
- Generate timeline for visualization
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from albus.infrastructure.errors import ErrorCode
from albus.transport.utils import error_response, get_runtime

logger = logging.getLogger(__name__)


def _get_store(request: web.Request) -> Any | None:
    """Get the studio store from runtime, if available."""
    runtime = get_runtime(request)

    # Try to get store from pathway_service
    store = getattr(runtime.pathway_service, "_store", None)
    if store:
        return store

    # Try to get from VM context
    vm = getattr(runtime, "pathway_vm", None)
    if vm and vm.ctx:
        domain = getattr(vm.ctx.services, "domain", None)
        if domain:
            store = getattr(domain, "_store", None)
            if store:
                return store

    return None


async def handle_list_runs(request: web.Request) -> web.Response:
    """GET /api/v1/runs - List recent runs.

    Query params:
        workspace_id: Filter by workspace
        doc_id: Filter by document (pathway)
        limit: Max results (default: 50)
        status: Filter by status (running, completed, failed)
    """
    workspace_id = request.query.get("workspace_id")
    doc_id = request.query.get("doc_id")
    limit = int(request.query.get("limit", "50"))
    status_filter = request.query.get("status")

    store = _get_store(request)
    if not store:
        return web.json_response(
            {
                "runs": [],
                "count": 0,
                "message": "Run storage not available",
            }
        )

    try:
        list_fn = getattr(store, "list_run_summaries", None)
        if not callable(list_fn):
            return web.json_response({"runs": [], "count": 0})

        summaries = list_fn(
            workspace_id=workspace_id,
            doc_id=doc_id,
            limit=limit,
        )

        # Filter by status if requested
        if status_filter:
            summaries = [
                s
                for s in summaries
                if getattr(s, "status", None) and s.status.value == status_filter
            ]

        runs = []
        for s in summaries:
            duration_ms = None
            if s.finished_at_ms and s.started_at_ms:
                duration_ms = s.finished_at_ms - s.started_at_ms

            runs.append(
                {
                    "run_id": s.run_id,
                    "status": (
                        s.status.value if hasattr(s.status, "value") else str(s.status)
                    ),
                    "started_at_ms": s.started_at_ms,
                    "finished_at_ms": s.finished_at_ms,
                    "duration_ms": duration_ms,
                    "error": s.error,
                    "workspace_id": s.workspace_id,
                    "doc_id": s.doc_id,
                }
            )

        return web.json_response(
            {
                "runs": runs,
                "count": len(runs),
            }
        )

    except Exception as e:
        logger.error("Failed to list runs: %s", e)
        return web.json_response(
            {
                "runs": [],
                "count": 0,
                "error": str(e),
            }
        )


async def handle_get_run(request: web.Request) -> web.Response:
    """GET /api/v1/runs/{run_id} - Get run summary with inputs/outputs."""
    run_id = str(request.match_info.get("run_id") or "").strip()
    if not run_id:
        return error_response(
            request, "run_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    store = _get_store(request)
    if not store:
        return error_response(
            request,
            "Run storage not available",
            ErrorCode.SERVICE_UNAVAILABLE,
            status=503,
        )

    try:
        # Get summary
        get_fn = getattr(store, "get_run_summary", None)
        if not callable(get_fn):
            return error_response(
                request,
                "Run storage not available",
                ErrorCode.SERVICE_UNAVAILABLE,
                status=503,
            )

        summary = get_fn(run_id=run_id)
        if not summary:
            return error_response(
                request, f"Run not found: {run_id}", ErrorCode.NOT_FOUND, status=404
            )

        # Get events to extract inputs/outputs and pathway info
        list_events_fn = getattr(store, "list_run_events", None)
        events = []
        if callable(list_events_fn):
            events = list_events_fn(run_id=run_id, limit=1000)

        inputs = None
        outputs = None
        pathway_id = None
        pathway_name = None
        node_count = 0

        for ev in events:
            if ev.type == "execution_started":
                inputs = ev.payload.get("inputs")
                pathway_data = ev.payload.get("pathway")
                if pathway_data:
                    pathway_id = pathway_data.get("pathway_id")
                    node_count = pathway_data.get("node_count", 0)

            # Try to get outputs from execution_completed
            if ev.type == "execution_completed":
                outputs = ev.payload.get("outputs")

        duration_ms = None
        if summary.finished_at_ms and summary.started_at_ms:
            duration_ms = summary.finished_at_ms - summary.started_at_ms

        return web.json_response(
            {
                "run_id": summary.run_id,
                "pathway_id": pathway_id,
                "pathway_name": pathway_name,
                "status": (
                    summary.status.value
                    if hasattr(summary.status, "value")
                    else str(summary.status)
                ),
                "started_at_ms": summary.started_at_ms,
                "finished_at_ms": summary.finished_at_ms,
                "duration_ms": duration_ms,
                "inputs": inputs,
                "outputs": outputs,
                "error": summary.error,
                "workspace_id": summary.workspace_id,
                "doc_id": summary.doc_id,
                "node_count": node_count,
                "event_count": len(events),
            }
        )

    except Exception as e:
        logger.error("Failed to get run: %s", e)
        return error_response(
            request, str(e), ErrorCode.SERVICE_UNAVAILABLE, status=500
        )


async def handle_get_run_spans(request: web.Request) -> web.Response:
    """GET /api/v1/runs/{run_id}/spans - Get hierarchical span tree.

    Returns spans as a flat list with parent_span_id for tree reconstruction.
    Studio can build the tree client-side for flexible visualization.
    """
    run_id = str(request.match_info.get("run_id") or "").strip()
    if not run_id:
        return error_response(
            request, "run_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    store = _get_store(request)
    if not store:
        return error_response(
            request,
            "Run storage not available",
            ErrorCode.SERVICE_UNAVAILABLE,
            status=503,
        )

    try:
        list_events_fn = getattr(store, "list_run_events", None)
        if not callable(list_events_fn):
            return error_response(
                request,
                "Run storage not available",
                ErrorCode.SERVICE_UNAVAILABLE,
                status=503,
            )

        events = list_events_fn(run_id=run_id, limit=5000)

        # Extract completed spans from events
        # Spans are emitted as events with type="span" and phase="end"
        spans = []
        for ev in events:
            if ev.type == "span" and ev.payload.get("phase") == "end":
                span_data = ev.payload.get("span", {})

                # Calculate duration
                start_ms = span_data.get("start_ms")
                end_ms = span_data.get("end_ms")
                duration_ms = None
                if start_ms is not None and end_ms is not None:
                    duration_ms = end_ms - start_ms

                spans.append(
                    {
                        "span_id": span_data.get("span_id"),
                        "parent_span_id": span_data.get("parent_span_id"),
                        "kind": span_data.get("kind"),
                        "name": span_data.get("name"),
                        "start_ms": start_ms,
                        "end_ms": end_ms,
                        "duration_ms": duration_ms,
                        "status": span_data.get("status"),
                        "error": span_data.get("error"),
                        "attributes": span_data.get("attributes", {}),
                        "inputs": span_data.get("inputs"),
                        "outputs": span_data.get("outputs"),
                    }
                )

        # Sort by start time
        spans.sort(key=lambda s: s.get("start_ms") or 0)

        return web.json_response(
            {
                "run_id": run_id,
                "spans": spans,
                "count": len(spans),
            }
        )

    except Exception as e:
        logger.error("Failed to get run spans: %s", e)
        return error_response(
            request, str(e), ErrorCode.SERVICE_UNAVAILABLE, status=500
        )


async def handle_get_run_events(request: web.Request) -> web.Response:
    """GET /api/v1/runs/{run_id}/events - Get event stream.

    Query params:
        after_seq: Return events after this sequence number (for polling)
        limit: Max events to return (default: 500)
        type: Filter by event type
    """
    run_id = str(request.match_info.get("run_id") or "").strip()
    if not run_id:
        return error_response(
            request, "run_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    after_seq = request.query.get("after_seq")
    limit = int(request.query.get("limit", "500"))
    type_filter = request.query.get("type")

    store = _get_store(request)
    if not store:
        return error_response(
            request,
            "Run storage not available",
            ErrorCode.SERVICE_UNAVAILABLE,
            status=503,
        )

    try:
        list_events_fn = getattr(store, "list_run_events", None)
        if not callable(list_events_fn):
            return error_response(
                request,
                "Run storage not available",
                ErrorCode.SERVICE_UNAVAILABLE,
                status=503,
            )

        # Fetch one extra to detect has_more
        events = list_events_fn(
            run_id=run_id,
            after_seq=int(after_seq) if after_seq else None,
            limit=limit + 1,
        )

        has_more = len(events) > limit
        events = events[:limit]

        # Filter by type if requested
        if type_filter:
            events = [e for e in events if e.type == type_filter]

        result = []
        for ev in events:
            result.append(
                {
                    "seq": ev.seq,
                    "ts_ms": ev.ts_ms,
                    "type": ev.type,
                    "node_id": ev.node_id,
                    "payload": ev.payload,
                }
            )

        return web.json_response(
            {
                "run_id": run_id,
                "events": result,
                "count": len(result),
                "has_more": has_more,
            }
        )

    except Exception as e:
        logger.error("Failed to get run events: %s", e)
        return error_response(
            request, str(e), ErrorCode.SERVICE_UNAVAILABLE, status=500
        )


async def handle_get_run_timeline(request: web.Request) -> web.Response:
    """GET /api/v1/runs/{run_id}/timeline - Get timeline for visualization.

    Returns a flat list of segments with depth information for rendering
    a Gantt-chart style timeline in Studio.
    """
    run_id = str(request.match_info.get("run_id") or "").strip()
    if not run_id:
        return error_response(
            request, "run_id is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    store = _get_store(request)
    if not store:
        return error_response(
            request,
            "Run storage not available",
            ErrorCode.SERVICE_UNAVAILABLE,
            status=503,
        )

    try:
        list_events_fn = getattr(store, "list_run_events", None)
        if not callable(list_events_fn):
            return error_response(
                request,
                "Run storage not available",
                ErrorCode.SERVICE_UNAVAILABLE,
                status=503,
            )

        events = list_events_fn(run_id=run_id, limit=5000)

        # Build span registry from start/end events
        spans_by_id: dict[str, dict[str, Any]] = {}
        run_start_ms: int | None = None

        for ev in events:
            if ev.type == "span":
                span_data = ev.payload.get("span", {})
                span_id = span_data.get("span_id")
                phase = ev.payload.get("phase")

                if not span_id:
                    continue

                if phase == "start":
                    spans_by_id[span_id] = {
                        "span_id": span_id,
                        "parent_span_id": span_data.get("parent_span_id"),
                        "kind": span_data.get("kind"),
                        "name": span_data.get("name"),
                        "start_ms": span_data.get("start_ms"),
                        "end_ms": None,
                        "status": "running",
                    }

                    # Track earliest start for normalization
                    start_ms = span_data.get("start_ms")
                    if start_ms is not None:
                        if run_start_ms is None or start_ms < run_start_ms:
                            run_start_ms = start_ms

                elif phase == "end" and span_id in spans_by_id:
                    spans_by_id[span_id]["end_ms"] = span_data.get("end_ms")
                    spans_by_id[span_id]["status"] = span_data.get("status")

        run_start_ms = run_start_ms or 0

        # Calculate depth based on parent relationships
        depth_cache: dict[str, int] = {}

        def get_depth(span_id: str, visited: set[str] | None = None) -> int:
            if span_id in depth_cache:
                return depth_cache[span_id]

            if visited is None:
                visited = set()

            if span_id in visited:
                return 0  # Cycle protection

            visited.add(span_id)

            span = spans_by_id.get(span_id)
            if not span or not span.get("parent_span_id"):
                depth_cache[span_id] = 0
                return 0

            parent_depth = get_depth(span["parent_span_id"], visited)
            depth_cache[span_id] = parent_depth + 1
            return parent_depth + 1

        # Build timeline segments
        segments = []
        for span_id, span in spans_by_id.items():
            start_ms = span.get("start_ms")
            end_ms = span.get("end_ms")

            if start_ms is None:
                continue

            # Normalize to run start
            relative_start = start_ms - run_start_ms
            relative_end = (
                (end_ms - run_start_ms) if end_ms is not None else relative_start
            )

            segments.append(
                {
                    "span_id": span_id,
                    "name": span["name"],
                    "kind": span["kind"],
                    "start_ms": relative_start,
                    "end_ms": relative_end,
                    "duration_ms": relative_end - relative_start,
                    "depth": get_depth(span_id),
                    "status": span["status"],
                }
            )

        # Sort by start time, then by depth
        segments.sort(key=lambda s: (s["start_ms"], s["depth"]))

        # Calculate total duration
        total_duration = max((s["end_ms"] for s in segments), default=0)

        return web.json_response(
            {
                "run_id": run_id,
                "total_duration_ms": total_duration,
                "segments": segments,
                "count": len(segments),
            }
        )

    except Exception as e:
        logger.error("Failed to get run timeline: %s", e)
        return error_response(
            request, str(e), ErrorCode.SERVICE_UNAVAILABLE, status=500
        )


__all__ = [
    "handle_list_runs",
    "handle_get_run",
    "handle_get_run_spans",
    "handle_get_run_events",
    "handle_get_run_timeline",
]
