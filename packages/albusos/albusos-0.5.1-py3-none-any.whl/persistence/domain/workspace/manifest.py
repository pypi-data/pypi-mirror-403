"""Project manifest artifact contracts (core).

Goal:
- Provide a first-class, typed "spacetime" artifact that ties together the project's
  canonical system docs (Graph) and its evolving narrative.

Storage (v1):
- Studio ARTIFACT document with `metadata.kind="project_manifest"`
- Content is a versioned JSON object:
  { "format": "project_manifest_v1", "spec": { ... } }

We also accept (for text-editor compatibility):
- { "text": "<json>" } where the JSON parses to the same object shape above.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceReality(BaseModel):
    """The bounded reality of the workspace.

    This defines the "Laws of Physics" for the agent's world:
    - ground_truth: Read-only files that constitute facts.
    - laws: Pathways that MUST be used for verification.
    """

    model_config = ConfigDict(extra="forbid")

    ground_truth: list[str] = Field(
        default_factory=list,
        description="Files that represent absolute truth (e.g., evidence.csv)",
    )
    laws: list[str] = Field(
        default_factory=list, description="Pathways that MUST be used for verification"
    )


class ProjectPointersV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_doc_id: str | None = None


class ProjectManifestSpecV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str | None = None
    name: str | None = None

    # The Laws of Physics for this workspace
    reality: WorkspaceReality = Field(default_factory=WorkspaceReality)

    # Canonical system docs (pointers)
    pointers: ProjectPointersV1 = Field(default_factory=ProjectPointersV1)

    # Lightweight evolution fields (kept intentionally generic for v1)
    goal: str = ""
    constraints: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    notes: str = ""


class ProjectManifestDocV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["project_manifest_v1"] = "project_manifest_v1"
    spec: ProjectManifestSpecV1 = Field(default_factory=ProjectManifestSpecV1)


def safe_parse_project_manifest_doc(content: Any) -> ProjectManifestDocV1 | None:
    """Best-effort parse from common Studio content shapes."""
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        try:
            parsed = json.loads(content.get("text") or "")
        except Exception:
            parsed = None
        content = parsed
    if not isinstance(content, dict):
        return None
    try:
        return ProjectManifestDocV1.model_validate(content)
    except Exception:
        return None


__all__ = [
    "ProjectManifestDocV1",
    "ProjectManifestSpecV1",
    "ProjectPointersV1",
    "WorkspaceReality",
    "safe_parse_project_manifest_doc",
]
