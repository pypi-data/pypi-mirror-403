from __future__ import annotations

from typing import Any

from persistence.domain.contracts import (
    DocType,
    StudioDocument,
    StudioFolder,
    StudioProject,
    StudioRevision,
    StudioWorkspace,
)
from persistence.domain.invariants import (
    assert_non_empty_name as _assert_non_empty_name,
)
from persistence.domain.invariants import (
    assert_parent_folder as _assert_parent_folder,
)
from persistence.domain.invariants import (
    assert_unique_name as _assert_unique_name,
)
from persistence.domain.invariants import (
    assert_workspace_exists as _assert_workspace_exists,
)
from persistence.domain.invariants import (
    document_model as _document_model,
)
from persistence.domain.invariants import (
    folder_model as _folder_model,
)
from persistence.domain.invariants import (
    folder_parent_chain as _folder_parent_chain,
)
from persistence.domain.invariants import (
    project_model as _project_model,
)
from persistence.domain.invariants import (
    revision_model as _revision_model,
)
from persistence.domain.invariants import (
    workspace_model as _workspace_model,
)
from persistence.domain.project_seed import (
    ensure_project_seed_docs as _ensure_project_seed_docs,
)


class StudioDomainInvariantsMixin:
    """Internal helpers + stable invariants.

    Expects `self._store` to be present (see `StudioDomainService`).
    """

    # -------------------------
    # Shared invariants
    # -------------------------
    def _assert_non_empty_name(self, name: str) -> str:
        return _assert_non_empty_name(name)

    def _workspace_model(self, ws: dict[str, Any]) -> StudioWorkspace:
        return _workspace_model(ws)

    def _folder_model(self, folder: dict[str, Any]) -> StudioFolder:
        return _folder_model(folder)

    def _document_model(self, doc: dict[str, Any]) -> StudioDocument:
        return _document_model(doc)

    def _revision_model(self, rev: dict[str, Any]) -> StudioRevision:
        return _revision_model(rev)

    def _project_model(self, project: dict[str, Any]) -> StudioProject:
        return _project_model(project)

    def _assert_workspace_exists(self, workspace_id: str) -> StudioWorkspace:
        return _assert_workspace_exists(self._store, workspace_id)  # type: ignore[attr-defined]

    def _normalize_parent_id(
        self, *, workspace_id: str, parent_id: str | None
    ) -> str | None:
        """Accept either a folder id or a project id as `parent_id`.

        Intelligence/orchestrators often scope by project id. Studio storage, however, uses
        folder ids as the actual parent container. If a project id is provided, resolve it
        to the project's root folder id.
        """
        pid = str(parent_id or "").strip() or None
        if pid is None:
            return None
        # Folder id fast-path.
        try:
            if self._store.get_folder(pid):  # type: ignore[attr-defined]
                return pid
        except Exception:
            pass
        # Project id -> root folder id.
        try:
            if pid.startswith("prj_"):
                prj = self._store.get_project(pid)  # type: ignore[attr-defined]
                if isinstance(prj, dict) and str(prj.get("workspace_id") or "") == str(
                    workspace_id
                ):
                    root = str(prj.get("root_folder_id") or "").strip() or None
                    if root:
                        return root
        except Exception:
            pass
        return pid

    def _assert_parent_folder(
        self, *, workspace_id: str, parent_id: str | None
    ) -> None:
        return _assert_parent_folder(  # type: ignore[return-value]
            store=self._store,  # type: ignore[attr-defined]
            workspace_id=workspace_id,
            parent_id=parent_id,
        )

    def _assert_unique_name(
        self,
        *,
        workspace_id: str,
        parent_id: str | None,
        kind: str,
        name: str,
        exclude_id: str | None = None,
    ) -> None:
        return _assert_unique_name(  # type: ignore[return-value]
            store=self._store,  # type: ignore[attr-defined]
            workspace_id=workspace_id,
            parent_id=parent_id,
            kind=kind,
            name=name,
            exclude_id=exclude_id,
        )

    def _folder_parent_chain(self, *, workspace_id: str, folder_id: str) -> list[str]:
        return _folder_parent_chain(  # type: ignore[return-value]
            store=self._store,  # type: ignore[attr-defined]
            workspace_id=workspace_id,
            folder_id=folder_id,
        )

    # -------------------------
    # Projects (strict) - shared helpers
    # -------------------------
    def _pick_project_pointers(
        self, *, workspace_id: str, folder_id: str
    ) -> dict[str, str | None]:
        docs = self._store.list_documents(  # type: ignore[attr-defined]
            workspace_id=workspace_id, parent_id=folder_id
        )

        def _meta(d: dict[str, Any]) -> dict[str, Any]:
            return (
                dict(d.get("metadata") or {})
                if isinstance(d.get("metadata"), dict)
                else {}
            )

        whiteboard_docs = [
            d
            for d in docs
            if str(d.get("type") or "")
            in (DocType.WHITEBOARD.value, DocType.CANVAS.value)
        ]
        pathway_docs = [
            d for d in docs if str(d.get("type") or "") == DocType.FLOW.value
        ]
        text_docs = [d for d in docs if str(d.get("type") or "") == DocType.TEXT.value]

        def _pick_by_role(items: list[dict[str, Any]], role: str) -> str | None:
            for d in sorted(items, key=lambda x: str(x.get("id") or "")):
                if str(_meta(d).get("role") or "").strip() == role:
                    return str(d.get("id") or "") or None
            return str(items[0].get("id") or "") if items else None

        whiteboard_doc_id = _pick_by_role(whiteboard_docs, "primary_whiteboard")
        graph_doc_id = _pick_by_role(pathway_docs, "primary_graph")
        manifest_doc_id = None
        for d in sorted(text_docs, key=lambda x: str(x.get("id") or "")):
            md = _meta(d)
            if str(md.get("kind") or "").strip() == "project_manifest":
                manifest_doc_id = str(d.get("id") or "") or None
                break

        return {
            "whiteboard_doc_id": whiteboard_doc_id,
            "graph_doc_id": graph_doc_id,
            "manifest_doc_id": manifest_doc_id,
        }

    def _ensure_project_seed_docs(self, *, workspace_id: str, folder_id: str) -> None:
        _ensure_project_seed_docs(
            svc=self, workspace_id=workspace_id, folder_id=folder_id
        )


__all__ = ["StudioDomainInvariantsMixin"]
