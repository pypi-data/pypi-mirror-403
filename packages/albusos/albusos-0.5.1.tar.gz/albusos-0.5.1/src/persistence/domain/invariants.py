from __future__ import annotations

from typing import Any

from persistence.domain.contracts.studio import (
    StudioDocument,
    StudioFolder,
    StudioProject,
    StudioRevision,
    StudioWorkspace,
)
from persistence.domain.errors import (
    StudioConflict,
    StudioNotFound,
    StudioValidationError,
)
from persistence.infrastructure.storage.store import StudioStore


def assert_non_empty_name(name: str) -> str:
    n = str(name).strip()
    if not n:
        raise StudioValidationError("name must be non-empty")
    return n


def workspace_model(ws: dict[str, Any]) -> StudioWorkspace:
    try:
        return StudioWorkspace.model_validate(ws)
    except Exception as e:
        raise StudioValidationError(f"invalid workspace record: {e}")


def project_model(project: dict[str, Any]) -> StudioProject:
    try:
        return StudioProject.model_validate(project)
    except Exception as e:
        raise StudioValidationError(f"invalid project record: {e}")


def folder_model(folder: dict[str, Any]) -> StudioFolder:
    try:
        return StudioFolder.model_validate(folder)
    except Exception as e:
        raise StudioValidationError(f"invalid folder record: {e}")


def document_model(doc: dict[str, Any]) -> StudioDocument:
    try:
        return StudioDocument.model_validate(doc)
    except Exception as e:
        raise StudioValidationError(f"invalid document record: {e}")


def revision_model(rev: dict[str, Any]) -> StudioRevision:
    try:
        return StudioRevision.model_validate(rev)
    except Exception as e:
        raise StudioValidationError(f"invalid revision record: {e}")


def assert_workspace_exists(store: StudioStore, workspace_id: str) -> StudioWorkspace:
    ws = store.get_workspace(workspace_id)
    if not ws:
        raise StudioNotFound(f"workspace not found: {workspace_id}")
    return workspace_model(ws)


def assert_parent_folder(
    *, store: StudioStore, workspace_id: str, parent_id: str | None
) -> None:
    if parent_id is None:
        return
    parent = store.get_folder(parent_id)
    if not parent:
        raise StudioNotFound(f"parent folder not found: {parent_id}")
    if str(parent.get("workspace_id") or "") != workspace_id:
        raise StudioValidationError("parent folder workspace mismatch")


def assert_unique_name(
    *,
    store: StudioStore,
    workspace_id: str,
    parent_id: str | None,
    kind: str,
    name: str,
    exclude_id: str | None = None,
) -> None:
    """Enforce unique names among siblings (folders vs folders, documents vs documents)."""
    n = assert_non_empty_name(name)
    if kind == "folder":
        siblings = store.list_folders(workspace_id=workspace_id, parent_id=parent_id)
        for s in siblings:
            if exclude_id and str(s.get("id")) == exclude_id:
                continue
            if str(s.get("name") or "") == n:
                raise StudioConflict("name already exists in folder")
        return
    if kind == "document":
        siblings = store.list_documents(workspace_id=workspace_id, parent_id=parent_id)
        for s in siblings:
            if exclude_id and str(s.get("id")) == exclude_id:
                continue
            if str(s.get("name") or "") == n:
                raise StudioConflict("name already exists in folder")
        return
    raise StudioValidationError(f"unknown kind: {kind}")


def folder_parent_chain(
    *, store: StudioStore, workspace_id: str, folder_id: str
) -> list[str]:
    """Return ancestor folder ids up to root (excluding the folder itself)."""
    out: list[str] = []
    current = store.get_folder(folder_id)
    if not current:
        raise StudioNotFound(f"folder not found: {folder_id}")
    if str(current.get("workspace_id") or "") != workspace_id:
        raise StudioValidationError("folder workspace mismatch")
    parent = current.get("parent_id")
    seen: set[str] = set()
    while parent is not None:
        pid = str(parent)
        if pid in seen:
            raise StudioValidationError("folder cycle detected (corrupt state)")
        seen.add(pid)
        out.append(pid)
        p = store.get_folder(pid)
        if not p:
            break
        if str(p.get("workspace_id") or "") != workspace_id:
            raise StudioValidationError("folder workspace mismatch")
        parent = p.get("parent_id")
    return out
