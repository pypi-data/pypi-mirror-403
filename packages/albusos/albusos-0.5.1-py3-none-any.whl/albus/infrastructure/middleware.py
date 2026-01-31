"""HTTP middleware for request tracking and error handling."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from aiohttp import web

from albus.infrastructure.errors import (
    ErrorCode,
    create_error_response,
    sanitize_error_message,
)

logger = logging.getLogger(__name__)


@web.middleware
async def request_id_middleware(request: web.Request, handler: Any) -> web.Response:
    """Add request ID to all requests for correlation.

    Sets request_id in request['request_id'] and adds X-Request-ID header.
    """
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    request["request_id"] = request_id

    response = await handler(request)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


@web.middleware
async def error_handler_middleware(request: web.Request, handler: Any) -> web.Response:
    """Standardize error responses and add request tracking.

    Catches exceptions and converts them to standardized error responses.
    """
    request_id = request.get("request_id", "unknown")
    start_time = time.time()

    try:
        response = await handler(request)
        duration_ms = (time.time() - start_time) * 1000

        # Add timing header
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        return response

    except web.HTTPException as e:
        # aiohttp HTTP exceptions (like 404, 400, etc.)
        duration_ms = (time.time() - start_time) * 1000
        error_code = ErrorCode.BAD_REQUEST
        if e.status == 404:
            error_code = ErrorCode.NOT_FOUND
        elif e.status == 401:
            error_code = ErrorCode.UNAUTHORIZED
        elif e.status == 403:
            error_code = ErrorCode.FORBIDDEN
        elif e.status == 409:
            error_code = ErrorCode.CONFLICT

        error_msg = sanitize_error_message(
            str(e.reason) or "Request failed", is_production=None
        )

        logger.warning(
            "HTTP error: %s (code=%s, request_id=%s, duration_ms=%.2f)",
            error_msg,
            error_code,
            request_id,
            duration_ms,
        )

        return web.json_response(
            create_error_response(
                error=error_msg,
                code=error_code,
                request_id=request_id,
            ),
            status=e.status,
        )

    except Exception as e:
        # Unexpected exceptions
        duration_ms = (time.time() - start_time) * 1000
        error_msg = sanitize_error_message(str(e), is_production=None)

        logger.exception(
            "Unhandled exception: %s (request_id=%s, duration_ms=%.2f, path=%s)",
            error_msg,
            request_id,
            duration_ms,
            request.path,
        )

        return web.json_response(
            create_error_response(
                error=error_msg,
                code=ErrorCode.INTERNAL_ERROR,
                request_id=request_id,
            ),
            status=500,
        )


@web.middleware
async def logging_middleware(request: web.Request, handler: Any) -> web.Response:
    """Log request/response for observability.

    Logs structured information about each request.
    """
    request_id = request.get("request_id", "unknown")
    start_time = time.time()

    # Log request
    logger.info(
        "Request: %s %s (request_id=%s, remote=%s)",
        request.method,
        request.path_qs,
        request_id,
        request.remote,
    )

    response = await handler(request)
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    logger.info(
        "Response: %s %s -> %d (request_id=%s, duration_ms=%.2f)",
        request.method,
        request.path_qs,
        response.status,
        request_id,
        duration_ms,
    )

    return response


@web.middleware
async def cors_middleware(request: web.Request, handler: Any) -> web.Response:
    """Add CORS headers for browser clients."""
    # Handle preflight
    if request.method == "OPTIONS":
        return web.Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    # Handle actual request
    response = await handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


__all__ = [
    "request_id_middleware",
    "error_handler_middleware",
    "logging_middleware",
    "cors_middleware",
]
