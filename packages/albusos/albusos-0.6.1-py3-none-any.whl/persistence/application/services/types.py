from __future__ import annotations

from typing import Any, Protocol

from persistence.domain.contracts.studio import (
    StudioDocument,
    StudioFolder,
    StudioProject,
    StudioRevision,
    StudioWorkspace,
)
from persistence.infrastructure.storage.store import StudioStore


class StudioDomainCtx(Protocol):
    """Typing contract for mixins in this package (internal)."""

    _store: StudioStore

    # Model helpers
    def _workspace_model(self, ws: dict[str, Any]) -> StudioWorkspace: ...
    def _folder_model(self, folder: dict[str, Any]) -> StudioFolder: ...
    def _document_model(self, doc: dict[str, Any]) -> StudioDocument: ...
    def _revision_model(self, rev: dict[str, Any]) -> StudioRevision: ...
    def _project_model(self, project: dict[str, Any]) -> StudioProject: ...

    # Invariants
    def _assert_non_empty_name(self, name: str) -> str: ...
    def _assert_workspace_exists(self, workspace_id: str) -> StudioWorkspace: ...
    def _assert_parent_folder(
        self, *, workspace_id: str, parent_id: str | None
    ) -> None: ...
    def _assert_unique_name(
        self,
        *,
        workspace_id: str,
        parent_id: str | None,
        kind: str,
        name: str,
        exclude_id: str | None = None,
    ) -> None: ...
    def _folder_parent_chain(
        self, *, workspace_id: str, folder_id: str
    ) -> list[str]: ...

    # Project helpers
    def _pick_project_pointers(
        self, *, workspace_id: str, folder_id: str
    ) -> dict[str, str | None]: ...
    def _ensure_project_seed_docs(
        self, *, workspace_id: str, folder_id: str
    ) -> None: ...


__all__ = ["StudioDomainCtx"]
