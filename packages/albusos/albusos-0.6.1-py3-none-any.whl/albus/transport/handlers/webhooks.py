"""Webhook endpoint handlers."""

from __future__ import annotations

from typing import Any

from aiohttp import web

from albus.infrastructure.errors import ErrorCode, sanitize_error_message
from albus.transport.utils import error_response, get_request_id, parse_json_body


async def handle_webhook(request: web.Request) -> web.Response:
    """POST /api/v1/webhooks/{topic} - Publish a webhook event into the in-memory bus."""
    request_id = get_request_id(request)

    topic = str(request.match_info.get("topic", "")).strip()
    if not topic:
        return error_response(
            request, "topic is required", ErrorCode.VALIDATION_ERROR, status=400
        )

    body = await parse_json_body(request)

    payload: dict[str, Any]
    if isinstance(body, dict):
        payload = body
    elif body is None:
        payload = {"raw": None}
    else:
        payload = {"raw": body}

    # Publish into the in-memory bus
    from pathway_engine.domain.streaming import WEBHOOK_BUS

    delivered = WEBHOOK_BUS.publish(topic, payload)

    return web.json_response({"success": True, "topic": topic, "delivered": delivered})


__all__ = [
    "handle_webhook",
]
