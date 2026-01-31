"""Standardized error handling for Albus API.

Provides consistent error response format and error code enumeration.
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Client errors (4xx)
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Server errors (5xx)
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    GATEWAY_ERROR = "gateway_error"

    # Pathway-specific errors
    PATHWAY_NOT_FOUND = "pathway_not_found"
    PATHWAY_EXECUTION_FAILED = "pathway_execution_failed"
    PATHWAY_INVALID = "pathway_invalid"

    # Tool-specific errors
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"

    # Thread-specific errors
    THREAD_NOT_FOUND = "thread_not_found"

    # Generic
    UNKNOWN_ERROR = "unknown_error"


def create_error_response(
    error: str,
    code: ErrorCode | str,
    *,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response.

    Args:
        error: Human-readable error message
        code: Error code (ErrorCode enum or string)
        request_id: Optional request ID for correlation
        details: Optional additional error details
    Returns:
        Standardized error response dict
    """
    if isinstance(code, ErrorCode):
        code_str = code.value
    else:
        code_str = str(code)

    response: dict[str, Any] = {
        "success": False,
        "error": error,
        "code": code_str,
    }

    if request_id:
        response["request_id"] = request_id

    if details:
        response["details"] = details

    return response


def sanitize_error_message(error: str, is_production: bool | None = None) -> str:
    """Sanitize error messages for production.

    In production, avoid leaking internal details like stack traces,
    file paths, or implementation details.

    Args:
        error: Raw error message
        is_production: Whether we're in production (auto-detected if None)

    Returns:
        Sanitized error message
    """
    if is_production is None:
        env = os.getenv("ALBUS_ENV", "").lower()
        is_production = env in ("production", "prod")

    if not is_production:
        return error

    # In production, return generic messages for internal errors
    # but keep user-facing validation errors as-is
    if any(
        phrase in error.lower()
        for phrase in [
            "traceback",
            "file",
            "line",
            "exception",
            "trace",
            "stack",
            "internal",
        ]
    ):
        return "An internal error occurred. Please try again or contact support."

    return error


def get_status_code_for_error_code(code: ErrorCode | str) -> int:
    """Map error code to HTTP status code.

    Args:
        code: Error code

    Returns:
        HTTP status code
    """
    code_str = code.value if isinstance(code, ErrorCode) else str(code)

    # Client errors
    if code_str in (
        ErrorCode.BAD_REQUEST.value,
        ErrorCode.VALIDATION_ERROR.value,
    ):
        return 400
    if code_str == ErrorCode.UNAUTHORIZED.value:
        return 401
    if code_str == ErrorCode.FORBIDDEN.value:
        return 403
    if code_str in (
        ErrorCode.NOT_FOUND.value,
        ErrorCode.PATHWAY_NOT_FOUND.value,
        ErrorCode.TOOL_NOT_FOUND.value,
        ErrorCode.THREAD_NOT_FOUND.value,
    ):
        return 404
    if code_str == ErrorCode.CONFLICT.value:
        return 409
    if code_str == ErrorCode.RATE_LIMIT_EXCEEDED.value:
        return 429

    # Server errors
    if code_str == ErrorCode.SERVICE_UNAVAILABLE.value:
        return 503
    if code_str == ErrorCode.TIMEOUT.value:
        return 504
    if code_str == ErrorCode.GATEWAY_ERROR.value:
        return 502

    # Default to 500 for internal errors
    return 500


__all__ = [
    "ErrorCode",
    "create_error_response",
    "sanitize_error_message",
    "get_status_code_for_error_code",
]
