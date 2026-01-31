"""WebSocket endpoint handler."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from aiohttp import web, WSMsgType

from albus.transport.utils import get_runtime, jsonable

logger = logging.getLogger(__name__)


async def handle_ws(request: web.Request) -> web.WebSocketResponse:
    """GET /api/v1/ws - WebSocket stream of Albus observability events.

    Query params:
        thread_id: Optional filter to only stream events for a specific thread.
        mode: "events" (default), "rpc", or "both"
    """
    runtime = get_runtime(request)
    thread_id_filter = request.query.get("thread_id")
    mode = str(request.query.get("mode") or "events").strip().lower()
    if mode not in {"events", "rpc", "both"}:
        mode = "events"

    ws = web.WebSocketResponse(
        heartbeat=15.0,
        autoping=True,
        compress=True,
    )
    await ws.prepare(request)

    send_lock = asyncio.Lock()

    async def _send_json(obj: Any) -> None:
        try:
            data = json.dumps(jsonable(obj), ensure_ascii=False)
        except Exception:
            data = json.dumps(
                {"type": "ws_error", "error": "failed_to_serialize"}, ensure_ascii=False
            )
        async with send_lock:
            await ws.send_str(data)

    # Events stream
    event_queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=1000)

    def _on_event(event: Any) -> None:
        try:
            if thread_id_filter:
                ev_thread_id = getattr(event, "thread_id", None)
                if ev_thread_id != thread_id_filter:
                    return
            event_queue.put_nowait(event)
        except asyncio.QueueFull:
            return
        except Exception:
            return

    async def _sender() -> None:
        try:
            while True:
                event = await event_queue.get()
                await _send_json(event)
        except asyncio.CancelledError:
            raise
        except Exception:
            return

    sender_task: asyncio.Task[None] | None = None
    if mode in {"events", "both"}:
        runtime.on_all(_on_event)
        sender_task = asyncio.create_task(_sender())

    # JSON-RPC control plane
    def _is_jsonrpc(msg: Any) -> bool:
        return (
            isinstance(msg, dict)
            and msg.get("jsonrpc") == "2.0"
            and isinstance(msg.get("method"), str)
        )

    def _rpc_ok(id_: Any, result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": id_, "result": result}

    def _rpc_err(
        id_: Any, code: int, message: str, data: Any | None = None
    ) -> dict[str, Any]:
        err: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            err["data"] = data
        return {"jsonrpc": "2.0", "id": id_, "error": err}

    def _get_pathway_vm() -> Any | None:
        try:
            vm = getattr(runtime, "pathway_vm", None)
        except Exception:
            vm = None
        return vm

    stream_tasks: dict[str, asyncio.Task[None]] = {}

    async def _start_stream(
        *, pathway_id: str, inputs: dict[str, Any], max_events: int | None
    ) -> str:
        vm = _get_pathway_vm()
        if vm is None:
            raise RuntimeError("PathwayVM not available")

        pathway = runtime.pathway_service.load(pathway_id)
        if pathway is None:
            raise RuntimeError(f"Pathway not found: {pathway_id}")

        stream_id = f"ps_{uuid.uuid4().hex[:12]}"

        async def _runner() -> None:
            try:
                async for tick in vm.stream_execute(
                    pathway, inputs, max_events=max_events
                ):
                    await _send_json(
                        {
                            "jsonrpc": "2.0",
                            "method": "pathway.tick",
                            "params": {
                                "stream_id": stream_id,
                                "pathway_id": pathway_id,
                                "tick": tick,
                            },
                        }
                    )
                await _send_json(
                    {
                        "jsonrpc": "2.0",
                        "method": "pathway.complete",
                        "params": {"stream_id": stream_id, "pathway_id": pathway_id},
                    }
                )
            except asyncio.CancelledError:
                await _send_json(
                    {
                        "jsonrpc": "2.0",
                        "method": "pathway.cancelled",
                        "params": {"stream_id": stream_id, "pathway_id": pathway_id},
                    }
                )
                raise
            except Exception as e:
                await _send_json(
                    {
                        "jsonrpc": "2.0",
                        "method": "pathway.error",
                        "params": {
                            "stream_id": stream_id,
                            "pathway_id": pathway_id,
                            "error": str(e),
                        },
                    }
                )
            finally:
                stream_tasks.pop(stream_id, None)

        stream_tasks[stream_id] = asyncio.create_task(_runner())
        return stream_id

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                txt = (msg.data or "").strip()
                if not txt:
                    continue
                if txt == "ping":
                    async with send_lock:
                        await ws.send_str("pong")
                    continue
                try:
                    data = json.loads(txt)
                except Exception:
                    continue
                if isinstance(data, dict) and data.get("type") == "ping":
                    await _send_json(
                        {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        }
                    )
                    continue

                if mode in {"rpc", "both"} and _is_jsonrpc(data):
                    rpc_id = data.get("id")
                    method = data.get("method")
                    params = data.get("params") or {}
                    if not isinstance(params, dict):
                        await _send_json(_rpc_err(rpc_id, -32602, "Invalid params"))
                        continue

                    try:
                        if method == "pathway.stream_start":
                            pathway_id = str(params.get("pathway_id") or "").strip()
                            if not pathway_id:
                                await _send_json(
                                    _rpc_err(rpc_id, -32602, "pathway_id is required")
                                )
                                continue
                            inputs = params.get("inputs") or {}
                            if not isinstance(inputs, dict):
                                await _send_json(
                                    _rpc_err(rpc_id, -32602, "inputs must be an object")
                                )
                                continue
                            max_events = params.get("max_events")
                            if max_events is not None:
                                try:
                                    max_events = int(max_events)
                                except Exception:
                                    await _send_json(
                                        _rpc_err(
                                            rpc_id,
                                            -32602,
                                            "max_events must be an integer",
                                        )
                                    )
                                    continue
                            stream_id = await _start_stream(
                                pathway_id=pathway_id,
                                inputs=inputs,
                                max_events=max_events,
                            )
                            await _send_json(_rpc_ok(rpc_id, {"stream_id": stream_id}))

                        elif method == "pathway.stream_cancel":
                            stream_id = str(params.get("stream_id") or "").strip()
                            if not stream_id:
                                await _send_json(
                                    _rpc_err(rpc_id, -32602, "stream_id is required")
                                )
                                continue
                            task = stream_tasks.get(stream_id)
                            if not task:
                                await _send_json(
                                    _rpc_err(rpc_id, -32001, "Unknown stream_id")
                                )
                                continue
                            task.cancel()
                            await _send_json(
                                _rpc_ok(
                                    rpc_id, {"cancelled": True, "stream_id": stream_id}
                                )
                            )

                        else:
                            await _send_json(
                                _rpc_err(
                                    rpc_id,
                                    -32601,
                                    "Method not found",
                                    {"method": method},
                                )
                            )
                    except Exception as e:
                        await _send_json(
                            _rpc_err(rpc_id, -32000, "Server error", {"error": str(e)})
                        )
            elif msg.type == WSMsgType.ERROR:
                break
    finally:
        for t in list(stream_tasks.values()):
            t.cancel()
        await asyncio.gather(*list(stream_tasks.values()), return_exceptions=True)

        if sender_task is not None:
            sender_task.cancel()
            await asyncio.gather(sender_task, return_exceptions=True)
        try:
            if mode in {"events", "both"}:
                runtime.off_all(_on_event)
        except (AttributeError, RuntimeError) as e:
            # Gracefully handle cleanup errors (runtime might be shutting down)
            logger.debug("Error during WebSocket cleanup: %s", e)
        except Exception as e:
            # Catch-all for unexpected cleanup errors
            logger.warning("Unexpected error during WebSocket cleanup: %s", e)

    return ws


__all__ = [
    "handle_ws",
]
