"""HTTP/REST transport for Albus.

This is a thin translation layer - no business logic.
Routes are organized by domain in handlers/ subdirectory.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiohttp import web

from albus.infrastructure.middleware import (
    cors_middleware,
    error_handler_middleware,
    logging_middleware,
    request_id_middleware,
)
from albus.transport.routes import register_routes
from albus.transport.utils import RUNTIME_KEY

if TYPE_CHECKING:
    from albus.application.ports import RuntimePort

logger = logging.getLogger(__name__)


def create_http_app(runtime: "RuntimePort") -> web.Application:
    """Create aiohttp application with Albus routes.

    Args:
        runtime: AlbusRuntime (or anything implementing RuntimePort)

    Returns:
        Configured aiohttp Application
    """
    app = web.Application()

    # Store runtime in app state
    app[RUNTIME_KEY] = runtime

    # Add middleware (order matters: request_id -> logging -> error_handler -> cors)
    app.middlewares.append(request_id_middleware)
    app.middlewares.append(logging_middleware)
    app.middlewares.append(error_handler_middleware)
    app.middlewares.append(cors_middleware)

    # Register all routes
    register_routes(app)

    logger.info("HTTP routes registered")
    return app


__all__ = [
    "create_http_app",
]
