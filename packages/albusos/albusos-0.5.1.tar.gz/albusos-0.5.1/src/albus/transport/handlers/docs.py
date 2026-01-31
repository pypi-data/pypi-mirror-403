"""Docs endpoints (OpenAPI + Swagger UI)."""

from __future__ import annotations

from aiohttp import web

from albus.transport.openapi_spec import build_openapi_spec


async def handle_openapi(_: web.Request) -> web.Response:
    """GET /api/v1/openapi.json - OpenAPI 3.0 spec for Albus API."""
    spec = build_openapi_spec(base_url="/api/v1")
    return web.json_response(spec)


async def handle_docs(_: web.Request) -> web.Response:
    """GET /api/v1/docs - Swagger UI HTML page."""
    # Uses CDN for swagger-ui assets to keep the repo lightweight.
    # If we want offline/airgapped, we can vendor the static assets later.
    html = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AlbusOS API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; background: #0b0f19; }
      #swagger-ui { background: white; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = () => {
        SwaggerUIBundle({
          url: '/api/v1/openapi.json',
          dom_id: '#swagger-ui',
          deepLinking: true,
          displayRequestDuration: true
        });
      };
    </script>
  </body>
</html>
"""
    return web.Response(text=html, content_type="text/html")


__all__ = ["handle_openapi", "handle_docs"]
