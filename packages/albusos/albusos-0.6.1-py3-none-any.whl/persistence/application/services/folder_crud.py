from __future__ import annotations

import uuid
from typing import Any

from persistence.domain.contracts.studio import StudioFolder
from persistence.application.services.types import StudioDomainCtx


class StudioDomainFolderCrudMixin:
    # -------------------------
    # Folders
    # -------------------------
    def create_folder(
        self: StudioDomainCtx,
        *,
        workspace_id: str,
        name: str,
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StudioFolder:
        self._assert_workspace_exists(workspace_id)
        parent_id = self._normalize_parent_id(
            workspace_id=str(workspace_id), parent_id=parent_id
        )
        self._assert_parent_folder(workspace_id=workspace_id, parent_id=parent_id)
        self._assert_unique_name(
            workspace_id=workspace_id, parent_id=parent_id, kind="folder", name=name
        )
        folder_id = f"fld_{uuid.uuid4().hex[:12]}"
        meta = dict(metadata or {})
        project_id: str | None = None
        try:
            if parent_id is not None:
                parent = self._store.get_folder(str(parent_id))
                if parent and str(parent.get("workspace_id") or "") == workspace_id:
                    pid = str(parent.get("project_id") or "").strip()
                    project_id = pid or None
        except Exception:
            project_id = None
        folder = self._store.upsert_folder(
            {
                "id": folder_id,
                "workspace_id": workspace_id,
                "project_id": project_id,
                "name": str(name).strip(),
                "parent_id": parent_id,
                "metadata": meta,
            }
        )
        return self._folder_model(folder)


__all__ = ["StudioDomainFolderCrudMixin"]
