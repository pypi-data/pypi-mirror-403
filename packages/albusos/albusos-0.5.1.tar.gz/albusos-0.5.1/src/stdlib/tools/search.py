"""Search Tools - Query and search capabilities.

These are callable capabilities for pathways to search and query.
Uses StudioDomainPort for workspace search and pathway executor for vector memory.

Tools receive dependencies via ToolContext - no globals, no service locators.
"""

from __future__ import annotations

import logging
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("search.workspace")
async def search_workspace(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Search workspace files by content or name.

    Inputs:
        query: Search query
        file_types: File types to search (optional)
        max_results: Maximum results (default: 10)

    Returns:
        results: List of matching files with snippets
    """
    query = str(inputs.get("query", "")).strip()
    file_types = inputs.get("file_types", [])
    max_results = int(inputs.get("max_results", 10))

    if not query:
        return {"success": False, "error": "query is required", "results": []}

    workspace_id = context.workspace_id

    if context.domain and workspace_id:
        try:
            tree = context.domain.get_tree(workspace_id=str(workspace_id))

            results = []
            query_lower = query.lower()

            def search_tree(node: Any, path: str = "") -> None:
                if hasattr(node, "documents"):
                    for doc in node.documents:
                        doc_type = getattr(doc, "type", "")
                        if file_types and doc_type not in file_types:
                            continue

                        doc_name = getattr(doc, "name", "")
                        doc_id = getattr(doc, "id", "")
                        doc_path = f"{path}/{doc_name}" if path else doc_name

                        # Search in name first
                        if query_lower in doc_name.lower():
                            results.append(
                                {
                                    "doc_id": doc_id,
                                    "path": doc_path,
                                    "name": doc_name,
                                    "type": doc_type,
                                    "match_type": "name",
                                    "snippet": doc_name,
                                }
                            )
                            return

                        # Try to search in content
                        try:
                            content = context.domain.get_head_content(doc_id=doc_id)
                            content_str = str(content)
                            if query_lower in content_str.lower():
                                idx = content_str.lower().find(query_lower)
                                start = max(0, idx - 50)
                                end = min(len(content_str), idx + len(query) + 50)
                                snippet = content_str[start:end]
                                if start > 0:
                                    snippet = "..." + snippet
                                if end < len(content_str):
                                    snippet = snippet + "..."

                                results.append(
                                    {
                                        "doc_id": doc_id,
                                        "path": doc_path,
                                        "name": doc_name,
                                        "type": doc_type,
                                        "match_type": "content",
                                        "snippet": snippet,
                                    }
                                )
                        except Exception:
                            pass

                if hasattr(node, "folders"):
                    for folder in node.folders:
                        folder_path = f"{path}/{folder.name}" if path else folder.name
                        search_tree(folder, folder_path)

                if len(results) >= max_results:
                    return

            search_tree(tree)

            return {
                "success": True,
                "query": query,
                "results": results[:max_results],
                "total_matches": len(results),
            }
        except Exception as e:
            logger.warning("Workspace search failed: %s", e)
            return {"success": False, "error": str(e), "results": []}

    return {"success": False, "error": "workspace not available", "results": []}


@register_tool("search.semantic")
async def semantic_search(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Semantic search using vector embeddings.

    Inputs:
        query: Natural language query
        scope: Search scope (workspace, documents, pathways, chat)
        max_results: Maximum results (default: 5)
        min_score: Minimum similarity score (default: 0.5)

    Returns:
        results: List of semantically similar items
    """
    query = str(inputs.get("query", "")).strip()
    scope = str(inputs.get("scope", "workspace")).strip()
    max_results = int(inputs.get("max_results", 5))
    min_score = float(inputs.get("min_score", 0.5))

    if not query:
        return {"success": False, "error": "query is required", "results": []}

    workspace_id = context.workspace_id

    if context.pathway_executor:
        try:
            from stdlib.perception.vector_memory import retrieve_memory_context

            # Build scope identifier
            if scope == "workspace" and workspace_id:
                search_scope = f"workspace:{workspace_id}"
            elif scope == "chat":
                thread_id = context.thread_id or "default"
                search_scope = f"chat:{thread_id}"
            elif scope == "pathways" and workspace_id:
                search_scope = f"pathways:{workspace_id}"
            else:
                search_scope = scope

            context_text, hits = await retrieve_memory_context(
                pathway_vm=context.pathway_executor,
                scope=search_scope,
                query=query,
                k=max_results * 2,
                policy_kwargs={"workspace_id": workspace_id} if workspace_id else None,
            )

            results = []
            for hit in hits:
                score = hit.get("score", 0)
                if score >= min_score:
                    results.append(
                        {
                            "id": hit.get("id"),
                            "text": hit.get("text", ""),
                            "score": round(score, 4),
                            "scope": search_scope,
                        }
                    )

            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            results = results[:max_results]

            return {
                "success": True,
                "query": query,
                "scope": search_scope,
                "results": results,
                "total_matches": len(results),
            }
        except Exception as e:
            logger.warning("Semantic search failed: %s", e)
            return await search_workspace(
                {"query": query, "max_results": max_results},
                context,
            )

    return {"success": False, "error": "pathway executor not available", "results": []}


@register_tool("search.pathways")
async def search_pathways(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Search pathways by name, description, or capability.

    Inputs:
        query: Search query
        tags: Filter by tags (optional)
        workspace_id: Workspace to search (optional)

    Returns:
        results: List of matching pathways
    """
    query = str(inputs.get("query", "")).strip()
    tags = inputs.get("tags", [])
    workspace_id = inputs.get("workspace_id") or context.workspace_id

    if context.domain and workspace_id:
        try:
            tree = context.domain.get_tree(workspace_id=str(workspace_id))

            results = []
            query_lower = query.lower() if query else ""

            def search_flows(node: Any, path: str = "") -> None:
                if hasattr(node, "documents"):
                    for doc in node.documents:
                        if getattr(doc, "type", "") != "flow":
                            continue

                        doc_name = getattr(doc, "name", "")
                        doc_id = getattr(doc, "id", "")
                        doc_path = f"{path}/{doc_name}" if path else doc_name

                        name_match = (
                            query_lower in doc_name.lower() if query_lower else True
                        )

                        description = ""
                        pathway_tags = []
                        node_count = 0

                        try:
                            content = context.domain.get_head_content(doc_id=doc_id)
                            description = str(content.get("description", ""))
                            pathway_tags = content.get("metadata", {}).get("tags", [])
                            node_count = len(content.get("nodes", []))
                        except Exception:
                            pass

                        desc_match = (
                            query_lower in description.lower() if query_lower else True
                        )

                        tag_match = True
                        if tags:
                            tag_match = any(t in pathway_tags for t in tags)

                        if (name_match or desc_match) and tag_match:
                            results.append(
                                {
                                    "id": doc_id,
                                    "name": doc_name,
                                    "path": doc_path,
                                    "description": (
                                        description[:200] if description else ""
                                    ),
                                    "tags": pathway_tags,
                                    "node_count": node_count,
                                    "match_type": (
                                        "name" if name_match else "description"
                                    ),
                                }
                            )

                if hasattr(node, "folders"):
                    for folder in node.folders:
                        folder_path = f"{path}/{folder.name}" if path else folder.name
                        search_flows(folder, folder_path)

            search_flows(tree)

            return {
                "success": True,
                "query": query,
                "tags": tags,
                "results": results,
                "total_matches": len(results),
            }
        except Exception as e:
            logger.warning("Pathway search failed: %s", e)
            return {"success": False, "error": str(e), "results": []}

    return {"success": False, "error": "workspace not available", "results": []}


@register_tool("search.history")
async def search_chat_history(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Search through chat history.

    Inputs:
        query: Search query
        thread_id: Thread to search (optional, uses current thread)
        max_results: Maximum results (default: 10)

    Returns:
        results: List of matching chat turns
    """
    query = str(inputs.get("query", "")).strip()
    thread_id = inputs.get("thread_id") or context.thread_id
    max_results = int(inputs.get("max_results", 10))

    if not query:
        return {"success": False, "error": "query is required", "results": []}

    if context.pathway_executor:
        try:
            from stdlib.perception.vector_memory import retrieve_memory_context

            scope = f"chat:{thread_id}" if thread_id else "chat:default"

            context_text, hits = await retrieve_memory_context(
                pathway_vm=context.pathway_executor,
                scope=scope,
                query=query,
                k=max_results,
                policy_kwargs=None,
            )

            results = []
            for hit in hits:
                results.append(
                    {
                        "id": hit.get("id"),
                        "text": hit.get("text", ""),
                        "score": round(hit.get("score", 0), 4),
                    }
                )

            return {
                "success": True,
                "query": query,
                "thread_id": thread_id,
                "results": results,
                "total_matches": len(results),
            }
        except Exception as e:
            logger.warning("Chat history search failed: %s", e)
            return {"success": False, "error": str(e), "results": []}

    return {"success": False, "error": "pathway executor not available", "results": []}


@register_tool("search.similar")
async def find_similar(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Find items similar to a given document or pathway.

    Inputs:
        doc_id: Document ID to find similar items for
        max_results: Maximum results (default: 5)

    Returns:
        results: List of similar items
    """
    doc_id = str(inputs.get("doc_id", "")).strip()
    max_results = int(inputs.get("max_results", 5))

    if not doc_id:
        return {"success": False, "error": "doc_id is required", "results": []}

    if context.domain:
        try:
            content = context.domain.get_head_content(doc_id=doc_id)

            # Build a query from the content
            if isinstance(content, dict):
                query_parts = []
                if content.get("name"):
                    query_parts.append(str(content.get("name")))
                if content.get("description"):
                    query_parts.append(str(content.get("description")))
                if content.get("nodes"):
                    node_types = [
                        str(n.get("type", ""))
                        for n in content.get("nodes", [])
                        if isinstance(n, dict)
                    ]
                    if node_types:
                        query_parts.append(" ".join(set(node_types)))
                query = " ".join(query_parts)
            else:
                query = str(content)[:500]

            if not query.strip():
                return {
                    "success": False,
                    "error": "document has no content to compare",
                    "results": [],
                }

            result = await semantic_search(
                {
                    "query": query,
                    "scope": "workspace",
                    "max_results": max_results + 1,
                },
                context,
            )

            if not result.get("success"):
                return result

            results = [r for r in result.get("results", []) if r.get("id") != doc_id][
                :max_results
            ]

            return {
                "success": True,
                "doc_id": doc_id,
                "results": results,
                "total_matches": len(results),
            }
        except Exception as e:
            logger.warning("Find similar failed: %s", e)
            return {"success": False, "error": str(e), "results": []}

    return {"success": False, "error": "domain not available", "results": []}
