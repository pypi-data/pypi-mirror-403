from __future__ import annotations

import uuid
from typing import Any

from persistence.domain.contracts.studio import DocType, StudioDocument, StudioRevision
from persistence.domain.errors import StudioNotFound, StudioValidationError


class StudioDomainDocCrudMixin:
    """Document + revision CRUD.

    Expects invariants/model helpers from `StudioDomainInvariantsMixin` and `self._store`.
    """

    # -------------------------
    # Documents
    # -------------------------
    def create_document(
        self,
        *,
        doc_id: str | None = None,
        doc_type: str,
        name: str,
        parent_id: str | None = None,
        workspace_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> StudioDocument:
        # Validate type against universal DTOs
        try:
            dtype = DocType(str(doc_type))
        except Exception:
            raise StudioValidationError(
                "type must be 'pathway', 'agent', 'artifact', 'text', or 'asset'"
            )

        self._assert_workspace_exists(str(workspace_id))
        parent_id = self._normalize_parent_id(
            workspace_id=str(workspace_id), parent_id=parent_id
        )
        self._assert_parent_folder(workspace_id=str(workspace_id), parent_id=parent_id)

        project_id: str | None = None
        try:
            if parent_id is not None:
                parent = self._store.get_folder(str(parent_id))  # type: ignore[attr-defined]
                if parent and str(parent.get("workspace_id") or "") == str(
                    workspace_id
                ):
                    pid = str(parent.get("project_id") or "").strip()
                    project_id = pid or None
        except Exception:
            project_id = None

        if doc_id is not None:
            did = str(doc_id).strip()
            if not did:
                raise StudioValidationError(
                    "document.id must be non-empty when provided"
                )
            # Keep ids predictable and safe for file paths / URLs.
            if not did.startswith("doc_"):
                raise StudioValidationError("document.id must start with 'doc_'")
            # Idempotency: if the document already exists with the same attrs, treat as success.
            try:
                existing = self._store.get_document(did)  # type: ignore[attr-defined]
            except Exception:
                existing = None
            if existing:
                try:
                    if (
                        str(existing.get("id") or "") == did
                        and str(existing.get("workspace_id") or "") == str(workspace_id)
                        and str(existing.get("parent_id") or "") == str(parent_id or "")
                        and str(existing.get("type") or "") == str(dtype.value)
                        and str(existing.get("name") or "")
                        == self._assert_non_empty_name(name)
                        and (
                            existing.get("metadata")
                            if isinstance(existing.get("metadata"), dict)
                            else {}
                        )
                        == dict(metadata or {})
                    ):
                        return self._document_model(existing)
                except Exception:
                    # Fall through to conflict (fail-closed).
                    pass
                from persistence.domain.errors import StudioConflict  # noqa: PLC0415

                raise StudioConflict(
                    "document id already exists", doc_id=did, conflict_code="id_exists"
                )
            doc_id = did
        else:
            doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Name uniqueness is evaluated only for *new* documents.
        self._assert_unique_name(
            workspace_id=str(workspace_id),
            parent_id=parent_id,
            kind="document",
            name=name,
            exclude_id=None,
        )
        doc = {
            "id": doc_id,
            "type": dtype.value,
            "name": self._assert_non_empty_name(name),
            "parent_id": parent_id,
            "workspace_id": str(workspace_id),
            "project_id": project_id,
            "metadata": dict(metadata or {}),
            "head_rev": None,
        }
        out = self._store.upsert_document(doc)  # type: ignore[attr-defined]
        return self._document_model(out)

    def get_document(self, *, doc_id: str) -> StudioDocument:
        doc = self._store.get_document(doc_id)  # type: ignore[attr-defined]
        if not doc:
            raise StudioNotFound(f"document not found: {doc_id}")
        return self._document_model(doc)

    def save_revision(
        self, *, doc_id: str, content: dict[str, Any], rev_id: str | None = None
    ) -> StudioRevision:
        self.get_document(doc_id=doc_id)  # ensure exists
        rid = rev_id or f"rev_{uuid.uuid4().hex[:12]}"
        rev = self._store.write_revision(doc_id=doc_id, rev_id=rid, content=content)  # type: ignore[attr-defined]
        self._store.upsert_document({"id": doc_id, "head_rev": rid})  # type: ignore[attr-defined]
        return self._revision_model(rev)

    def _get_head_revision_id(self, *, doc_id: str) -> str | None:
        doc = self.get_document(doc_id=doc_id)
        return str(doc.head_rev) if doc.head_rev else None

    def _get_revision_content(self, *, doc_id: str, rev_id: str) -> dict[str, Any]:
        rev = self._store.get_revision(doc_id=doc_id, rev_id=str(rev_id))  # type: ignore[attr-defined]
        if not rev:
            raise StudioNotFound(f"revision not found: {rev_id}")
        content = rev.get("content")
        if not isinstance(content, dict):
            raise StudioValidationError("revision content is invalid")
        return content

    def get_revision_content(self, *, doc_id: str, rev_id: str) -> dict[str, Any]:
        """Return the content snapshot for a specific immutable revision."""
        return self._get_revision_content(doc_id=doc_id, rev_id=rev_id)

    def get_head_content(self, *, doc_id: str) -> dict[str, Any]:
        doc = self.get_document(doc_id=doc_id)
        head = doc.head_rev
        if not head:
            raise StudioNotFound(f"head revision not set for document: {doc_id}")
        rev = self._store.get_revision(doc_id=doc_id, rev_id=str(head))  # type: ignore[attr-defined]
        if not rev:
            raise StudioNotFound(f"revision not found: {head}")
        content = rev.get("content")
        if not isinstance(content, dict):
            raise StudioValidationError("revision content is invalid")
        return content


__all__ = ["StudioDomainDocCrudMixin"]
