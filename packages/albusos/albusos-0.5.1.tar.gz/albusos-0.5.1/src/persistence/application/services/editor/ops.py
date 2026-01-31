"""Graph Edit Operation Nodes - Pure transform nodes for pathway editing.

Each operation is a transform node that takes pathway content + operation spec
and returns modified pathway content. These are the "verbs" of graph editing.

Operations:
- add_node_op: Add a new node
- remove_node_op: Remove a node (and its connections)  
- rename_node_op: Rename a node ID
- connect_op: Add a connection
- disconnect_op: Remove a connection
- update_node_op: Update node properties
- update_prompt_op: Update node prompt

All operations are pure transforms: (content, op) -> content
They compose naturally in pathways.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpResult:
    """Result of a single graph operation."""

    ok: bool
    content: dict[str, Any]
    issue: str | None = None
    question: str | None = None


def _connection_key(w: dict[str, Any]) -> tuple[str, str, str, str]:
    """Unique key for a connection."""
    return (
        str(w.get("from") or "").strip(),
        str(w.get("to") or "").strip(),
        str(w.get("from_output") or "output").strip() or "output",
        str(w.get("to_input") or "input").strip() or "input",
    )


def _default_from_output_for_node_type(node_type: str) -> str:
    """Heuristic defaults for connection `from_output`.

    Many node builders return structured outputs (e.g. LLM → {"response": ...}).
    These defaults make "connect a → b" behave intuitively.
    """
    t = str(node_type or "").strip().lower()
    if t in ("llm", "tool_calling_llm", "operator", "vision"):
        return "response"
    if t in ("transform",):
        return "data"
    if t in ("select",):
        return "value"
    if t in ("code", "python"):
        return "result"
    if t in ("memory_read",):
        return "value"
    if t in ("tool", "tool_node", "tool_batch"):
        return "output"
    return "output"


def _get_node_index(nodes: list[dict], node_id: str) -> int | None:
    """Find index of node with given ID."""
    for i, n in enumerate(nodes):
        if isinstance(n, dict) and str(n.get("id") or "").strip() == node_id:
            return i
    return None


def _deep_merge(base: Any, patch: Any) -> Any:
    """Deep-merge dicts; patch wins. Lists are replaced (not merged)."""
    if isinstance(base, dict) and isinstance(patch, dict):
        out = dict(base)
        for k, v in patch.items():
            if k in out:
                out[k] = _deep_merge(out.get(k), v)
            else:
                out[k] = v
        return out
    return patch


# =============================================================================
# OPERATION NODES
# =============================================================================


def add_node_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Add a new node to the pathway.

    Op spec:
        {"op": "add_node", "node": {...}, "after": "node_id", "before": "node_id"}
    """
    nodes = list(content.get("nodes") or [])
    connections = list(content.get("connections") or [])

    node = op.get("node") or op.get("step")  # Support both
    if not isinstance(node, dict):
        return OpResult(ok=False, content=content, issue="add_node_missing_node")

    nid = str(node.get("id") or "").strip()
    ntype = str(node.get("type") or "").strip()

    if not nid:
        return OpResult(
            ok=False,
            content=content,
            issue="add_node_missing_id",
            question="What id should the new node have?",
        )

    if not ntype:
        return OpResult(
            ok=False,
            content=content,
            issue=f"add_node_missing_type:{nid}",
            question=f"What type should node '{nid}' be (e.g. llm/transform/router)?",
        )

    # Check for duplicate
    existing_idx = _get_node_index(nodes, nid)
    if existing_idx is not None:
        return OpResult(
            ok=False,
            content=content,
            issue=f"duplicate_node_id:{nid}",
            question=f"Node id '{nid}' already exists. Rename the new node or choose a different id?",
        )

    # Determine insert position
    insert_after = str(op.get("after") or "").strip() or None
    insert_before = str(op.get("before") or "").strip() or None

    insert_idx = len(nodes)
    if insert_before:
        idx = _get_node_index(nodes, insert_before)
        if idx is not None:
            insert_idx = idx
    elif insert_after:
        idx = _get_node_index(nodes, insert_after)
        if idx is not None:
            insert_idx = idx + 1

    nodes.insert(insert_idx, dict(node))

    return OpResult(
        ok=True, content={**content, "nodes": nodes, "connections": connections}
    )


def remove_node_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Remove a node and all its connections.

    Op spec:
        {"op": "remove_node", "id": "node_id"}
    """
    nodes = list(content.get("nodes") or [])
    connections = list(content.get("connections") or [])

    nid = str(op.get("id") or "").strip()
    if not nid:
        return OpResult(ok=False, content=content, issue="remove_node_missing_id")

    idx = _get_node_index(nodes, nid)
    if idx is None:
        return OpResult(ok=False, content=content, issue=f"remove_node_unknown:{nid}")

    nodes.pop(idx)

    # Remove connections involving this node
    connections = [
        w
        for w in connections
        if str(w.get("from") or "").strip() != nid
        and str(w.get("to") or "").strip() != nid
    ]

    return OpResult(
        ok=True, content={**content, "nodes": nodes, "connections": connections}
    )


def rename_node_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Rename a node ID, updating all references.

    Op spec:
        {"op": "rename_node", "from": "old_id", "to": "new_id"}
    """
    nodes = list(content.get("nodes") or [])
    connections = list(content.get("connections") or [])

    old_id = str(op.get("from") or "").strip()
    new_id = str(op.get("to") or "").strip()

    if not old_id or not new_id:
        return OpResult(
            ok=False, content=content, issue="rename_node_missing_from_or_to"
        )

    old_idx = _get_node_index(nodes, old_id)
    if old_idx is None:
        return OpResult(
            ok=False, content=content, issue=f"rename_node_unknown:{old_id}"
        )

    new_idx = _get_node_index(nodes, new_id)
    if new_idx is not None:
        return OpResult(
            ok=False, content=content, issue=f"rename_node_target_exists:{new_id}"
        )

    # Update node ID
    nodes[old_idx] = {**nodes[old_idx], "id": new_id}

    # Update connection references
    for w in connections:
        if str(w.get("from") or "").strip() == old_id:
            w["from"] = new_id
        if str(w.get("to") or "").strip() == old_id:
            w["to"] = new_id

    return OpResult(
        ok=True, content={**content, "nodes": nodes, "connections": connections}
    )


def connect_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Add a connection between nodes.

    Op spec:
        {"op": "connect", "from": "node_id", "to": "node_id",
         "from_output": "output", "to_input": "input"}
    """
    nodes = list(content.get("nodes") or [])
    connections = list(content.get("connections") or [])

    frm = str(op.get("from") or "").strip()
    to = str(op.get("to") or "").strip()

    if not frm or not to:
        return OpResult(ok=False, content=content, issue="connect_missing_from_or_to")

    # Verify nodes exist
    frm_idx = _get_node_index(nodes, frm)
    if frm_idx is None:
        return OpResult(
            ok=False,
            content=content,
            issue=f"connect_from_unknown_node:{frm}",
            question=f"I can't find node '{frm}'. Should I create it, or did you mean a different id?",
        )

    to_idx = _get_node_index(nodes, to)
    if to_idx is None:
        return OpResult(
            ok=False,
            content=content,
            issue=f"connect_to_unknown_node:{to}",
            question=f"I can't find node '{to}'. Should I create it, or did you mean a different id?",
        )

    # Determine from_output
    if op.get("from_output") is not None:
        from_out = str(op.get("from_output") or "output").strip() or "output"
    else:
        src_type = str(nodes[frm_idx].get("type") or "").strip()
        from_out = _default_from_output_for_node_type(src_type)

    to_in = str(op.get("to_input") or "input").strip() or "input"

    new_conn = {"from": frm, "to": to, "from_output": from_out, "to_input": to_in}

    # Check for duplicates
    key = _connection_key(new_conn)
    existing = {_connection_key(w) for w in connections}
    if key not in existing:
        connections.append(new_conn)

    return OpResult(
        ok=True, content={**content, "nodes": nodes, "connections": connections}
    )


def disconnect_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Remove a connection between nodes.

    Op spec:
        {"op": "disconnect", "from": "node_id", "to": "node_id",
         "from_output": "output", "to_input": "input"}
    """
    nodes = list(content.get("nodes") or [])
    connections = list(content.get("connections") or [])

    frm = str(op.get("from") or "").strip()
    to = str(op.get("to") or "").strip()

    if not frm or not to:
        return OpResult(
            ok=False, content=content, issue="disconnect_missing_from_or_to"
        )

    from_out = str(op.get("from_output") or "").strip() or None
    to_in = str(op.get("to_input") or "").strip() or None

    new_conns: list[dict[str, Any]] = []
    for w in connections:
        w_frm = str(w.get("from") or "").strip()
        w_to = str(w.get("to") or "").strip()

        if w_frm != frm or w_to != to:
            new_conns.append(w)
            continue

        if from_out and str(w.get("from_output") or "output").strip() != from_out:
            new_conns.append(w)
            continue

        if to_in and str(w.get("to_input") or "input").strip() != to_in:
            new_conns.append(w)
            continue

        # Match found - skip (i.e. remove)

    return OpResult(
        ok=True, content={**content, "nodes": nodes, "connections": new_conns}
    )


def update_node_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Update node properties via deep merge.

    Op spec:
        {"op": "update_node", "id": "node_id", "patch": {...}}
    """
    nodes = list(content.get("nodes") or [])
    connections = list(content.get("connections") or [])

    nid = str(op.get("id") or "").strip()
    patch = op.get("patch")

    if not nid:
        return OpResult(ok=False, content=content, issue="update_node_missing_id")

    idx = _get_node_index(nodes, nid)
    if idx is None:
        return OpResult(
            ok=False,
            content=content,
            issue=f"update_node_unknown:{nid}",
            question=f"I can't find node '{nid}' to update. Which node should I modify?",
        )

    if not isinstance(patch, dict):
        return OpResult(
            ok=False, content=content, issue=f"update_node_missing_patch:{nid}"
        )

    nodes[idx] = _deep_merge(nodes[idx], patch)

    return OpResult(
        ok=True, content={**content, "nodes": nodes, "connections": connections}
    )


def update_prompt_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Update a node's prompt (convenience for LLM nodes).

    Op spec:
        {"op": "update_prompt", "id": "node_id", "prompt": "new prompt"}
    """
    nodes = list(content.get("nodes") or [])
    connections = list(content.get("connections") or [])

    nid = str(op.get("id") or "").strip()
    prompt = op.get("prompt")

    if not nid:
        return OpResult(ok=False, content=content, issue="update_prompt_missing_id")

    idx = _get_node_index(nodes, nid)
    if idx is None:
        return OpResult(
            ok=False,
            content=content,
            issue=f"update_prompt_unknown_node:{nid}",
            question=f"I can't find node '{nid}' to update its prompt. Which node should I modify?",
        )

    if not isinstance(prompt, str):
        return OpResult(
            ok=False, content=content, issue=f"update_prompt_missing_prompt:{nid}"
        )

    cur = nodes[idx]
    cfg = cur.get("config") if isinstance(cur.get("config"), dict) else {}
    cfg2 = dict(cfg)
    cfg2["prompt"] = str(prompt)
    cur2 = dict(cur)
    cur2["config"] = cfg2
    nodes[idx] = cur2

    return OpResult(
        ok=True, content={**content, "nodes": nodes, "connections": connections}
    )


# =============================================================================
# OPERATION DISPATCH
# =============================================================================

OP_DISPATCH: dict[str, Any] = {
    "add_node": add_node_op,
    "remove_node": remove_node_op,
    "rename_node": rename_node_op,
    "connect": connect_op,
    "disconnect": disconnect_op,
    "update_node": update_node_op,
    "update_prompt": update_prompt_op,
}


def dispatch_op(content: dict[str, Any], op: dict[str, Any]) -> OpResult:
    """Dispatch a single operation to its handler."""
    if not isinstance(op, dict):
        return OpResult(ok=False, content=content, issue="op_not_an_object")

    op_name = str(op.get("op") or "").strip()
    if not op_name:
        return OpResult(ok=False, content=content, issue="op_missing_op")

    handler = OP_DISPATCH.get(op_name)
    if handler is None:
        return OpResult(ok=False, content=content, issue=f"unsupported_op:{op_name}")

    return handler(content, op)


__all__ = [
    "OpResult",
    "add_node_op",
    "remove_node_op",
    "rename_node_op",
    "connect_op",
    "disconnect_op",
    "update_node_op",
    "update_prompt_op",
    "dispatch_op",
    "OP_DISPATCH",
]
