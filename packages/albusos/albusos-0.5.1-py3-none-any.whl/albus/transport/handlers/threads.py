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


__all__ = [
    "handle_list_threads",
    "handle_get_thread",
    "handle_delete_thread",
]
