"""Bridge PathwayVM execution events into Albus observability events.

Pathway Engine emits `PathwayEvent` during execution via `PathwayVM.add_listener`.
Albus exposes a higher-level typed event stream (turn/pathway/node/tool/llm).

This module is the single, explicit adapter between those layers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from albus.infrastructure.observability.emitter import EventEmitter
from albus.infrastructure.observability.events import (
    NodeCompletedEvent,
    NodeFailedEvent,
    NodeStartedEvent,
    NodeInfo,
    PathwayCreatedEvent,
    PathwayCompletedEvent,
    PathwayStartedEvent,
    ToolCalledEvent,
    ToolCompletedEvent,
    ToolFailedEvent,
    LLMRequestEvent,
    LLMResponseEvent,
)

logger = logging.getLogger(__name__)


@dataclass
class _ExecutionIndex:
    pathway_id: str | None = None
    thread_id: str | None = None
    turn_id: str | None = None
    started_at: datetime | None = None


class PathwayVMObservabilityBridge:
    """Listener that converts PathwayVM events into Albus events."""

    def __init__(self, *, events: EventEmitter):
        self._events = events
        self._by_execution_id: dict[str, _ExecutionIndex] = {}

    def __call__(self, ev: Any) -> None:
        """Handle a PathwayVM PathwayEvent (best-effort, never raises)."""
        try:
            event_type = getattr(ev, "event_type", None)
            data = getattr(ev, "data", {}) or {}
            ts = getattr(ev, "timestamp", None)
            node_id = getattr(ev, "node_id", None)
            pathway_id = getattr(ev, "pathway_id", None)
            error = getattr(ev, "error", None)

            execution_id = data.get("execution_id")
            if not isinstance(execution_id, str) or not execution_id:
                # PathwayVM should always provide this, but don't explode if not.
                return

            idx = self._by_execution_id.get(execution_id)
            if idx is None:
                idx = _ExecutionIndex()
                self._by_execution_id[execution_id] = idx

            # Keep a stable started_at timestamp for duration computations.
            if (
                isinstance(ts, datetime)
                and idx.started_at is None
                and event_type == "execution_started"
            ):
                idx.started_at = ts

            # Capture IDs on execution start (inputs are only present there).
            if event_type == "execution_started":
                idx.pathway_id = pathway_id or idx.pathway_id
                try:
                    inputs = data.get("inputs", {}) or {}
                    if isinstance(inputs, dict):
                        idx.thread_id = (
                            str(inputs.get("thread_id") or idx.thread_id or "") or None
                        )
                        idx.turn_id = (
                            str(inputs.get("turn_id") or idx.turn_id or "") or None
                        )
                except Exception:
                    pass

                # Optional: pathway graph payload (nodes + connections) for Studio.
                nodes: list[NodeInfo] = []
                connections: list[tuple[str, str]] = []
                try:
                    g = data.get("pathway")
                    if isinstance(g, dict):
                        for n in g.get("nodes", []) or []:
                            if isinstance(n, dict) and n.get("id"):
                                nodes.append(
                                    NodeInfo(
                                        id=str(n.get("id")),
                                        type=str(n.get("type") or ""),
                                        prompt=(
                                            str(n.get("prompt"))
                                            if n.get("prompt") is not None
                                            else None
                                        ),
                                    )
                                )
                        for c in g.get("connections", []) or []:
                            if isinstance(c, (list, tuple)) and len(c) >= 2:
                                connections.append((str(c[0]), str(c[1])))
                except Exception:
                    nodes = []
                    connections = []

                if nodes or connections:
                    try:
                        self._events.emit(
                            PathwayCreatedEvent(
                                thread_id=idx.thread_id,
                                turn_id=idx.turn_id,
                                execution_id=execution_id,
                                pathway_id=idx.pathway_id or str(pathway_id or ""),
                                node_count=len(nodes),
                                nodes=nodes,
                                connections=connections,
                            )
                        )
                    except Exception:
                        pass

                self._events.emit(
                    PathwayStartedEvent(
                        thread_id=idx.thread_id,
                        turn_id=idx.turn_id,
                        execution_id=execution_id,
                        pathway_id=idx.pathway_id or str(pathway_id or ""),
                        node_count=len(nodes) if nodes else 0,
                        nodes=nodes,
                    )
                )
                return

            # Prefer captured pathway_id for node events (PathwayVM doesn't attach it to node_*).
            effective_pathway_id = idx.pathway_id or pathway_id or ""

            # Tool call lifecycle (emitted by PathwayVM tool wrappers).
            if event_type in {"tool_called", "tool_completed", "tool_failed"}:
                tool_name = str(data.get("tool_name") or "")
                call_id = str(data.get("call_id") or "") or None
                args = data.get("args") if isinstance(data.get("args"), dict) else {}
                duration_ms = data.get("duration_ms")
                ok = data.get("ok")
                err = str(error or data.get("error") or "") or None
                result = data.get("result")

                # Always emit tool events.
                if event_type == "tool_called":
                    self._events.emit(
                        ToolCalledEvent(
                            thread_id=idx.thread_id,
                            turn_id=idx.turn_id,
                            execution_id=execution_id,
                            pathway_id=effective_pathway_id or None,
                            node_id=str(node_id or "") or None,
                            call_id=call_id,
                            tool_name=tool_name,
                            tool_args=args,
                        )
                    )
                elif event_type == "tool_completed":
                    self._events.emit(
                        ToolCompletedEvent(
                            thread_id=idx.thread_id,
                            turn_id=idx.turn_id,
                            execution_id=execution_id,
                            pathway_id=effective_pathway_id or None,
                            node_id=str(node_id or "") or None,
                            call_id=call_id,
                            tool_name=tool_name,
                            tool_args=args,
                            result=result,
                            duration_ms=duration_ms,
                            success=True if ok is None else bool(ok),
                        )
                    )
                else:
                    self._events.emit(
                        ToolFailedEvent(
                            thread_id=idx.thread_id,
                            turn_id=idx.turn_id,
                            execution_id=execution_id,
                            pathway_id=effective_pathway_id or None,
                            node_id=str(node_id or "") or None,
                            call_id=call_id,
                            tool_name=tool_name,
                            tool_args=args,
                            result=result,
                            duration_ms=duration_ms,
                            error=err,
                        )
                    )

                # Additionally, treat llm.* tools as LLM request/response events.
                if tool_name.startswith("llm."):
                    if event_type == "tool_called":
                        prompt = ""
                        model = ""
                        try:
                            prompt = str(args.get("prompt") or "")
                            model = str(args.get("model") or "")
                        except Exception:
                            pass
                        self._events.emit(
                            LLMRequestEvent(
                                thread_id=idx.thread_id,
                                turn_id=idx.turn_id,
                                execution_id=execution_id,
                                pathway_id=effective_pathway_id or None,
                                node_id=str(node_id or "") or None,
                                call_id=call_id,
                                model=model,
                                prompt=prompt,
                            )
                        )
                    if event_type in {"tool_completed", "tool_failed"}:
                        model = ""
                        prompt = ""
                        response = ""
                        tokens_in = None
                        tokens_out = None
                        try:
                            model = str(
                                (result or {}).get("model") or args.get("model") or ""
                            )
                            prompt = str(args.get("prompt") or "")
                            response = str(
                                (result or {}).get("content")
                                or (result or {}).get("response")
                                or ""
                            )
                            usage = (
                                (result or {}).get("usage")
                                if isinstance(result, dict)
                                else None
                            )
                            if isinstance(usage, dict):
                                tokens_in = usage.get("input_tokens") or usage.get(
                                    "prompt_tokens"
                                )
                                tokens_out = usage.get("output_tokens") or usage.get(
                                    "completion_tokens"
                                )
                        except Exception:
                            pass
                        self._events.emit(
                            LLMResponseEvent(
                                thread_id=idx.thread_id,
                                turn_id=idx.turn_id,
                                execution_id=execution_id,
                                pathway_id=effective_pathway_id or None,
                                node_id=str(node_id or "") or None,
                                call_id=call_id,
                                model=model,
                                prompt=prompt,
                                response=response,
                                tokens_in=tokens_in,
                                tokens_out=tokens_out,
                                duration_ms=duration_ms,
                            )
                        )
                return

            if event_type == "node_started":
                self._events.emit(
                    NodeStartedEvent(
                        thread_id=idx.thread_id,
                        turn_id=idx.turn_id,
                        execution_id=execution_id,
                        node_id=str(node_id or ""),
                        node_type="",
                        pathway_id=effective_pathway_id,
                        inputs={},
                    )
                )
                return

            if event_type == "node_completed":
                self._events.emit(
                    NodeCompletedEvent(
                        thread_id=idx.thread_id,
                        turn_id=idx.turn_id,
                        execution_id=execution_id,
                        node_id=str(node_id or ""),
                        node_type="",
                        pathway_id=effective_pathway_id,
                        outputs={},
                        duration_ms=data.get("duration_ms"),
                    )
                )
                return

            if event_type == "node_failed":
                self._events.emit(
                    NodeFailedEvent(
                        thread_id=idx.thread_id,
                        turn_id=idx.turn_id,
                        execution_id=execution_id,
                        node_id=str(node_id or ""),
                        node_type="",
                        pathway_id=effective_pathway_id,
                        error=str(error or ""),
                        duration_ms=data.get("duration_ms"),
                    )
                )
                return

            if event_type == "execution_completed":
                duration_ms = None
                if isinstance(ts, datetime) and isinstance(idx.started_at, datetime):
                    duration_ms = (ts - idx.started_at).total_seconds() * 1000

                self._events.emit(
                    PathwayCompletedEvent(
                        thread_id=idx.thread_id,
                        turn_id=idx.turn_id,
                        execution_id=execution_id,
                        pathway_id=idx.pathway_id or str(pathway_id or ""),
                        duration_ms=duration_ms,
                        success=str(data.get("status", "")) == "completed",
                        outputs={},  # PathwayVM does not include outputs in events.
                    )
                )
                # Keep index around briefly; safe cleanup on completion.
                self._by_execution_id.pop(execution_id, None)
                return

        except Exception as e:
            logger.debug("PathwayVMObservabilityBridge dropped event: %s", e)


def attach_pathway_vm_observability(*, vm: Any, events: EventEmitter) -> None:
    """Attach a single bridge listener to a PathwayVM-like object."""
    add_listener = getattr(vm, "add_listener", None)
    if not callable(add_listener):
        raise TypeError("vm does not support add_listener(listener)")
    add_listener(PathwayVMObservabilityBridge(events=events))
