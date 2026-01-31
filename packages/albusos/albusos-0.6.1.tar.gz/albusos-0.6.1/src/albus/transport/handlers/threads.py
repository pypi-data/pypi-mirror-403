"""Thread endpoint handlers."""

from __future__ import annotations

from aiohttp import web

from albus.infrastructure.errors import ErrorCode
from albus.transport.utils import error_response, get_runtime


async def handle_list_threads(request: web.Request) -> web.Response:
    """GET /api/v1/threads - List threads."""
    runtime = get_runtime(request)

    workspace_id = request.query.get("workspace_id")
    limit = int(request.query.get("limit", 100))

    threads = await runtime.list_threads(workspace_id=workspace_id, limit=limit)

    return web.json_response({"threads": threads})


async def handle_get_thread(request: web.Request) -> web.Response:
    """GET /api/v1/threads/{thread_id} - Get thread info."""
    runtime = get_runtime(request)
    thread_id = request.match_info["thread_id"]

    info = await runtime.get_thread(thread_id)

    if info is None:
        return error_response(
            request,
            f"Thread not found: {thread_id}",
            ErrorCode.THREAD_NOT_FOUND,
            status=404,
        )

    return web.json_response(info)


async def handle_delete_thread(request: web.Request) -> web.Response:
    """DELETE /api/v1/threads/{thread_id} - End/delete a thread."""
    runtime = get_runtime(request)
    thread_id = request.match_info["thread_id"]

    deleted = await runtime.end_thread(thread_id)

    return web.json_response({"deleted": deleted})


async def handle_send_event(request: web.Request) -> web.Response:
    """POST /api/v1/threads/{thread_id}/events - Send event to state machine.
    
    Request body:
        {
            "state_machine_id": "host.v1",
            "event": "task",
            "payload": {"task": "Do something"}
        }
    
    Response:
        {
            "success": true,
            "thread_id": "...",
            "state": "planning",
            "result": {...}
        }
    """
    runtime = get_runtime(request)
    thread_id = request.match_info["thread_id"]
    
    try:
        body = await request.json()
    except Exception:
        return error_response(
            request,
            "Invalid JSON body",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    state_machine_id = body.get("state_machine_id", "host.v1")
    event = body.get("event")
    payload = body.get("payload", {})
    
    if not event:
        return error_response(
            request,
            "Missing 'event' field",
            ErrorCode.VALIDATION_ERROR,
            status=400,
        )
    
    try:
        result = await runtime.send_event(
            thread_id=thread_id,
            event=event,
            payload=payload,
            state_machine_id=state_machine_id,
        )
        
        # result is a dict from runtime.send_event()
        return web.json_response({
            "success": result.get("success", False),
            "thread_id": thread_id,
            "from_state": result.get("from_state"),
            "to_state": result.get("to_state"),
            "error": result.get("error"),
            "emitted_events": result.get("emitted_events", []),
        })
    except Exception as e:
        return error_response(
            request,
            str(e),
            ErrorCode.INTERNAL_ERROR,
            status=500,
        )


__all__ = [
    "handle_list_threads",
    "handle_get_thread",
    "handle_delete_thread",
    "handle_send_event",
]
