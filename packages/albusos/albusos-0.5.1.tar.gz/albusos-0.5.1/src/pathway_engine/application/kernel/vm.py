"""PathwayVM - The graph execution engine.

This is the **only graph executor** in `pathway_engine`: it defines the semantics of
executing a single Pathway (ordering, gating, node compute(), metrics, and events).

Higher-level orchestration (running many pathways concurrently, batching, queuing,
agent/background lifecycles) can be built *on top* of the VM, but should not change
graph semantics.
"""

from __future__ import annotations

import asyncio
import logging
import time
from uuid import uuid4
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any

from pathway_engine.domain.context import Context
from pathway_engine.domain.pathway import Connection, Loop, NodeStatus, Pathway, PSEUDO_NODES, Signal
from pathway_engine.domain.nodes.execution import (
    PathwayEvent,
    PathwayMetrics,
    PathwayRecord,
    PathwayStatus,
)

logger = logging.getLogger(__name__)


class PathwayPriority(Enum):
    """Execution priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class PathwayVM:
    """The graph execution engine.

    Execute graphs by calling node.compute() directly.
    No resolvers, no type lookups - nodes know how to execute themselves.

    Usage:
        ctx = create_context(...)
        vm = PathwayVM(ctx)
        record = await vm.execute(graph, {"input": "hello"})
    """

    def __init__(
        self,
        ctx: Context,
        *,
        max_parallel: int = 10,
        default_timeout: float = 300.0,
    ):
        """Create a PathwayVM.

        Args:
            ctx: Execution context with tools and services
            max_parallel: Maximum concurrent node executions
            default_timeout: Default execution timeout in seconds
        """
        self.ctx = ctx
        try:
            if self.ctx.services.pathway_executor is None:
                self.ctx.services.pathway_executor = self
        except Exception:
            pass
        self.max_parallel = max_parallel
        self.default_timeout = default_timeout
        self._execution_semaphore = asyncio.Semaphore(max_parallel)
        self._node_semaphore = asyncio.Semaphore(max_parallel)
        self._executions: dict[str, PathwayRecord] = {}
        self._listeners: list = []
        # Best-effort: wrap tool handlers so the VM can emit tool-call events.
        # This stays entirely within `pathway_engine` by emitting PathwayEvent,
        # and higher layers can bridge as needed.
        try:
            self._wrap_tools_for_observability()
        except Exception:
            logger.debug(
                "Failed to wrap tools for observability (non-fatal)", exc_info=True
            )

    def _wrap_tools_for_observability(self) -> None:
        """Wrap ctx.tools handlers to emit tool call lifecycle PathwayEvents.

        Important: we preserve `.stream` on handlers so EventSourceNode keeps working.
        """
        if self.ctx.extras.get("_tools_wrapped_for_observability"):
            return

        from pathway_engine.domain.nodes.execution import PathwayEvent

        tools = dict(self.ctx.tools or {})

        def _emit(
            event_type: str,
            *,
            tool_name: str,
            call_id: str,
            ok: bool | None = None,
            duration_ms: float | None = None,
            error: str | None = None,
            args: dict[str, Any] | None = None,
            result: Any | None = None,
        ) -> None:
            try:
                self._emit_event(
                    PathwayEvent(
                        event_type=event_type,
                        pathway_id=getattr(self.ctx, "pathway_id", None) or None,
                        node_id=str(self.ctx.extras.get("_current_node_id") or "")
                        or None,
                        data={
                            "execution_id": getattr(self.ctx, "execution_id", "") or "",
                            "tool_name": tool_name,
                            "call_id": call_id,
                            "ok": ok,
                            "duration_ms": duration_ms,
                            "args": args or {},
                            "result": result,
                        },
                        error=error,
                    )
                )
            except Exception:
                pass

        for name, handler in tools.items():
            if not callable(handler):
                continue
            if getattr(handler, "_albus_wrapped", False):
                continue

            async def _wrapped(
                call_args: dict[str, Any],
                ctx: Context,
                *,
                _name: str = name,
                _handler=handler,
            ):
                call_id = f"tc_{uuid4().hex[:10]}"
                _emit(
                    "tool_called",
                    tool_name=_name,
                    call_id=call_id,
                    args=dict(call_args or {}),
                )
                started_at = time.time()
                try:
                    out = await _handler(call_args, ctx)
                    dur = (time.time() - started_at) * 1000
                    _emit(
                        "tool_completed",
                        tool_name=_name,
                        call_id=call_id,
                        ok=True,
                        duration_ms=dur,
                        result=out,
                    )
                    return out
                except Exception as e:
                    dur = (time.time() - started_at) * 1000
                    _emit(
                        "tool_failed",
                        tool_name=_name,
                        call_id=call_id,
                        ok=False,
                        duration_ms=dur,
                        error=str(e),
                    )
                    raise

            # Preserve streaming attribute if present.
            if hasattr(handler, "stream"):
                setattr(_wrapped, "stream", getattr(handler, "stream"))
            setattr(_wrapped, "_albus_wrapped", True)
            tools[name] = _wrapped

        self.ctx.tools = tools
        self.ctx.extras["_tools_wrapped_for_observability"] = True

    def add_listener(self, listener) -> None:
        """Add an event listener."""
        self._listeners.append(listener)

    def _emit_event(self, event: PathwayEvent) -> None:
        """Emit an event to all listeners."""
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

    async def execute(
        self,
        pathway: Pathway,
        inputs: dict[str, Any] | None = None,
        *,
        execution_id: str | None = None,
        timeout: float | None = None,
    ) -> PathwayRecord:
        """Execute a pathway.

        Args:
            pathway: The pathway to execute
            inputs: Input data for the pathway
            execution_id: Optional execution ID
            timeout: Execution timeout in seconds

        Returns:
            PathwayRecord with outputs and metrics
        """
        execution_id = execution_id or f"exec_{int(time.time() * 1000)}"
        timeout = timeout or self.default_timeout
        inputs = inputs or {}

        # Update context
        self.ctx.pathway_id = pathway.id
        self.ctx.execution_id = execution_id

        async with self._execution_semaphore:
            try:
                result = await asyncio.wait_for(
                    self._run_pathway(pathway, inputs, execution_id),
                    timeout=timeout,
                )
                self._executions[execution_id] = result
                return result

            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Execution {execution_id} timed out after {timeout}s"
                )

    async def stream_execute(
        self,
        pathway: Pathway,
        inputs: dict[str, Any] | None = None,
        *,
        max_events: int | None = None,
    ):
        """Execute a streaming pathway (EventSourceNode/IntrospectionNode) and yield per-event tick results.

        This is **true streaming execution**:
        - Each streaming node yields events over time
        - For each event, the VM executes the downstream reachable subgraph

        Yields dicts like:
            {
              "type": "tick",
              "source_node_id": "...",
              "event": {...},
              "outputs": {node_id: node_output, ...},
            }
        """
        from pathway_engine.domain.nodes.streaming import (
            EventSourceNode,
            IntrospectionNode,
        )

        inputs = inputs or {}

        # Establish an execution_id for observability parity with execute().
        execution_id = f"exec_{int(time.time() * 1000)}"
        self.ctx.pathway_id = pathway.id
        self.ctx.execution_id = execution_id
        self._emit_event(
            PathwayEvent(
                event_type="execution_started",
                pathway_id=pathway.id,
                data={"execution_id": execution_id, "inputs": inputs, "mode": "stream"},
            )
        )

        # Identify streaming source nodes (outer + inner).
        streaming_nodes: list[tuple[str, Any]] = [
            (node_id, node)
            for node_id, node in pathway.nodes.items()
            if isinstance(node, (EventSourceNode, IntrospectionNode))
        ]
        if not streaming_nodes:
            # No streaming nodes; just run once and yield a single completion.
            record = await self.execute(pathway, inputs)
            yield {
                "type": "complete",
                "outputs": record.outputs,
                "success": record.success,
                "error": record.error,
            }
            return

        # Build adjacency for reachability.
        outgoing: dict[str, set[str]] = {}
        for c in pathway.connections:
            outgoing.setdefault(c.from_node, set()).add(c.to_node)

        def reachable_from(start: str) -> set[str]:
            seen: set[str] = set()
            stack = [start]
            while stack:
                cur = stack.pop()
                for nxt in outgoing.get(cur, set()):
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
            return seen

        topo_order = self._topological_sort(pathway)
        reach_map: dict[str, set[str]] = {
            nid: reachable_from(nid) for nid, _ in streaming_nodes
        }

        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        tasks: list[asyncio.Task[None]] = []

        async def _pump(node_id: str, node: Any) -> None:
            try:
                async for item in node.stream(inputs, self.ctx):
                    # Normalize to an event payload for downstream consumers.
                    ev = item.get("event") if isinstance(item, dict) else item
                    await queue.put(
                        {"source_node_id": node_id, "event": ev, "raw": item}
                    )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                await queue.put({"source_node_id": node_id, "error": str(e)})

        for node_id, node in streaming_nodes:
            tasks.append(asyncio.create_task(_pump(node_id, node)))

        produced = 0
        try:
            while True:
                if max_events is not None and produced >= max_events:
                    return

                item = await queue.get()
                source_node_id = item.get("source_node_id")
                if item.get("error"):
                    yield {
                        "type": "stream_error",
                        "source_node_id": source_node_id,
                        "error": item.get("error"),
                    }
                    produced += 1
                    continue

                event_payload = item.get("event")

                # Emit a synthetic node event for the streaming source (it doesn't run via compute()).
                try:
                    self._emit_event(
                        PathwayEvent(
                            event_type="node_started",
                            node_id=str(source_node_id),
                            pathway_id=pathway.id,
                            data={
                                "execution_id": execution_id,
                                "tick_index": produced,
                                "source_node_id": source_node_id,
                            },
                        )
                    )
                    self._emit_event(
                        PathwayEvent(
                            event_type="node_completed",
                            node_id=str(source_node_id),
                            pathway_id=pathway.id,
                            data={
                                "execution_id": execution_id,
                                "success": True,
                                "duration_ms": 0.0,
                                "tick_index": produced,
                                "source_node_id": source_node_id,
                            },
                        )
                    )
                except Exception:
                    # Observability must never break streaming.
                    pass

                # Seed results with the source node output so normal connections work.
                results: dict[str, dict[str, Any]] = {
                    str(source_node_id): {
                        "output": event_payload,
                        "event": event_payload,
                        "source_node_id": source_node_id,
                    }
                }

                # Execute reachable downstream nodes in topo order.
                reachable = reach_map.get(str(source_node_id), set())
                for node_id in topo_order:
                    if node_id == source_node_id:
                        continue
                    if node_id not in reachable:
                        continue

                    node = pathway.nodes.get(node_id)
                    if node is None:
                        continue

                    if not self._should_execute(pathway, node_id, results):
                        continue

                    node_inputs = self._gather_inputs(pathway, node_id, results, inputs)
                    try:
                        self._emit_event(
                            PathwayEvent(
                                event_type="node_started",
                                node_id=node_id,
                                pathway_id=pathway.id,
                                data={
                                    "execution_id": execution_id,
                                    "tick_index": produced,
                                    "source_node_id": source_node_id,
                                },
                            )
                        )
                        started_at = time.time()
                        # Allow tool wrappers to attribute tool calls to the current node.
                        try:
                            self.ctx.extras["_current_node_id"] = node_id
                        except Exception:
                            pass
                        out = await node.compute(node_inputs, self.ctx)
                        duration_ms = (time.time() - started_at) * 1000
                        results[node_id] = out
                        self._emit_event(
                            PathwayEvent(
                                event_type="node_completed",
                                node_id=node_id,
                                pathway_id=pathway.id,
                                data={
                                    "execution_id": execution_id,
                                    "success": True,
                                    "duration_ms": duration_ms,
                                    "tick_index": produced,
                                    "source_node_id": source_node_id,
                                },
                            )
                        )
                    except Exception as e:
                        results[node_id] = {"error": str(e)}
                        try:
                            self._emit_event(
                                PathwayEvent(
                                    event_type="node_failed",
                                    node_id=node_id,
                                    pathway_id=pathway.id,
                                    error=str(e),
                                    data={
                                        "execution_id": execution_id,
                                        "tick_index": produced,
                                        "source_node_id": source_node_id,
                                    },
                                )
                            )
                        except Exception:
                            pass
                        # For streaming, yield the tick with error and stop this tick execution.
                        break
                    finally:
                        try:
                            if self.ctx.extras.get("_current_node_id") == node_id:
                                self.ctx.extras.pop("_current_node_id", None)
                        except Exception:
                            pass

                yield {
                    "type": "tick",
                    "source_node_id": source_node_id,
                    "event": event_payload,
                    "outputs": results,
                }
                produced += 1
        except asyncio.CancelledError:
            # Best-effort signal cancellation, then re-raise.
            try:
                self._emit_event(
                    PathwayEvent(
                        event_type="execution_completed",
                        pathway_id=pathway.id,
                        data={
                            "execution_id": execution_id,
                            "status": "cancelled",
                            "produced": produced,
                        },
                    )
                )
            except Exception:
                pass
            raise
        finally:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            # Best-effort completion event (mirrors execute()).
            try:
                self._emit_event(
                    PathwayEvent(
                        event_type="execution_completed",
                        pathway_id=pathway.id,
                        data={
                            "execution_id": execution_id,
                            "status": "completed",
                            "produced": produced,
                        },
                    )
                )
            except Exception:
                pass

    async def _run_pathway(
        self,
        pathway: Pathway,
        inputs: dict[str, Any],
        execution_id: str,
    ) -> PathwayRecord:
        """Run a pathway - the core execution logic."""
        record = PathwayRecord(
            id=execution_id,
            pathway_id=pathway.id,
            inputs=inputs,
            status=PathwayStatus.RUNNING,
        )
        record.metrics.start_time = datetime.utcnow()

        # Include a compact pathway graph payload for dev ergonomics (Studio graph view).
        # This is intentionally minimal (ids + types + prompt preview + edges).
        try:
            nodes_payload = []
            for nid, node in (pathway.nodes or {}).items():
                ntype = getattr(node, "type", node.__class__.__name__)
                prompt = getattr(node, "prompt", None)
                if isinstance(prompt, str) and len(prompt) > 160:
                    prompt = prompt[:157] + "..."
                nodes_payload.append(
                    {"id": str(nid), "type": str(ntype), "prompt": prompt}
                )
            conns_payload = [
                (c.from_node, c.to_node) for c in (pathway.connections or [])
            ]
            graph_payload = {
                "pathway_id": pathway.id,
                "node_count": len(nodes_payload),
                "nodes": nodes_payload,
                "connections": conns_payload,
            }
        except Exception:
            graph_payload = None

        # Generate run-level span ID upfront for event correlation
        run_span_id = f"run:{execution_id}"

        self._emit_event(
            PathwayEvent(
                event_type="execution_started",
                pathway_id=pathway.id,
                data={
                    "execution_id": execution_id,
                    "span_id": run_span_id,
                    "parent_span_id": None,
                    "inputs": self._sanitize_for_logging(inputs),
                    "pathway": graph_payload,
                },
            )
        )

        try:
            topo_order = self._topological_sort(pathway)
            order_index = {nid: i for i, nid in enumerate(topo_order)}
            results: dict[str, dict[str, Any]] = {}

            # Dependency graph from explicit connections only.
            # Skip pseudo-nodes (input/output) which are not real executable nodes.
            deps: dict[str, set[str]] = {nid: set() for nid in pathway.nodes}
            dependents: dict[str, set[str]] = {nid: set() for nid in pathway.nodes}
            for conn in pathway.connections:
                # Skip pseudo-nodes
                if conn.from_node in PSEUDO_NODES or conn.to_node in PSEUDO_NODES:
                    continue
                if conn.from_node in deps and conn.to_node in deps:
                    deps[conn.to_node].add(conn.from_node)
                    dependents[conn.from_node].add(conn.to_node)

            completed: set[str] = set()
            # Tuple: (node_id, outputs, success, duration_ms, error_msg, error_type, inputs)
            in_flight: dict[
                str,
                asyncio.Task[
                    tuple[
                        str,
                        dict[str, Any],
                        bool,
                        float,
                        str | None,
                        str | None,
                        dict[str, Any],
                    ]
                ],
            ] = {}
            ready: list[str] = [nid for nid in topo_order if not deps.get(nid)]
            stop_on_error = bool(inputs.get("_stop_on_error"))
            lock = asyncio.Lock()

            async def _run_node(
                node_id: str,
            ) -> tuple[
                str, dict[str, Any], bool, float, str | None, str | None, dict[str, Any]
            ]:
                """Run a single node under the global node semaphore."""
                node = pathway.nodes.get(node_id)
                if node is None:
                    return (node_id, {}, True, 0.0, None, None, {})

                # Gather inputs from connections (deps are complete by scheduler invariant).
                async with lock:
                    node_inputs = self._gather_inputs(pathway, node_id, results, inputs)

                # Generate node-level span ID
                node_span_id = f"node:{execution_id}:{node_id}"
                node_type = getattr(node, "type", node.__class__.__name__)

                async with self._node_semaphore:
                    # Emit node started with span info and inputs for debugging
                    try:
                        self._emit_event(
                            PathwayEvent(
                                event_type="node_started",
                                node_id=node_id,
                                pathway_id=pathway.id,
                                data={
                                    "execution_id": execution_id,
                                    "span_id": node_span_id,
                                    "parent_span_id": run_span_id,
                                    "node_type": node_type,
                                    "inputs": self._sanitize_for_logging(node_inputs),
                                },
                            )
                        )
                    except Exception:
                        pass

                    started_at = time.time()
                    try:
                        # Allow tool wrappers to attribute tool calls to the current node.
                        try:
                            self.ctx.extras["_current_node_id"] = node_id
                        except Exception:
                            pass
                        out = await node.compute(node_inputs, self.ctx)
                        duration_ms = (time.time() - started_at) * 1000
                        return (
                            node_id,
                            out,
                            True,
                            duration_ms,
                            None,
                            None,
                            node_inputs,
                        )
                    except Exception as e:
                        duration_ms = (time.time() - started_at) * 1000
                        return (
                            node_id,
                            {"error": str(e), "error_type": type(e).__name__},
                            False,
                            duration_ms,
                            str(e),
                            type(e).__name__,
                            node_inputs,
                        )
                    finally:
                        try:
                            if self.ctx.extras.get("_current_node_id") == node_id:
                                self.ctx.extras.pop("_current_node_id", None)
                        except Exception:
                            pass

            def _mark_ready_if_unblocked(nid: str) -> None:
                if nid in completed or nid in in_flight:
                    return
                if deps.get(nid, set()).issubset(completed):
                    ready.append(nid)

            # Scheduler loop: execute independent nodes concurrently.
            while ready or in_flight:
                # Launch as many ready nodes as possible (deterministic by topo order).
                ready.sort(key=lambda nid: order_index.get(nid, 10**9))
                while ready and len(in_flight) < self.max_parallel:
                    node_id = ready.pop(0)

                    async with lock:
                        should = self._should_execute(pathway, node_id, results)
                    if not should:
                        # Mark skipped as "completed" for dependency unblocking, but do not
                        # inject a synthetic result (preserves prior behavior).
                        record.metrics.nodes_skipped += 1
                        completed.add(node_id)
                        for dep in dependents.get(node_id, set()):
                            _mark_ready_if_unblocked(dep)
                        continue

                    in_flight[node_id] = asyncio.create_task(_run_node(node_id))

                if not in_flight:
                    # No runnable work left (shouldn't happen unless nodes are missing).
                    break

                done, _pending = await asyncio.wait(
                    in_flight.values(), return_when=asyncio.FIRST_COMPLETED
                )
                for task in done:
                    (
                        node_id,
                        out,
                        ok,
                        duration_ms,
                        error_msg,
                        error_type,
                        node_inputs,
                    ) = task.result()
                    in_flight.pop(node_id, None)

                    # Update results + metrics.
                    async with lock:
                        if out:
                            results[node_id] = out
                        record.metrics.nodes_executed += 1
                        if ok:
                            record.metrics.nodes_succeeded += 1
                        else:
                            record.metrics.nodes_failed += 1

                    # Get node type for event
                    node = pathway.nodes.get(node_id)
                    node_type = (
                        getattr(node, "type", node.__class__.__name__)
                        if node
                        else "unknown"
                    )
                    node_span_id = f"node:{execution_id}:{node_id}"

                    if ok:
                        try:
                            self._emit_event(
                                PathwayEvent(
                                    event_type="node_completed",
                                    node_id=node_id,
                                    pathway_id=pathway.id,
                                    data={
                                        "execution_id": execution_id,
                                        "span_id": node_span_id,
                                        "parent_span_id": run_span_id,
                                        "success": True,
                                        "duration_ms": duration_ms,
                                        "node_type": node_type,
                                        "inputs": self._sanitize_for_logging(
                                            node_inputs
                                        ),
                                        "outputs": self._sanitize_for_logging(out),
                                    },
                                )
                            )
                        except Exception:
                            pass
                    else:
                        # Log error with context
                        logger.error(
                            "Node execution failed: node_id=%s, type=%s, error=%s, execution_id=%s, duration_ms=%.2f",
                            node_id,
                            error_type,
                            error_msg,
                            execution_id,
                            duration_ms,
                            exc_info=True,
                        )
                        try:
                            self._emit_event(
                                PathwayEvent(
                                    event_type="node_failed",
                                    node_id=node_id,
                                    pathway_id=pathway.id,
                                    error=error_msg or "",
                                    data={
                                        "execution_id": execution_id,
                                        "span_id": node_span_id,
                                        "parent_span_id": run_span_id,
                                        "duration_ms": duration_ms,
                                        "error_type": error_type,
                                        "node_type": node_type,
                                        "inputs": self._sanitize_for_logging(
                                            node_inputs
                                        ),
                                        "outputs": self._sanitize_for_logging(out),
                                    },
                                )
                            )
                        except Exception:
                            pass

                        if stop_on_error:
                            record.status = PathwayStatus.FAILED
                            record.error = f"{node_id} ({error_type}): {error_msg}"
                            for t in in_flight.values():
                                t.cancel()
                            await asyncio.gather(
                                *in_flight.values(), return_exceptions=True
                            )
                            in_flight.clear()
                            ready.clear()
                            break

                    completed.add(node_id)
                    for dep in dependents.get(node_id, set()):
                        _mark_ready_if_unblocked(dep)

                if record.status == PathwayStatus.FAILED and stop_on_error:
                    break

            # Execute loops (ReAct pattern)
            if record.status != PathwayStatus.FAILED:
                for loop in pathway.loops:
                    iteration = 0
                    while loop.should_continue(results, iteration):
                        self._emit_event(
                            PathwayEvent(
                                event_type="loop_iteration",
                                pathway_id=pathway.id,
                                data={
                                    "execution_id": execution_id,
                                    "iteration": iteration,
                                    "loop_nodes": loop.body_nodes,
                                },
                            )
                        )

                        # Execute body nodes in order
                        for node_id in loop.body_nodes:
                            node = pathway.nodes.get(node_id)
                            if node is None:
                                continue

                            # Gather inputs (include previous iteration results)
                            node_inputs = self._gather_inputs(
                                pathway, node_id, results, inputs
                            )
                            node_inputs["_iteration"] = iteration

                            # Execute node
                            started_at = time.time()
                            try:
                                async with self._node_semaphore:
                                    # Allow tool wrappers to attribute tool calls to the current node.
                                    try:
                                        self.ctx.extras["_current_node_id"] = node_id
                                    except Exception:
                                        pass
                                    result = await node.compute(node_inputs, self.ctx)
                                duration_ms = (time.time() - started_at) * 1000

                                results[node_id] = result
                                record.metrics.nodes_executed += 1
                                record.metrics.nodes_succeeded += 1

                                self._emit_event(
                                    PathwayEvent(
                                        event_type="node_completed",
                                        node_id=node_id,
                                        data={
                                            "execution_id": execution_id,
                                            "success": True,
                                            "duration_ms": duration_ms,
                                            "iteration": iteration,
                                        },
                                    )
                                )

                            except Exception as e:
                                duration_ms = (time.time() - started_at) * 1000
                                results[node_id] = {"error": str(e)}
                                record.metrics.nodes_executed += 1
                                record.metrics.nodes_failed += 1

                                self._emit_event(
                                    PathwayEvent(
                                        event_type="node_failed",
                                        node_id=node_id,
                                        error=str(e),
                                        data={
                                            "execution_id": execution_id,
                                            "duration_ms": duration_ms,
                                            "iteration": iteration,
                                        },
                                    )
                                )
                            finally:
                                try:
                                    if (
                                        self.ctx.extras.get("_current_node_id")
                                        == node_id
                                    ):
                                        self.ctx.extras.pop("_current_node_id", None)
                                except Exception:
                                    pass
                                break

                        iteration += 1

                    # Record final iteration count for this loop
                    results["_loop_iterations"] = iteration

            # Finalize
            record.outputs = results
            if record.status != PathwayStatus.FAILED:
                record.status = PathwayStatus.COMPLETED

        except Exception as e:
            record.status = PathwayStatus.FAILED
            record.error = str(e)
            self._emit_event(
                PathwayEvent(
                    event_type="execution_error",
                    pathway_id=pathway.id,
                    error=str(e),
                    data={"execution_id": execution_id},
                )
            )

        finally:
            record.metrics.end_time = datetime.utcnow()
            if record.metrics.start_time:
                duration = (
                    record.metrics.end_time - record.metrics.start_time
                ).total_seconds()
                record.metrics.duration_ms = duration * 1000

            self._emit_event(
                PathwayEvent(
                    event_type="execution_completed",
                    pathway_id=pathway.id,
                    data={
                        "execution_id": execution_id,
                        "span_id": run_span_id,
                        "status": record.status.value,
                        "success": record.status == PathwayStatus.COMPLETED,
                        "duration_ms": record.metrics.duration_ms,
                        "outputs": self._sanitize_for_logging(record.outputs),
                        "error": record.error,
                        "metrics": {
                            "nodes_executed": record.metrics.nodes_executed,
                            "nodes_succeeded": record.metrics.nodes_succeeded,
                            "nodes_failed": record.metrics.nodes_failed,
                            "nodes_skipped": record.metrics.nodes_skipped,
                        },
                    },
                )
            )

        return record

    def _topological_sort(self, pathway: Pathway) -> list[str]:
        """Get execution order via topological sort.
        
        Only considers connections between real nodes (not pseudo-nodes like 'input'/'output').
        """
        deps: dict[str, set[str]] = defaultdict(set)
        nodes = pathway.nodes or {}
        for conn in pathway.connections:
            # Skip connections involving pseudo-nodes (input/output)
            if conn.from_node in PSEUDO_NODES or conn.to_node in PSEUDO_NODES:
                continue
            # Skip connections to/from non-existent nodes
            if conn.from_node not in nodes or conn.to_node not in nodes:
                continue
            deps[conn.to_node].add(conn.from_node)

        in_degree = {
            node_id: len(deps.get(node_id, set())) for node_id in pathway.nodes
        }
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for other_id, other_deps in deps.items():
                if node_id in other_deps:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        if len(result) != len(pathway.nodes):
            try:
                from pathway_engine.application.validation import find_cycle

                cycle = find_cycle(pathway)
            except Exception:
                cycle = None
            if cycle:
                raise ValueError(f"Pathway contains cycles! Cycle: {' -> '.join(cycle)}")
            raise ValueError("Pathway contains cycles!")

        return result

    def _gather_inputs(
        self,
        pathway: Pathway,
        node_id: str,
        results: dict[str, dict[str, Any]],
        initial_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Gather inputs for a node from connections and initial inputs."""
        inputs: dict[str, Any] = {}

        # Start with initial inputs
        inputs.update(initial_inputs)

        # Add results from upstream nodes
        for conn in pathway.connections:
            if conn.to_node == node_id:
                upstream_result = results.get(conn.from_node, {})
                if upstream_result:
                    # Use the from_output key if it exists, otherwise use whole result
                    if conn.from_output in upstream_result:
                        value = upstream_result[conn.from_output]
                    else:
                        value = upstream_result
                    
                    # Use to_input as the target key, falling back to from_node
                    target_key = conn.to_input if conn.to_input != "input" else conn.from_node
                    inputs[target_key] = value

        return inputs

    def _should_execute(
        self,
        pathway: Pathway,
        node_id: str,
        results: dict[str, dict[str, Any]],
    ) -> bool:
        """Check if node should execute (not gated out)."""
        # Check gates
        for gate in pathway.gates:
            if gate.true_path == node_id or gate.false_path == node_id:
                # This node is controlled by a gate
                # Find the gate node's result
                for other_id, result in results.items():
                    if "selected_route" in result:
                        selected = result["selected_route"]
                        if selected != node_id:
                            return False

        # Check router results
        for conn in pathway.connections:
            if conn.to_node == node_id:
                upstream_result = results.get(conn.from_node, {})
                if "selected_route" in upstream_result:
                    if upstream_result["selected_route"] != node_id:
                        return False

        return True

    async def get_execution(self, execution_id: str) -> PathwayRecord | None:
        """Get execution record by ID."""
        return self._executions.get(execution_id)

    def get_stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        total = len(self._executions)
        completed = sum(
            1 for r in self._executions.values() if r.status == PathwayStatus.COMPLETED
        )
        failed = sum(
            1 for r in self._executions.values() if r.status == PathwayStatus.FAILED
        )

        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
        }

    def _sanitize_for_logging(
        self,
        data: Any,
        *,
        max_depth: int = 4,
        max_str_len: int = 1000,
        max_list_len: int = 20,
    ) -> Any:
        """Sanitize data for logging - truncate large values, limit depth.

        This ensures observability data doesn't explode storage or memory
        while still providing useful debugging information.
        """
        if max_depth <= 0:
            return {"_truncated": True, "_type": type(data).__name__}

        if data is None:
            return None

        if isinstance(data, (bool, int, float)):
            return data

        if isinstance(data, str):
            if len(data) > max_str_len:
                return data[:max_str_len] + f"... ({len(data)} chars total)"
            return data

        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                key = str(k) if not isinstance(k, str) else k
                result[key] = self._sanitize_for_logging(
                    v,
                    max_depth=max_depth - 1,
                    max_str_len=max_str_len,
                    max_list_len=max_list_len,
                )
            return result

        if isinstance(data, (list, tuple)):
            if len(data) > max_list_len:
                truncated = [
                    self._sanitize_for_logging(
                        item,
                        max_depth=max_depth - 1,
                        max_str_len=max_str_len,
                        max_list_len=max_list_len,
                    )
                    for item in data[:max_list_len]
                ]
                truncated.append(f"... ({len(data)} items total)")
                return truncated
            return [
                self._sanitize_for_logging(
                    item,
                    max_depth=max_depth - 1,
                    max_str_len=max_str_len,
                    max_list_len=max_list_len,
                )
                for item in data
            ]

        # For other types, convert to string representation
        try:
            s = str(data)
            if len(s) > max_str_len:
                return s[:max_str_len] + f"... ({type(data).__name__})"
            return s
        except Exception:
            return f"<{type(data).__name__}>"


__all__ = [
    "PathwayVM",
    "PathwayPriority",
]
