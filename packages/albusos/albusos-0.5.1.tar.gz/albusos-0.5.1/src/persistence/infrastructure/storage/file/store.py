"""File-backed Studio store (dev-first)."""

from __future__ import annotations

from typing import Any, Optional

from persistence.domain.contracts.studio import StudioRunEvent, StudioRunSummary
from persistence.infrastructure.storage.file import (
    documents,
    folders,
    patches,
    projects,
    revisions,
    run_events,
    threads,
    workspaces,
)
from persistence.infrastructure.storage.file.state import (
    FileStoreState,
    FileStudioStoreConfig,
)
from persistence.infrastructure.storage.store import StudioStore


class FileStudioStore(StudioStore):
    """A minimal file-backed store for documents + revisions + runs.

    Layout is managed by `persistence.storage.file.state.FileStoreState`.
    """

    def __init__(self, config: FileStudioStoreConfig | None = None):
        self._cfg = config or FileStudioStoreConfig()
        self._state = FileStoreState.from_config(self._cfg)

    # -------------------------
    # Documents
    # -------------------------
    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]:
        with self._state.lock:
            return documents.get_document(self._state, doc_id)

    def upsert_document(self, doc: dict[str, Any]) -> dict[str, Any]:
        with self._state.lock:
            return documents.upsert_document(self._state, doc)

    def list_documents(
        self,
        *,
        workspace_id: str | None = None,
        parent_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        with self._state.lock:
            return documents.list_documents(
                self._state,
                workspace_id=workspace_id,
                parent_id=parent_id,
                include_deleted=include_deleted,
            )

    def list_all_documents(
        self, *, workspace_id: str, include_deleted: bool = False
    ) -> list[dict[str, Any]]:
        with self._state.lock:
            return documents.list_all_documents(
                self._state, workspace_id=workspace_id, include_deleted=include_deleted
            )

    # -------------------------
    # Workspaces
    # -------------------------
    def get_workspace(self, workspace_id: str) -> Optional[dict[str, Any]]:
        with self._state.lock:
            return workspaces.get_workspace(self._state, workspace_id)

    def upsert_workspace(self, ws: dict[str, Any]) -> dict[str, Any]:
        with self._state.lock:
            return workspaces.upsert_workspace(self._state, ws)

    def list_workspaces(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        with self._state.lock:
            return workspaces.list_workspaces(
                self._state, include_deleted=include_deleted
            )

    # -------------------------
    # Projects
    # -------------------------
    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        with self._state.lock:
            return projects.get_project(self._state, project_id)

    def upsert_project(self, project: dict[str, Any]) -> dict[str, Any]:
        with self._state.lock:
            return projects.upsert_project(self._state, project)

    def list_projects(
        self, *, workspace_id: str, include_deleted: bool = False
    ) -> list[dict[str, Any]]:
        with self._state.lock:
            return projects.list_projects(
                self._state, workspace_id=workspace_id, include_deleted=include_deleted
            )

    # -------------------------
    # Folders
    # -------------------------
    def get_folder(self, folder_id: str) -> Optional[dict[str, Any]]:
        with self._state.lock:
            return folders.get_folder(self._state, folder_id)

    def upsert_folder(self, folder: dict[str, Any]) -> dict[str, Any]:
        with self._state.lock:
            return folders.upsert_folder(self._state, folder)

    def list_folders(
        self,
        *,
        workspace_id: str,
        parent_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        with self._state.lock:
            return folders.list_folders(
                self._state,
                workspace_id=workspace_id,
                parent_id=parent_id,
                include_deleted=include_deleted,
            )

    def list_all_folders(
        self, *, workspace_id: str, include_deleted: bool = False
    ) -> list[dict[str, Any]]:
        with self._state.lock:
            return folders.list_all_folders(
                self._state, workspace_id=workspace_id, include_deleted=include_deleted
            )

    # -------------------------
    # Revisions
    # -------------------------
    def write_revision(
        self, *, doc_id: str, rev_id: str, content: dict[str, Any]
    ) -> dict[str, Any]:
        with self._state.lock:
            doc = documents.get_document(self._state, doc_id) or {"id": doc_id}
            return revisions.write_revision(
                self._state, doc=doc, doc_id=doc_id, rev_id=rev_id, content=content
            )

    def get_revision(self, *, doc_id: str, rev_id: str) -> Optional[dict[str, Any]]:
        with self._state.lock:
            doc = documents.get_document(self._state, doc_id) or {"id": doc_id}
            return revisions.get_revision(
                self._state, doc=doc, doc_id=doc_id, rev_id=rev_id
            )

    # -------------------------
    # Patch idempotency + atomic commit
    # -------------------------
    def get_patch_idempotency(
        self, *, doc_id: str, client_patch_id: str
    ) -> Optional[dict[str, Any]]:
        with self._state.lock:
            doc = documents.get_document(self._state, doc_id)
            if not doc:
                return None
            return patches.get_patch_idempotency(
                self._state, doc=doc, doc_id=doc_id, client_patch_id=client_patch_id
            )

    def put_patch_idempotency(
        self, *, doc_id: str, client_patch_id: str, record: dict[str, Any]
    ) -> dict[str, Any]:
        with self._state.lock:
            doc = documents.get_document(self._state, doc_id) or {"id": doc_id}
            return patches.put_patch_idempotency(
                self._state,
                doc=doc,
                doc_id=doc_id,
                client_patch_id=client_patch_id,
                record=record,
            )

    def commit_patch(
        self,
        *,
        doc_id: str,
        expected_head_rev: str | None,
        base_rev: str | None,
        new_rev: str,
        content: dict[str, Any],
        client_patch_id: str | None,
    ) -> dict[str, Any]:
        with self._state.lock:
            doc = documents.get_document(self._state, doc_id)
            if not doc:
                raise ValueError(f"document not found: {doc_id}")
            return patches.commit_patch(
                self._state,
                doc=doc,
                doc_id=doc_id,
                expected_head_rev=expected_head_rev,
                base_rev=base_rev,
                new_rev=new_rev,
                content=content,
                client_patch_id=client_patch_id,
            )

    # -------------------------
    # Runs
    # -------------------------
    def upsert_run_summary(self, *, summary: StudioRunSummary) -> StudioRunSummary:
        with self._state.lock:
            return run_events.upsert_run_summary(self._state, summary=summary)

    def get_run_summary(self, *, run_id: str) -> StudioRunSummary | None:
        with self._state.lock:
            return run_events.get_run_summary(self._state, run_id=run_id)

    def list_run_summaries(
        self,
        *,
        workspace_id: str | None = None,
        doc_id: str | None = None,
        limit: int = 50,
    ) -> list[StudioRunSummary]:
        with self._state.lock:
            return run_events.list_run_summaries(
                self._state, workspace_id=workspace_id, doc_id=doc_id, limit=limit
            )

    def append_run_event(self, *, event: StudioRunEvent) -> StudioRunEvent:
        with self._state.lock:
            return run_events.append_run_event(self._state, event=event)

    def list_run_events(
        self, *, run_id: str, after_seq: int | None = None, limit: int = 500
    ) -> list[StudioRunEvent]:
        with self._state.lock:
            return run_events.list_run_events(
                self._state, run_id=run_id, after_seq=after_seq, limit=limit
            )

    # -------------------------
    # Threads (conversation persistence)
    # -------------------------
    def save_thread(self, thread_id: str, data: dict[str, Any]) -> None:
        """Save or update a thread."""
        with self._state.lock:
            threads.save_thread(self._state, thread_id, data)

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        """Load a thread by ID."""
        with self._state.lock:
            return threads.get_thread(self._state, thread_id)

    def list_threads(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List threads, optionally filtered by workspace."""
        with self._state.lock:
            return threads.list_threads(
                self._state, workspace_id=workspace_id, limit=limit, offset=offset
            )

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread."""
        with self._state.lock:
            return threads.delete_thread(self._state, thread_id)

    def count_threads(self, *, workspace_id: str | None = None) -> int:
        """Count threads, optionally filtered by workspace."""
        with self._state.lock:
            return threads.count_threads(self._state, workspace_id=workspace_id)


__all__ = ["FileStudioStore", "FileStudioStoreConfig"]
