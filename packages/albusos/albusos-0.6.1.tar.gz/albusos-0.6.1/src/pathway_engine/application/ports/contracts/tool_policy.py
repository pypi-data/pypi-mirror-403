"""Tool policy contracts (engine-owned).

These DTOs define the *generic* interface between a host (like Albus) and the
execution substrate (Pathway Engine).

Key rule: `pathway_engine` must not import product code (`albus`). These are the
stable contracts that both layers can depend on.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolPolicyContext(BaseModel):
    """Ambient governance context carried through execution.

    Hosts set this (request-scoped); runtime/tool wrappers consume it for:
    - audit trails
    - tool gating / allowlists
    - execution approvals
    """

    model_config = ConfigDict(extra="forbid")

    origin: str = "unknown"
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None
    doc_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    actor_id: Optional[str] = None

    # Approval gating
    approved: bool = False
    approved_plan_id: Optional[str] = None

    # Optional policy profile
    policy_profile_doc_id: Optional[str] = None
    policy_profile_tool_allowlist: list[str] | None = None
    policy_profile_tool_denylist: list[str] | None = None

    # Freeform extra (best-effort plumbing; avoid breaking older callers)
    metadata: dict[str, Any] = Field(default_factory=dict)


ToolImpact = Literal["read", "mutate", "network", "execute"]


class ToolPolicyDecision(BaseModel):
    """Host classification decision for a tool call."""

    model_config = ConfigDict(extra="forbid")

    impact: ToolImpact
    requires_approval: bool
    reason: str


__all__ = [
    "ToolPolicyContext",
    "ToolImpact",
    "ToolPolicyDecision",
]
