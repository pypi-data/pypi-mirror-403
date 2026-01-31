from __future__ import annotations

import uuid
from typing import Any

from persistence.domain.contracts.studio import StudioProject
from persistence.application.services.types import StudioDomainCtx


class StudioDomainProjectCrudMixin:
    # -------------------------
    # Projects (strict)
    # -------------------------
    def create_project(
        self: StudioDomainCtx,
        *,
        workspace_id: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> StudioProject:
        self._assert_workspace_exists(workspace_id)
        # Root folder name uniqueness keeps UX simple; later we can decouple folder and project naming.
        self._assert_unique_name(
            workspace_id=workspace_id, parent_id=None, kind="folder", name=name
        )

        project_id = f"prj_{uuid.uuid4().hex[:12]}"
        folder_id = f"fld_{uuid.uuid4().hex[:12]}"
        folder_meta = {"kind": "project", **dict(metadata or {})}

        self._store.upsert_folder(
            {
                "id": folder_id,
                "workspace_id": workspace_id,
                "project_id": project_id,
                "name": self._assert_non_empty_name(name),
                "parent_id": None,
                "metadata": folder_meta,
            }
        )

        # Seed required docs (will inherit project_id via parent folder).
        try:
            self._ensure_project_seed_docs(
                workspace_id=workspace_id, folder_id=folder_id
            )
        except Exception:
            pass

        pointers = self._pick_project_pointers(
            workspace_id=workspace_id, folder_id=folder_id
        )
        proj = self._store.upsert_project(
            {
                "id": project_id,
                "workspace_id": workspace_id,
                "name": self._assert_non_empty_name(name),
                "root_folder_id": folder_id,
                **pointers,
                "metadata": dict(metadata or {}),
            }
        )
        return self._project_model(proj)


__all__ = ["StudioDomainProjectCrudMixin"]
