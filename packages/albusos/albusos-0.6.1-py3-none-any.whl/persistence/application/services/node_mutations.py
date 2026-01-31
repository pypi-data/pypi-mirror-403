from __future__ import annotations

from typing import Any

from persistence.application.services.types import StudioDomainCtx
from persistence.domain.errors import StudioNotFound, StudioValidationError


class StudioDomainNodeMutationsMixin:
    # -------------------------
    # Nodes (rename/move)
    # -------------------------
    def rename_node(
        self: StudioDomainCtx, *, kind: str, id: str, name: str
    ) -> dict[str, Any]:
        if kind == "folder":
            existing = self._store.get_folder(id)
            if not existing:
                raise StudioNotFound(f"folder not found: {id}")
            ws_id = str(existing.get("workspace_id") or "")
            parent_id = existing.get("parent_id")
            self._assert_unique_name(
                workspace_id=ws_id,
                parent_id=str(parent_id) if parent_id is not None else None,
                kind="folder",
                name=name,
                exclude_id=id,
            )
            out = self._store.upsert_folder(
                {**existing, "name": self._assert_non_empty_name(name)}
            )
            return self._folder_model(out)

        if kind == "document":
            existing = self._store.get_document(id)
            if not existing:
                raise StudioNotFound(f"document not found: {id}")
            ws_id = str(existing.get("workspace_id") or "")
            parent_id = existing.get("parent_id")
            self._assert_unique_name(
                workspace_id=ws_id,
                parent_id=str(parent_id) if parent_id is not None else None,
                kind="document",
                name=name,
                exclude_id=id,
            )
            out = self._store.upsert_document(
                {**existing, "name": self._assert_non_empty_name(name)}
            )
            return self._document_model(out)

        raise StudioValidationError("kind must be 'folder' or 'document'")

    def move_node(
        self: StudioDomainCtx, *, kind: str, id: str, new_parent_id: str | None
    ) -> dict[str, Any]:
        if kind == "folder":
            existing = self._store.get_folder(id)
            if not existing:
                raise StudioNotFound(f"folder not found: {id}")
            ws_id = str(existing.get("workspace_id") or "")
            new_parent_id = self._normalize_parent_id(
                workspace_id=ws_id, parent_id=new_parent_id
            )
            self._assert_parent_folder(workspace_id=ws_id, parent_id=new_parent_id)

            if new_parent_id is not None:
                if str(new_parent_id) == str(id):
                    raise StudioValidationError("cannot move folder into itself")
                parent_chain = self._folder_parent_chain(
                    workspace_id=ws_id, folder_id=str(new_parent_id)
                )
                if str(id) in parent_chain:
                    raise StudioValidationError(
                        "cannot move folder into its descendant"
                    )

            self._assert_unique_name(
                workspace_id=ws_id,
                parent_id=new_parent_id,
                kind="folder",
                name=str(existing.get("name") or ""),
                exclude_id=id,
            )
            out = self._store.upsert_folder({**existing, "parent_id": new_parent_id})
            return self._folder_model(out)

        if kind == "document":
            existing = self._store.get_document(id)
            if not existing:
                raise StudioNotFound(f"document not found: {id}")
            ws_id = str(existing.get("workspace_id") or "")
            new_parent_id = self._normalize_parent_id(
                workspace_id=ws_id, parent_id=new_parent_id
            )
            self._assert_parent_folder(workspace_id=ws_id, parent_id=new_parent_id)
            self._assert_unique_name(
                workspace_id=ws_id,
                parent_id=new_parent_id,
                kind="document",
                name=str(existing.get("name") or ""),
                exclude_id=id,
            )
            out = self._store.upsert_document({**existing, "parent_id": new_parent_id})
            return self._document_model(out)

        raise StudioValidationError("kind must be 'folder' or 'document'")


__all__ = ["StudioDomainNodeMutationsMixin"]
