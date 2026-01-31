"""Policy Profile DTOs.

These are JSON-safe document types for defining tool policies and governance rules.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyProfileSpecV1(BaseModel):
    """Specification for a policy profile."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(default="Policy Profile")
    description: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Tool policy
    tool_policy: dict[str, Any] = Field(default_factory=dict)

    # LLM policy
    llm_policy: dict[str, Any] = Field(default_factory=dict)


class PolicyProfileDocV1(BaseModel):
    """Document wrapper for policy profile spec."""

    model_config = ConfigDict(extra="allow")

    format: str = "policy_profile.v1"
    spec: PolicyProfileSpecV1 = Field(default_factory=PolicyProfileSpecV1)


def safe_parse_policy_profile_doc(
    content: dict[str, Any] | Any
) -> PolicyProfileDocV1 | None:
    """Parse policy profile document content, returning None on failure."""
    if not isinstance(content, dict):
        return None
    try:
        return PolicyProfileDocV1.model_validate(content)
    except Exception:
        return None


__all__ = [
    "PolicyProfileDocV1",
    "PolicyProfileSpecV1",
    "safe_parse_policy_profile_doc",
]
