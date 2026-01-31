"""Pathway Graph Editor - Pathway-canonical graph editing.

This module provides graph editing operations expressed AS pathways.
The editor that edits pathways IS ITSELF a pathway.

Architecture:
    ops.py          - Pure transform functions for each operation
    __init__.py     - Pathway builders and high-level interface

Operations:
- add_node: Add a new node
- remove_node: Remove a node (and its connections)
- rename_node: Rename a node ID
- connect: Add a connection
- disconnect: Remove a connection
- update_node: Update node properties
- update_prompt: Update node prompt

This is part of the pathway language - these are the "verbs" for editing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def validate_pathway_struct(content: dict) -> tuple[bool, list[str]]:
    """Validate pathway structure (nodes and connections).

    Returns (ok, issues) where issues are stable codes.
    """
    issues: list[str] = []

    if not isinstance(content, dict):
        return False, ["not_an_object"]

    nodes_raw = content.get("nodes")
    connections_raw = content.get("connections")

    if nodes_raw is None and connections_raw is None:
        return True, []  # Empty pathway is valid

    if nodes_raw is None:
        return False, ["nodes_required_when_connections_present"]
    if not isinstance(nodes_raw, list):
        return False, ["nodes_not_a_list"]

    node_ids: set[str] = set()
    for s in nodes_raw[:500]:
        if not isinstance(s, dict):
            issues.append("node_not_an_object")
            continue
        sid = str(s.get("id") or "").strip()
        if not sid:
            issues.append("node_missing_id")
            continue
        if sid in node_ids:
            issues.append(f"duplicate_node_id:{sid}")
        node_ids.add(sid)
        stype = str(s.get("type") or "").strip()
        if not stype:
            issues.append(f"node_missing_type:{sid}")

    if connections_raw is None:
        return len(issues) == 0, issues
    if not isinstance(connections_raw, list):
        issues.append("connections_not_a_list")
        return False, issues

    for w in connections_raw[:2000]:
        if not isinstance(w, dict):
            issues.append("connection_not_an_object")
            continue
        frm = str(w.get("from", w.get("from_node", ""))).strip()
        to = str(w.get("to", w.get("to_node", ""))).strip()
        if not frm or not to:
            issues.append("connection_missing_from_or_to")
            continue
        if node_ids and frm not in node_ids:
            issues.append(f"connection_from_unknown_node:{frm}")
        if node_ids and to not in node_ids:
            issues.append(f"connection_to_unknown_node:{to}")

    return len(issues) == 0, issues


from persistence.application.services.editor.ops import (
    OpResult,
    dispatch_op,
    add_node_op,
    remove_node_op,
    rename_node_op,
    connect_op,
    disconnect_op,
    update_node_op,
    update_prompt_op,
)


def _dedupe_strs(xs: list[Any], *, limit: int | None = None) -> list[str]:
    """Deduplicate and clean strings."""
    out: list[str] = []
    for x in xs:
        s = str(x or "").strip()
        if not s or s in out:
            continue
        out.append(s)
        if limit is not None and len(out) >= int(limit):
            break
    return out


# =============================================================================
# PATHWAY BUILDER
# =============================================================================


# =============================================================================
# RESULT TYPE
# =============================================================================


@dataclass(frozen=True)
class PathwayEditResult:
    """Result of a pathway edit operation."""

    ok: bool
    content: dict[str, Any]
    issues: list[str]
    questions: list[str]


# =============================================================================
# HIGH-LEVEL INTERFACE
# =============================================================================


def apply_graph_ops(
    content: dict[str, Any], ops: list[dict[str, Any]]
) -> PathwayEditResult:
    """Apply graph ops to canonical pathway content.

    This is the synchronous interface for graph editing.
    For async usage, build and execute the pathway directly.

    Args:
        content: The pathway document (nodes + connections)
        ops: List of operations to apply

    Returns:
        PathwayEditResult with modified content and any issues
    """
    # Check for wrapped spec (not allowed)
    base = dict(content or {})
    if isinstance(base.get("spec"), dict):
        return PathwayEditResult(
            ok=False,
            content=base,
            issues=["pathway_spec_wrapper_not_allowed"],
            questions=[
                "Remove the top-level 'spec' wrapper and store nodes/connections at the root."
            ],
        )

    # Ensure nodes and connections are lists
    if not isinstance(base.get("nodes"), list):
        base["nodes"] = []
    if not isinstance(base.get("connections"), list):
        base["connections"] = []

    issues: list[str] = []
    questions: list[str] = []

    # Apply each operation
    for op in ops or []:
        result = dispatch_op(base, op)
        base = result.content
        if not result.ok:
            if result.issue:
                issues.append(result.issue)
            if result.question:
                questions.append(result.question)

    # Final validation
    ok, struct_issues = validate_pathway_struct(base)
    issues.extend(struct_issues)

    # Extra connectivity hints
    nodes = base.get("nodes") if isinstance(base.get("nodes"), list) else []
    connections = (
        base.get("connections") if isinstance(base.get("connections"), list) else []
    )

    if not nodes:
        issues.append("no_steps")

    node_ids = {
        str(s.get("id") or "").strip()
        for s in nodes
        if isinstance(s, dict) and str(s.get("id") or "").strip()
    }
    if len(node_ids) > 1 and len(connections) == 0:
        issues.append("multi_node_no_connections")

    # Generate questions
    if "no_steps" in issues:
        questions.append("What are the 3–8 concrete nodes you want in this Pathway?")
    if "multi_node_no_connections" in issues:
        questions.append(
            "How should those nodes connect (what outputs feed into what inputs)?"
        )
    if any(
        x.startswith("connection_from_unknown_node:")
        or x.startswith("connection_to_unknown_node:")
        for x in issues
    ):
        questions.append(
            "Should any node IDs be renamed so connections reference the right nodes?"
        )

    issues_out = _dedupe_strs(issues, limit=25)
    questions_out = _dedupe_strs(questions, limit=3)

    return PathwayEditResult(
        ok=len(issues_out) == 0,
        content=base,
        issues=issues_out,
        questions=questions_out,
    )


def validate_pathwaydoc_struct(pathway_doc: Any) -> tuple[bool, list[str], list[str]]:
    """Validate PathwayDoc structure.

    Returns: (ok, issues, questions)
    """
    if not isinstance(pathway_doc, dict):
        return (
            False,
            ["pathwaydoc_not_an_object"],
            ["What should the Pathway contain (3–8 nodes)?"],
        )

    ok, issues = validate_pathway_struct(pathway_doc)

    nodes = (
        pathway_doc.get("nodes") if isinstance(pathway_doc.get("nodes"), list) else []
    )
    connections = (
        pathway_doc.get("connections")
        if isinstance(pathway_doc.get("connections"), list)
        else []
    )

    if not nodes:
        issues.append("no_steps")

    node_ids = {
        str(s.get("id") or "").strip()
        for s in nodes
        if isinstance(s, dict) and str(s.get("id") or "").strip()
    }
    if len(node_ids) > 1 and len(connections) == 0:
        issues.append("multi_node_no_connections")

    questions: list[str] = []
    if "no_steps" in issues:
        questions.append("What are the 3–8 concrete nodes you want in this Pathway?")
    if "multi_node_no_connections" in issues:
        questions.append(
            "How should those nodes connect (what outputs feed into what inputs)?"
        )
    if any(
        x.startswith("connection_from_unknown_node:")
        or x.startswith("connection_to_unknown_node:")
        for x in issues
    ):
        questions.append(
            "Should any node IDs be renamed so connections reference the right nodes?"
        )

    ok = len(issues) == 0
    return ok, issues, _dedupe_strs(questions, limit=3)


__all__ = [
    # Result type
    "PathwayEditResult",
    # High-level interface
    "apply_graph_ops",
    "validate_pathwaydoc_struct",
    # Individual operations (for direct use or composition)
    "OpResult",
    "add_node_op",
    "remove_node_op",
    "rename_node_op",
    "connect_op",
    "disconnect_op",
    "update_node_op",
    "update_prompt_op",
    "dispatch_op",
]
