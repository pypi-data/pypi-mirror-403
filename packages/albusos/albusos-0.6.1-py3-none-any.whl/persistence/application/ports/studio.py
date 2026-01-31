"""Studio ports.

These Protocols define the host-facing surface of Studio OS without requiring
callers to import implementation types.
"""

from __future__ import annotations

from typing import Any, Protocol

from persistence.domain.contracts.studio import (
    StudioApplyPatchResult,
    StudioDocument,
    StudioPatch,
    StudioProject,
    StudioRunEvent,
    StudioRunSummary,
    StudioWorkspaceTree,
)


class StudioDomainPort(Protocol):
    """Minimal stable interface of StudioDomainService used by transports."""

    def get_document(self, *, doc_id: str) -> StudioDocument: ...

    def get_head_content(self, *, doc_id: str) -> Any: ...

    def get_revision_content(self, *, doc_id: str, rev_id: str) -> Any: ...

    def apply_patch(
        self,
        *,
        doc_id: str,
        base_rev: str | None,
        patch: StudioPatch,
        client_patch_id: str | None,
    ) -> StudioApplyPatchResult: ...

    def get_tree(self, *, workspace_id: str) -> StudioWorkspaceTree: ...

    # Projects (strict)
    def create_project(
        self, *, workspace_id: str, name: str, metadata: dict[str, Any] | None = None
    ) -> StudioProject: ...

    def list_projects(self, *, workspace_id: str) -> list[StudioProject]: ...

    def get_project(self, *, project_id: str) -> StudioProject: ...

    # Runs (append-only event logs)
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

    # Agent instances (state machine lifecycle)
    def save_agent_instance(
        self,
        *,
        agent_id: str,
        state_machine_id: str,
        workspace_id: str | None = None,
        instance: dict[str, Any],
    ) -> None: ...

    def get_agent_instance(self, agent_id: str) -> dict[str, Any] | None: ...

    def update_agent_state(
        self,
        *,
        agent_id: str,
        current_state: str,
        context: dict[str, Any],
    ) -> None: ...

    def delete_agent_instance(self, agent_id: str) -> bool: ...
