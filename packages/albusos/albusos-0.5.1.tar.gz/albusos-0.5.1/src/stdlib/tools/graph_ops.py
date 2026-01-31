"""Graph Ops Tools - Albus can edit pathways programmatically.

These tools expose graph editing operations so Albus can:
- Build pathways step by step
- Modify existing pathways
- Wire up connections

This is how Albus becomes a "pathway builder" - it uses these tools
to construct graphs for users.
"""

from __future__ import annotations

import logging
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool
from persistence.application.services.editor.ops import (
    add_node_op,
    remove_node_op,
    rename_node_op,
    connect_op,
    disconnect_op,
    update_node_op,
    update_prompt_op,
    OpResult,
)

logger = logging.getLogger(__name__)


def _result_to_dict(result: OpResult, op_name: str) -> dict[str, Any]:
    """Convert OpResult to tool response."""
    return {
        "success": result.ok,
        "op": op_name,
        "content": result.content,
        "issue": result.issue,
        "question": result.question,
    }


@register_tool(
    "graph.add_node",
    description="Add a new node to a pathway",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Current pathway content (nodes + connections)",
            },
            "node": {
                "type": "object",
                "description": "Node definition: {id, type, name, config: {...}}",
            },
            "after": {
                "type": "string",
                "description": "Insert after this node ID (optional)",
            },
            "before": {
                "type": "string",
                "description": "Insert before this node ID (optional)",
            },
        },
        "required": ["content", "node"],
    },
)
async def graph_add_node(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Add a node to the pathway."""
    content = inputs.get("content", {"nodes": [], "connections": []})
    op = {
        "op": "add_node",
        "node": inputs.get("node", {}),
    }
    if inputs.get("after"):
        op["after"] = inputs["after"]
    if inputs.get("before"):
        op["before"] = inputs["before"]

    result = add_node_op(content, op)
    return _result_to_dict(result, "add_node")


@register_tool(
    "graph.remove_node",
    description="Remove a node from a pathway (also removes its connections)",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Current pathway content",
            },
            "node_id": {
                "type": "string",
                "description": "ID of node to remove",
            },
        },
        "required": ["content", "node_id"],
    },
)
async def graph_remove_node(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Remove a node from the pathway."""
    content = inputs.get("content", {"nodes": [], "connections": []})
    op = {"op": "remove_node", "id": inputs.get("node_id", "")}

    result = remove_node_op(content, op)
    return _result_to_dict(result, "remove_node")


@register_tool(
    "graph.rename_node",
    description="Rename a node ID (updates connections too)",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Current pathway content",
            },
            "old_id": {
                "type": "string",
                "description": "Current node ID",
            },
            "new_id": {
                "type": "string",
                "description": "New node ID",
            },
        },
        "required": ["content", "old_id", "new_id"],
    },
)
async def graph_rename_node(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Rename a node."""
    content = inputs.get("content", {"nodes": [], "connections": []})
    op = {
        "op": "rename_node",
        "from": inputs.get("old_id", ""),
        "to": inputs.get("new_id", ""),
    }

    result = rename_node_op(content, op)
    return _result_to_dict(result, "rename_node")


@register_tool(
    "graph.connect",
    description="Add a connection between two nodes",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Current pathway content",
            },
            "from_node": {
                "type": "string",
                "description": "Source node ID",
            },
            "to_node": {
                "type": "string",
                "description": "Target node ID",
            },
            "from_output": {
                "type": "string",
                "description": "Output port name (default: auto-detected)",
            },
            "to_input": {
                "type": "string",
                "description": "Input port name (default: 'input')",
            },
        },
        "required": ["content", "from_node", "to_node"],
    },
)
async def graph_connect(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Connect two nodes."""
    content = inputs.get("content", {"nodes": [], "connections": []})
    op = {
        "op": "connect",
        "from": inputs.get("from_node", ""),
        "to": inputs.get("to_node", ""),
    }
    if inputs.get("from_output"):
        op["from_output"] = inputs["from_output"]
    if inputs.get("to_input"):
        op["to_input"] = inputs["to_input"]

    result = connect_op(content, op)
    return _result_to_dict(result, "connect")


@register_tool(
    "graph.disconnect",
    description="Remove a connection between two nodes",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Current pathway content",
            },
            "from_node": {
                "type": "string",
                "description": "Source node ID",
            },
            "to_node": {
                "type": "string",
                "description": "Target node ID",
            },
        },
        "required": ["content", "from_node", "to_node"],
    },
)
async def graph_disconnect(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Remove a connection."""
    content = inputs.get("content", {"nodes": [], "connections": []})
    op = {
        "op": "disconnect",
        "from": inputs.get("from_node", ""),
        "to": inputs.get("to_node", ""),
    }

    result = disconnect_op(content, op)
    return _result_to_dict(result, "disconnect")


@register_tool(
    "graph.update_node",
    description="Update a node's properties",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Current pathway content",
            },
            "node_id": {
                "type": "string",
                "description": "Node ID to update",
            },
            "patch": {
                "type": "object",
                "description": "Properties to update (merged into existing node)",
            },
        },
        "required": ["content", "node_id", "patch"],
    },
)
async def graph_update_node(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Update node properties."""
    content = inputs.get("content", {"nodes": [], "connections": []})
    op = {
        "op": "update_node",
        "id": inputs.get("node_id", ""),
        "patch": inputs.get("patch", {}),
    }

    result = update_node_op(content, op)
    return _result_to_dict(result, "update_node")


@register_tool(
    "graph.update_prompt",
    description="Update an LLM node's prompt",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Current pathway content",
            },
            "node_id": {
                "type": "string",
                "description": "LLM node ID",
            },
            "prompt": {
                "type": "string",
                "description": "New prompt text",
            },
        },
        "required": ["content", "node_id", "prompt"],
    },
)
async def graph_update_prompt(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Update node prompt."""
    content = inputs.get("content", {"nodes": [], "connections": []})
    op = {
        "op": "update_prompt",
        "id": inputs.get("node_id", ""),
        "prompt": inputs.get("prompt", ""),
    }

    result = update_prompt_op(content, op)
    return _result_to_dict(result, "update_prompt")


__all__ = [
    "graph_add_node",
    "graph_remove_node",
    "graph_rename_node",
    "graph_connect",
    "graph_disconnect",
    "graph_update_node",
    "graph_update_prompt",
]
