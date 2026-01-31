"""Run summaries + append-only run event log CRUD mixin for StudioDomainService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from persistence.domain.contracts.studio import StudioRunEvent, StudioRunSummary

if TYPE_CHECKING:
    from persistence.application.services.types import StudioDomainCtx


class StudioDomainRunEventsCrudMixin:
    """Run log CRUD surface.

    Expects `self._store` implementing `StudioStore` (see `persistence.storage.store`).
    """

    def upsert_run_summary(
        self: "StudioDomainCtx", *, summary: StudioRunSummary
    ) -> StudioRunSummary:
        return self._store.upsert_run_summary(summary=summary)  # type: ignore[attr-defined]

    def get_run_summary(
        self: "StudioDomainCtx", *, run_id: str
    ) -> StudioRunSummary | None:
        return self._store.get_run_summary(run_id=str(run_id))  # type: ignore[attr-defined]

    def list_run_summaries(
        self: "StudioDomainCtx",
        *,
        workspace_id: str | None = None,
        doc_id: str | None = None,
        limit: int = 50,
    ) -> list[StudioRunSummary]:
        return self._store.list_run_summaries(  # type: ignore[attr-defined]
            workspace_id=str(workspace_id) if workspace_id else None,
            doc_id=str(doc_id) if doc_id else None,
            limit=int(limit),
        )

    def append_run_event(
        self: "StudioDomainCtx", *, event: StudioRunEvent
    ) -> StudioRunEvent:
        return self._store.append_run_event(event=event)  # type: ignore[attr-defined]

    def list_run_events(
        self: "StudioDomainCtx",
        *,
        run_id: str,
        after_seq: int | None = None,
        limit: int = 500,
    ) -> list[StudioRunEvent]:
        return self._store.list_run_events(  # type: ignore[attr-defined]
            run_id=str(run_id),
            after_seq=int(after_seq) if after_seq is not None else None,
            limit=int(limit),
        )


__all__ = ["StudioDomainRunEventsCrudMixin"]
