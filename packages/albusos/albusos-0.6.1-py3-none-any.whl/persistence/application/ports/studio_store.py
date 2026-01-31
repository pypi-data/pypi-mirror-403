"""Studio store ports.

These Protocols describe the minimal persistence/query surface the host needs for
tenancy guards and lightweight lookups without importing `persistence.storage.*`
types everywhere.

Note: `persistence` remains the owner of the actual storage implementations.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StudioStorePort(Protocol):
    """Minimal store interface used by host for tenancy + metadata lookups."""

    def get_document(self, doc_id: str) -> dict[str, Any] | None: ...

    def get_folder(self, folder_id: str) -> dict[str, Any] | None: ...
