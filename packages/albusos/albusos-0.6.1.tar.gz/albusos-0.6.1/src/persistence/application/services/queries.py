from __future__ import annotations

from typing import Any

from persistence.domain.contracts.studio import (
    StudioProject,
    StudioWorkspace,
    StudioWorkspaceTree,
)
from persistence.domain.errors import StudioNotFound
from persistence.domain.tree import get_tree as _get_tree


class StudioDomainQuerySurfacesMixin:
    """Read/query surfaces for Studio domain."""

    # -------------------------
    # Workspaces
    # -------------------------
    def list_workspaces(self) -> list[StudioWorkspace]:
        return [self._workspace_model(x) for x in self._store.list_workspaces()]  # type: ignore[attr-defined]

    # -------------------------
    # Projects (strict)
    # -------------------------
    def get_project(self, *, project_id: str) -> StudioProject:
        proj = self._store.get_project(project_id)  # type: ignore[attr-defined]
        if not proj:
            raise StudioNotFound(f"project not found: {project_id}")
        return self._project_model(proj)

    def list_projects(self, *, workspace_id: str) -> list[StudioProject]:
        self._assert_workspace_exists(workspace_id)
        return [self._project_model(x) for x in self._store.list_projects(workspace_id=workspace_id)]  # type: ignore[attr-defined]

    # -------------------------
    # Folders
    # -------------------------
    def list_children(
        self, *, workspace_id: str, parent_id: str | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        folders = self._store.list_folders(workspace_id=workspace_id, parent_id=parent_id)  # type: ignore[attr-defined]
        docs = self._store.list_documents(workspace_id=workspace_id, parent_id=parent_id)  # type: ignore[attr-defined]
        return {"folders": folders, "documents": docs}

    # -------------------------
    # Tree (nested)
    # -------------------------
    def get_tree(self, *, workspace_id: str) -> StudioWorkspaceTree:
        return _get_tree(svc=self, workspace_id=workspace_id)


__all__ = ["StudioDomainQuerySurfacesMixin"]
