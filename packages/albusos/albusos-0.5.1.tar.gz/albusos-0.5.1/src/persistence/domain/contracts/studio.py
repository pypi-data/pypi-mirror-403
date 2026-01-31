"""Studio DTOs - canonical, JSON-friendly contracts.

These types define the stable shapes used across:
- Studio persistence backends
- Studio domain service
- Transports (REST/WS/JSON-RPC)
- Intelligence/controller proposals
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocType(str, Enum):
    PATHWAY = "pathway"
    AGENT = "agent"
    ARTIFACT = "artifact"
    TEXT = "text"
    ASSET = "asset"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StudioWorkspace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class StudioProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    name: str
    root_folder_id: str
    graph_doc_id: Optional[str] = None
    manifest_doc_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class StudioFolder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    project_id: Optional[str] = None
    name: str
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class StudioDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: DocType
    name: str
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    parent_id: Optional[str] = None
    head_rev: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class StudioRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    rev_id: str
    content: dict[str, Any]
    created_at: Optional[datetime] = None


class StudioTreeDocumentNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["document"] = "document"
    id: str
    name: str
    doc_type: DocType
    head_rev: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StudioTreeChildren(BaseModel):
    model_config = ConfigDict(extra="forbid")

    folders: list["StudioTreeFolderNode"] = Field(default_factory=list)
    documents: list[StudioTreeDocumentNode] = Field(default_factory=list)


class StudioTreeFolderNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["folder"] = "folder"
    id: str
    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    children: StudioTreeChildren


class StudioWorkspaceTree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace: StudioWorkspace
    tree: StudioTreeChildren


# ---------------------------------------------------------------------------
# Patch DTOs (blessed semantic patch path)
# ---------------------------------------------------------------------------


class StudioSnapshotPatch(BaseModel):
    """Replace the entire document content snapshot."""

    model_config = ConfigDict(extra="forbid")
    type: Literal["snapshot"] = "snapshot"
    content: dict[str, Any]


class StudioPathwayGraphOp(BaseModel):
    """One semantic graph op (pathway_engine.editor applies these deterministically)."""

    model_config = ConfigDict(extra="allow")
    op: str


class StudioPathwayGraphOpsPatch(BaseModel):
    """Apply semantic graph ops to a pathway document."""

    model_config = ConfigDict(extra="forbid")
    type: Literal["pathway_graph_ops"] = "pathway_graph_ops"
    ops: list[StudioPathwayGraphOp] = Field(default_factory=list)


StudioPatch = StudioSnapshotPatch | StudioPathwayGraphOpsPatch


class StudioApplyPatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    base_rev: Optional[str] = None
    new_rev: str
    head_rev: str
    content: dict[str, Any]


# ---------------------------------------------------------------------------
# Runs / execution logs
# ---------------------------------------------------------------------------


class StudioRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workspace_id: Optional[str] = None
    doc_id: Optional[str] = None
    status: RunStatus = RunStatus.PENDING
    started_at_ms: Optional[int] = None
    finished_at_ms: Optional[int] = None
    error: Optional[str] = None


class StudioRunEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    seq: int
    ts_ms: int
    type: str
    node_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "DocType",
    "RunStatus",
    "StudioWorkspace",
    "StudioProject",
    "StudioFolder",
    "StudioDocument",
    "StudioRevision",
    "StudioTreeDocumentNode",
    "StudioTreeFolderNode",
    "StudioTreeChildren",
    "StudioWorkspaceTree",
    "StudioPatch",
    "StudioSnapshotPatch",
    "StudioPathwayGraphOp",
    "StudioPathwayGraphOpsPatch",
    "StudioApplyPatchResult",
    "StudioRunSummary",
    "StudioRunEvent",
]
