from __future__ import annotations

import uuid
from typing import Any, Protocol

from persistence.domain.contracts.studio import DocType


class _ProjectSeedServiceLike(Protocol):
    """Narrow protocol so helpers can be tested/mocked easily."""

    _store: Any

    def create_document(
        self,
        *,
        doc_type: str,
        name: str,
        parent_id: str | None = None,
        workspace_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any: ...


def ensure_project_seed_docs(
    *, svc: _ProjectSeedServiceLike, workspace_id: str, folder_id: str
) -> None:
    """Ensure a Project folder contains required system docs (best-effort, idempotent).

    Strict contract:
    - This is only invoked by `create_project` (not on reads).
    - No folder kind coercion or repair-on-read behavior.
    """
    docs = svc._store.list_documents(workspace_id=workspace_id, parent_id=folder_id)
    has_whiteboard = any(
        str(d.get("type") or "") in (DocType.WHITEBOARD.value, DocType.CANVAS.value)
        for d in docs
    )
    has_flow = any(str(d.get("type") or "") == DocType.FLOW.value for d in docs)
    has_manifest = any(
        str(d.get("type") or "") == DocType.TEXT.value
        and str(
            (d.get("metadata") if isinstance(d.get("metadata"), dict) else {}).get(
                "kind"
            )
            or ""
        )
        == "project_manifest"
        for d in docs
        if isinstance(d, dict)
    )

    # Fast path: if required docs exist, we're done.
    if has_whiteboard and has_flow and has_manifest:
        return

    existing_names = {str(d.get("name") or "").strip() for d in docs}

    def pick_name(base: str) -> str:
        b = base.strip() or "Untitled"
        if b not in existing_names:
            existing_names.add(b)
            return b
        for i in range(2, 50):
            cand = f"{b} {i}"
            if cand not in existing_names:
                existing_names.add(cand)
                return cand
        cand = f"{b} {uuid.uuid4().hex[:6]}"
        existing_names.add(cand)
        return cand

    if not has_whiteboard:
        try:
            svc.create_document(
                doc_type=DocType.WHITEBOARD.value,
                name=pick_name("Whiteboard"),
                workspace_id=workspace_id,
                parent_id=folder_id,
                metadata={"role": "primary_whiteboard"},
            )
        except Exception:
            pass
    if not has_flow:
        try:
            svc.create_document(
                doc_type=DocType.FLOW.value,
                name=pick_name("Graph"),
                workspace_id=workspace_id,
                parent_id=folder_id,
                metadata={"role": "primary_graph"},
            )
        except Exception:
            pass
    if not has_manifest:
        try:
            svc.create_document(
                doc_type=DocType.ARTIFACT.value,
                name=pick_name("Project Manifest"),
                workspace_id=workspace_id,
                parent_id=folder_id,
                metadata={
                    "kind": "project_manifest",
                    "role": "system_project_manifest",
                },
            )
        except Exception:
            pass


__all__ = ["ensure_project_seed_docs"]
