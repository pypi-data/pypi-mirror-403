"""persistence.contracts - Studio boundary DTOs.

This package contains all the data transfer objects for the Studio layer:
- StudioDocument, StudioWorkspace, StudioProject, StudioFolder
- StudioPatch, StudioRevision
- StudioRunEvent, StudioRunSummary
- Tree structures for workspace navigation
"""

from __future__ import annotations

from persistence.domain.contracts.studio import (
    DocType,
    RunStatus,
    StudioApplyPatchResult,
    StudioDocument,
    StudioFolder,
    StudioPatch,
    StudioPathwayGraphOp,
    StudioPathwayGraphOpsPatch,
    StudioProject,
    StudioRevision,
    StudioRunEvent,
    StudioRunSummary,
    StudioSnapshotPatch,
    StudioTreeChildren,
    StudioTreeDocumentNode,
    StudioTreeFolderNode,
    StudioWorkspace,
    StudioWorkspaceTree,
)

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
    "StudioRunEvent",
    "StudioRunSummary",
]
