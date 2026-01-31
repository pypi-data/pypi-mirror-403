"""Shared state/path helpers for the file-backed Studio store."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from persistence.infrastructure.storage.file.io import safe_segment


@dataclass(frozen=True)
class FileStudioStoreConfig:
    root: str = "./data/studio"


@dataclass(frozen=True)
class FileStoreState:
    root: Path
    docs: Path
    projects: Path
    workspaces: Path
    folders: Path
    revs: Path
    threads: Path
    idempotency: Path
    runs: Path
    lock: threading.RLock

    @classmethod
    def from_config(cls, config: FileStudioStoreConfig) -> "FileStoreState":
        root = Path(config.root)
        state = cls(
            root=root,
            docs=root / "documents",
            projects=root / "projects",
            workspaces=root / "workspaces",
            folders=root / "folders",
            revs=root / "revisions",
            threads=root / "threads",
            idempotency=root / "idempotency",
            runs=root / "runs",
            lock=threading.RLock(),
        )
        for p in (
            state.docs,
            state.projects,
            state.workspaces,
            state.folders,
            state.revs,
            state.threads,
            state.idempotency,
            state.runs,
        ):
            p.mkdir(parents=True, exist_ok=True)
        return state

    def ws_dir(self, workspace_id: str) -> Path:
        return self.workspaces / safe_segment(workspace_id)

    def ws_docs_dir(self, workspace_id: str) -> Path:
        return self.ws_dir(workspace_id) / "documents"

    def ws_folders_dir(self, workspace_id: str) -> Path:
        return self.ws_dir(workspace_id) / "folders"

    def ws_projects_dir(self, workspace_id: str) -> Path:
        return self.ws_dir(workspace_id) / "projects"

    def ws_revs_dir(self, workspace_id: str) -> Path:
        return self.ws_dir(workspace_id) / "revisions"

    def ws_idempotency_dir(self, workspace_id: str) -> Path:
        return self.ws_dir(workspace_id) / "idempotency"

    def ws_runs_dir(self, workspace_id: str) -> Path:
        return self.ws_dir(workspace_id) / "runs"


__all__ = ["FileStudioStoreConfig", "FileStoreState"]
