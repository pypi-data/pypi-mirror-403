"""persistence - Workspace and storage.

Simplified for local Electron app. File-based storage only.

Components:
- db/storage/: File-based document persistence
- db/services/: Domain operations
- db/domain/: Domain logic

For application initialization, use gateway.http.app.create_application()
"""

from __future__ import annotations

# No lazy exports / no compatibility shims.
# Import directly from:
# - persistence.application.services.service import StudioDomainService
# - persistence.infrastructure.storage.store import StudioStore

__all__: list[str] = []
