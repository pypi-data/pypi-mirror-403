"""Vector Memory Tools - Semantic search and embedding storage.

These tools provide vector memory capabilities for pathways:
- vector.search: Semantic search over stored embeddings
- vector.upsert: Store text with embeddings
- vector.delete: Remove stored entries
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext

from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool(
    "vector.search",
    description="Semantic search over vector memory using embeddings.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query to search for",
            },
            "scope": {
                "type": "string",
                "description": "Search scope (e.g., 'workspace:id', 'chat:thread_id'). Default: 'default'",
            },
            "k": {
                "type": "integer",
                "description": "Number of results to return. Default: 5",
            },
            "min_score": {
                "type": "number",
                "description": "Minimum similarity score (0-1). Default: 0.0",
            },
            "filters": {
                "type": "object",
                "description": "Metadata filters to apply",
            },
        },
        "required": ["query"],
    },
)
async def vector_search(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Semantic search over vector memory.

    Returns:
        {
            "results": [
                {
                    "id": str,
                    "text": str,
                    "score": float,
                    "metadata": dict,
                }
            ],
            "total": int,
        }
    """
    query = str(inputs.get("query", "")).strip()
    if not query:
        return {"success": False, "error": "query is required", "results": []}

    scope = str(inputs.get("scope", "default")).strip()
    k = int(inputs.get("k", 5))
    min_score = float(inputs.get("min_score", 0.0))
    filters = inputs.get("filters")

    start_time = time.time()

    # Get vector memory from context
    vector_memory = context.extras.get("vector_memory")
    if vector_memory is None:
        # Try to get from pathway_executor
        pathway_executor = context.pathway_executor
        if pathway_executor and hasattr(pathway_executor, "vector_memory"):
            vector_memory = pathway_executor.vector_memory

    if vector_memory is None:
        return {
            "success": False,
            "error": "Vector memory not available",
            "results": [],
        }

    try:
        results = await vector_memory.search(
            scope=scope,
            query=query,
            k=k,
            filters=filters,
        )

        # Filter by min_score and convert to dicts
        filtered = []
        for r in results:
            score = getattr(r, "score", 0)
            if score >= min_score:
                filtered.append(
                    {
                        "id": getattr(r, "id", ""),
                        "text": getattr(r, "text", ""),
                        "score": round(score, 4),
                        "metadata": getattr(r, "metadata", {}),
                    }
                )

        duration_ms = (time.time() - start_time) * 1000

        return {
            "success": True,
            "results": filtered,
            "total": len(filtered),
            "scope": scope,
            "query": query,
            "duration_ms": duration_ms,
        }

    except Exception as e:
        logger.error("Vector search failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "results": [],
        }


@register_tool(
    "vector.upsert",
    description="Store text with embeddings in vector memory.",
    parameters={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to store and embed",
            },
            "scope": {
                "type": "string",
                "description": "Storage scope. Default: 'default'",
            },
            "source_id": {
                "type": "string",
                "description": "Source identifier for grouping/deletion",
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata to store",
            },
            "chunk_size": {
                "type": "integer",
                "description": "Max characters per chunk. Default: 1200",
            },
            "chunk_overlap": {
                "type": "integer",
                "description": "Overlap between chunks. Default: 200",
            },
        },
        "required": ["text"],
    },
)
async def vector_upsert(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Store text with embeddings.

    The text is chunked, embedded, and stored for later retrieval.

    Returns:
        {
            "chunks_added": int,
            "ids": list[str],
        }
    """
    text = str(inputs.get("text", "")).strip()
    if not text:
        return {"success": False, "error": "text is required", "chunks_added": 0}

    scope = str(inputs.get("scope", "default")).strip()
    source_id = inputs.get("source_id")
    metadata = inputs.get("metadata", {})
    chunk_size = int(inputs.get("chunk_size", 1200))
    chunk_overlap = int(inputs.get("chunk_overlap", 200))

    # Get vector memory from context
    vector_memory = context.extras.get("vector_memory")
    if vector_memory is None:
        pathway_executor = context.pathway_executor
        if pathway_executor and hasattr(pathway_executor, "vector_memory"):
            vector_memory = pathway_executor.vector_memory

    if vector_memory is None:
        return {
            "success": False,
            "error": "Vector memory not available",
            "chunks_added": 0,
        }

    try:
        result = await vector_memory.upsert_text(
            scope=scope,
            text=text,
            metadata=metadata,
            source_id=source_id,
            chunk_max_chars=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        return {
            "success": True,
            "chunks_added": result.get("chunks_added", 0),
            "ids": result.get("ids", []),
            "scope": scope,
        }

    except Exception as e:
        logger.error("Vector upsert failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "chunks_added": 0,
        }


@register_tool(
    "vector.delete",
    description="Delete entries from vector memory.",
    parameters={
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "description": "Storage scope",
            },
            "source_id": {
                "type": "string",
                "description": "Source identifier to delete",
            },
        },
        "required": ["scope", "source_id"],
    },
)
async def vector_delete(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Delete entries from vector memory by source_id.

    Returns:
        {
            "deleted": int,
        }
    """
    scope = str(inputs.get("scope", "")).strip()
    source_id = str(inputs.get("source_id", "")).strip()

    if not scope or not source_id:
        return {"success": False, "error": "scope and source_id required", "deleted": 0}

    # Get vector memory from context
    vector_memory = context.extras.get("vector_memory")
    if vector_memory is None:
        pathway_executor = context.pathway_executor
        if pathway_executor and hasattr(pathway_executor, "vector_memory"):
            vector_memory = pathway_executor.vector_memory

    if vector_memory is None:
        return {
            "success": False,
            "error": "Vector memory not available",
            "deleted": 0,
        }

    try:
        result = await vector_memory.delete_source(scope=scope, source_id=source_id)

        return {
            "success": True,
            "deleted": result.get("deleted", 0),
            "scope": scope,
            "source_id": source_id,
        }

    except Exception as e:
        logger.error("Vector delete failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "deleted": 0,
        }


__all__ = [
    "vector_search",
    "vector_upsert",
    "vector_delete",
]
