"""Studio asset store (binary blobs).

Phase 0 implementation:
- Filesystem-backed blobs under the same root as the Studio file store
- Workspace-scoped layout

This intentionally stores *bytes* only. Metadata lives in Studio documents/revisions.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _safe_segment(s: str) -> str:
    return str(s).replace("/", "_").replace("\\", "_").replace(":", "_")


@dataclass(frozen=True)
class FileStudioAssetStoreConfig:
    root: str = "./data/studio"


class FileStudioAssetStore:
    """Filesystem-backed blob store for Studio assets."""

    def __init__(self, config: FileStudioAssetStoreConfig | None = None):
        self._cfg = config or FileStudioAssetStoreConfig()
        self._root = Path(self._cfg.root)

    def _ws_assets_dir(self, workspace_id: str) -> Path:
        return self._root / "workspaces" / _safe_segment(workspace_id) / "assets"

    def asset_path(self, *, workspace_id: str, asset_id: str) -> Path:
        # Single-file per asset id. Filename/original extension is carried in metadata.
        return self._ws_assets_dir(workspace_id) / _safe_segment(asset_id)

    def exists(self, *, workspace_id: str, asset_id: str) -> bool:
        return self.asset_path(workspace_id=workspace_id, asset_id=asset_id).exists()

    def write_bytes(self, *, workspace_id: str, asset_id: str, data: bytes) -> Path:
        target = self.asset_path(workspace_id=workspace_id, asset_id=asset_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Atomic swap (best-effort) to avoid partial writes.
        with tempfile.NamedTemporaryFile(
            "wb",
            delete=False,
            dir=str(target.parent),
            prefix=target.name,
            suffix=".tmp",
        ) as f:
            f.write(data)
            tmp = f.name
        os.replace(tmp, str(target))
        return target
