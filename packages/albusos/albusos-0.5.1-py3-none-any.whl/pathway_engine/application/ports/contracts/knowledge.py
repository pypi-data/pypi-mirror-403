"""Workspace knowledge retrieval DTOs.

These contracts are used for prompt-time retrieval and host-owned indexing.
They are JSON-friendly and safe to use across boundaries.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceKnowledgeSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    k: int = 8
    filters: dict[str, Any] | None = None


class WorkspaceKnowledgeSnippet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str | None = None
    doc_name: str | None = None
    doc_type: str | None = None
    excerpt: str | None = None
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkspaceKnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    error: Optional[str] = None
    workspace_id: Optional[str] = None
    query: Optional[str] = None
    results: list[WorkspaceKnowledgeSnippet] = Field(default_factory=list)


__all__ = [
    "WorkspaceKnowledgeSearchRequest",
    "WorkspaceKnowledgeSearchResponse",
    "WorkspaceKnowledgeSnippet",
]
