from __future__ import annotations

import uuid
from typing import Any

from persistence.domain.contracts.studio import StudioWorkspace
from persistence.application.services.types import StudioDomainCtx


class StudioDomainWorkspaceCrudMixin:
    # -------------------------
    # Workspaces
    # -------------------------
    def create_workspace(
        self: StudioDomainCtx, *, name: str, metadata: dict[str, Any] | None = None
    ) -> StudioWorkspace:
        ws_id = f"ws_{uuid.uuid4().hex[:12]}"
        n = self._assert_non_empty_name(name)
        ws = self._store.upsert_workspace(
            {"id": ws_id, "name": n, "metadata": dict(metadata or {})}
        )
        return self._workspace_model(ws)


__all__ = ["StudioDomainWorkspaceCrudMixin"]
