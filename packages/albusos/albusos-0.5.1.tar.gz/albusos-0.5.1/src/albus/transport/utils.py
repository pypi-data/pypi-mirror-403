"""Common utilities for HTTP handlers."""

from __future__ import annotations

import dataclasses
from datetime import datetime
from enum import Enum
from typing import Any

from aiohttp import web

from albus.infrastructure.errors import ErrorCode, create_error_response

# aiohttp best practice: use AppKey rather than bare string keys for app state.
# This prevents accidental key collisions and removes NotAppKeyWarning.
RUNTIME_KEY: web.AppKey[Any] = web.AppKey("albus.runtime", Any)


def jsonable(obj: Any) -> Any:
    """Convert object to JSON-serializable primitives."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if dataclasses.is_dataclass(obj):
        return {k: jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    return obj


async def parse_json_body(request: web.Request) -> dict[str, Any] | None:
    """Parse JSON body from request, return None if invalid."""
    try:
        return await request.json()
    except Exception:
        return None


def get_request_id(request: web.Request) -> str:
    """Get request ID from request."""
    return request.get("request_id", "unknown")


def error_response(
    request: web.Request,
    error: str,
    code: ErrorCode,
    status: int = 400,
    details: dict[str, Any] | None = None,
) -> web.Response:
    """Create standardized error response."""
    return web.json_response(
        create_error_response(
            error=error,
            code=code,
            request_id=get_request_id(request),
            details=details,
        ),
        status=status,
    )


def get_runtime(request: web.Request) -> Any:
    """Get runtime from app state."""
    return request.app[RUNTIME_KEY]


__all__ = [
    "jsonable",
    "parse_json_body",
    "get_request_id",
    "error_response",
    "get_runtime",
    "RUNTIME_KEY",
]
