from __future__ import annotations

from persistence.application.services.doc_crud import StudioDomainDocCrudMixin
from persistence.application.services.folder_crud import StudioDomainFolderCrudMixin
from persistence.application.services.invariants import StudioDomainInvariantsMixin
from persistence.application.services.node_mutations import (
    StudioDomainNodeMutationsMixin,
)
from persistence.application.services.project_crud import StudioDomainProjectCrudMixin
from persistence.application.services.queries import StudioDomainQuerySurfacesMixin
from persistence.application.services.run_events_crud import (
    StudioDomainRunEventsCrudMixin,
)
from persistence.application.services.workspace_crud import (
    StudioDomainWorkspaceCrudMixin,
)
from persistence.infrastructure.storage.store import StudioStore


class StudioDomainService(
    StudioDomainInvariantsMixin,
    StudioDomainWorkspaceCrudMixin,
    StudioDomainProjectCrudMixin,
    StudioDomainFolderCrudMixin,
    StudioDomainDocCrudMixin,
    StudioDomainQuerySurfacesMixin,
    StudioDomainNodeMutationsMixin,
    StudioDomainRunEventsCrudMixin,
):
    def __init__(self, *, store: StudioStore):
        self._store = store


__all__ = ["StudioDomainService"]
