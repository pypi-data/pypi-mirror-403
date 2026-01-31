from __future__ import annotations

import logging
from typing import Any, Optional

from persistence.domain.contracts import (
    DocType,
    StudioTreeChildren,
    StudioTreeDocumentNode,
    StudioTreeFolderNode,
    StudioWorkspaceTree,
)

logger = logging.getLogger(__name__)


def get_tree(*, svc: object, workspace_id: str) -> StudioWorkspaceTree:
    """Build a workspace tree (folders + documents) for Studio UI.

    `svc` is expected to be `StudioDomainService`-shaped:
    - `_assert_workspace_exists`
    - `_store` with `list_folders`/`list_documents`
    """

    # Keep behavior identical to the previous inline implementation.
    ws = svc._assert_workspace_exists(workspace_id)  # type: ignore[attr-defined]

    def build(parent_id: Optional[str]) -> StudioTreeChildren:
        folder_nodes: list[StudioTreeFolderNode] = []
        children: dict[str, list[dict[str, Any]]] = svc.list_children(  # type: ignore[attr-defined]
            workspace_id=workspace_id, parent_id=parent_id
        )
        for f in children["folders"]:
            folder_nodes.append(
                StudioTreeFolderNode(
                    id=str(f.get("id")),
                    name=str(f.get("name") or ""),
                    metadata=dict(f.get("metadata") or {}),
                    children=build(str(f.get("id"))),
                )
            )
        doc_nodes: list[StudioTreeDocumentNode] = []
        for d in children["documents"]:
            raw_type = str(d.get("type") or "")
            dt = DocType(raw_type)
            md = dict(d.get("metadata") or {})
            doc_nodes.append(
                StudioTreeDocumentNode(
                    id=str(d.get("id")),
                    name=str(d.get("name") or ""),
                    doc_type=dt,
                    metadata=md,
                )
            )
        return StudioTreeChildren(folders=folder_nodes, documents=doc_nodes)

    return StudioWorkspaceTree(workspace=ws, tree=build(None))
