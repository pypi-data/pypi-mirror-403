"""OpenAPI spec generation for Albus HTTP transport.

We keep this intentionally lightweight (no third-party OpenAPI generator) so it
can't drift away from the actual code and is easy to edit.
"""

from __future__ import annotations

from typing import Any


def build_openapi_spec(*, base_url: str = "/api/v1") -> dict[str, Any]:
    # Minimal, professional baseline. Extend as needed.
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "AlbusOS API",
            "version": "1.0",
            "description": "AlbusOS HTTP + WebSocket API (v1).",
        },
        "servers": [{"url": base_url}],
        "tags": [
            {"name": "infrastructure"},
            {"name": "packs"},
            {"name": "tools"},
            {"name": "pathways"},
            {"name": "threads"},
            {"name": "realtime"},
            {"name": "docs"},
        ],
        "paths": {
            "/": {
                "get": {
                    "tags": ["docs"],
                    "summary": "API discovery",
                    "description": "Returns an endpoint map and basic server metadata.",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/help": {
                "get": {
                    "tags": ["docs"],
                    "summary": "API help",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/openapi.json": {
                "get": {
                    "tags": ["docs"],
                    "summary": "OpenAPI specification (v1)",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/docs": {
                "get": {
                    "tags": ["docs"],
                    "summary": "Interactive API documentation (Swagger UI)",
                    "responses": {"200": {"description": "HTML"}},
                }
            },
            "/health": {
                "get": {
                    "tags": ["infrastructure"],
                    "summary": "Health check",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/config/validate": {
                "get": {
                    "tags": ["infrastructure"],
                    "summary": "Validate configuration",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/node-types": {
                "get": {
                    "tags": ["infrastructure"],
                    "summary": "List node types",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/tools": {
                "get": {
                    "tags": ["tools"],
                    "summary": "List registered tools",
                    "parameters": [
                        {
                            "name": "category",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "format",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "enum": ["list", "grouped"]},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/tools/{tool_name}": {
                "post": {
                    "tags": ["tools"],
                    "summary": "Call a tool",
                    "parameters": [
                        {
                            "name": "tool_name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/pathways": {
                "get": {
                    "tags": ["pathways"],
                    "summary": "List pathways",
                    "responses": {"200": {"description": "OK"}},
                },
                "post": {
                    "tags": ["pathways"],
                    "summary": "Create a pathway",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "responses": {"200": {"description": "OK"}},
                },
            },
            "/pathways/import": {
                "post": {
                    "tags": ["pathways"],
                    "summary": "Import a pathway",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/pathways/{pathway_id}": {
                "get": {
                    "tags": ["pathways"],
                    "summary": "Get pathway",
                    "parameters": [
                        {
                            "name": "pathway_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                    },
                }
            },
            "/pathways/{pathway_id}/run": {
                "post": {
                    "tags": ["pathways"],
                    "summary": "Run a pathway",
                    "parameters": [
                        {
                            "name": "pathway_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                    },
                }
            },
            "/pathways/{pathway_id}/export": {
                "get": {
                    "tags": ["pathways"],
                    "summary": "Export a pathway",
                    "parameters": [
                        {
                            "name": "pathway_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                    },
                }
            },
            "/pathways/{pathway_id}/graph": {
                "get": {
                    "tags": ["pathways"],
                    "summary": "Get pathway graph payload",
                    "parameters": [
                        {
                            "name": "pathway_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                    },
                }
            },
            "/threads": {
                "get": {
                    "tags": ["threads"],
                    "summary": "List threads",
                    "parameters": [
                        {
                            "name": "workspace_id",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/threads/{thread_id}": {
                "get": {
                    "tags": ["threads"],
                    "summary": "Get thread",
                    "parameters": [
                        {
                            "name": "thread_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                    },
                },
                "delete": {
                    "tags": ["threads"],
                    "summary": "Delete/end thread",
                    "parameters": [
                        {
                            "name": "thread_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            },
            "/webhooks/{topic}": {
                "post": {
                    "tags": ["realtime"],
                    "summary": "Publish webhook event (in-memory bus)",
                    "parameters": [
                        {
                            "name": "topic",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
        "components": {
            "schemas": {},
        },
    }

