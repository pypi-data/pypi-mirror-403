"""Storage interface for Studio OS (second-level contract).

StudioStore is the persistence seam. Implementations:
- `persistence.storage.file.store.FileStudioStore` (dev-first)
- `persistence.storage.postgres.store.PostgresStudioStore` (prod-ish)

This interface is intentionally "dumb":
- no validation logic
- no business invariants
- no runtime execution
"""

from __future__ import annotations

from typing import Any, Optional, Protocol

from persistence.domain.contracts.studio import StudioRunEvent, StudioRunSummary


class StudioStore(Protocol):
    # -------------------------
    # Documents
    # -------------------------
    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]: ...

    def upsert_document(self, doc: dict[str, Any]) -> dict[str, Any]: ...

    def list_documents(
        self,
        *,
        workspace_id: str | None = None,
        parent_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]: ...

    def list_all_documents(
        self, *, workspace_id: str, include_deleted: bool = False
    ) -> list[dict[str, Any]]: ...

    # -------------------------
    # Workspaces
    # -------------------------
    def get_workspace(self, workspace_id: str) -> Optional[dict[str, Any]]: ...

    def upsert_workspace(self, ws: dict[str, Any]) -> dict[str, Any]: ...

    def list_workspaces(
        self, *, include_deleted: bool = False
    ) -> list[dict[str, Any]]: ...

    # -------------------------
    # Projects (strict)
    # -------------------------
    def get_project(self, project_id: str) -> Optional[dict[str, Any]]: ...

    def upsert_project(self, project: dict[str, Any]) -> dict[str, Any]: ...

    def list_projects(
        self, *, workspace_id: str, include_deleted: bool = False
    ) -> list[dict[str, Any]]: ...

    # -------------------------
    # Folders
    # -------------------------
    def get_folder(self, folder_id: str) -> Optional[dict[str, Any]]: ...

    def upsert_folder(self, folder: dict[str, Any]) -> dict[str, Any]: ...

    def list_folders(
        self,
        *,
        workspace_id: str,
        parent_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]: ...

    def list_all_folders(
        self, *, workspace_id: str, include_deleted: bool = False
    ) -> list[dict[str, Any]]: ...

    # -------------------------
    # Revisions
    # -------------------------
    def write_revision(
        self, *, doc_id: str, rev_id: str, content: dict[str, Any]
    ) -> dict[str, Any]: ...

    def get_revision(self, *, doc_id: str, rev_id: str) -> Optional[dict[str, Any]]: ...

    # -------------------------
    # Patch idempotency + atomic commit
    # -------------------------
    def get_patch_idempotency(
        self, *, doc_id: str, client_patch_id: str
    ) -> Optional[dict[str, Any]]: ...

    def put_patch_idempotency(
        self, *, doc_id: str, client_patch_id: str, record: dict[str, Any]
    ) -> dict[str, Any]: ...

    def commit_patch(
        self,
        *,
        doc_id: str,
        expected_head_rev: str | None,
        base_rev: str | None,
        new_rev: str,
        content: dict[str, Any],
        client_patch_id: str | None,
    ) -> dict[str, Any]: ...

    # -------------------------
    # Runs (append-only event logs)
    # -------------------------
    def upsert_run_summary(self, *, summary: StudioRunSummary) -> StudioRunSummary: ...

    def get_run_summary(self, *, run_id: str) -> StudioRunSummary | None: ...

    def list_run_summaries(
        self,
        *,
        workspace_id: str | None = None,
        doc_id: str | None = None,
        limit: int = 50,
    ) -> list[StudioRunSummary]: ...

    def append_run_event(self, *, event: StudioRunEvent) -> StudioRunEvent: ...

    def list_run_events(
        self, *, run_id: str, after_seq: int | None = None, limit: int = 500
    ) -> list[StudioRunEvent]: ...

    # -------------------------
    # Threads (conversation persistence)
    # -------------------------
    def save_thread(self, thread_id: str, data: dict[str, Any]) -> None: ...

    def get_thread(self, thread_id: str) -> dict[str, Any] | None: ...

    def list_threads(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]: ...

    def delete_thread(self, thread_id: str) -> bool: ...

    def count_threads(self, *, workspace_id: str | None = None) -> int: ...


__all__ = ["StudioStore"]
