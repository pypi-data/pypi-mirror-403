"""persistence.ports - Studio interface definitions.

This package contains port interfaces for the Studio layer:
- StudioDomainPort - main studio operations
- StudioStorePort - persistence operations
"""

from __future__ import annotations

from persistence.application.ports.studio import StudioDomainPort
from persistence.application.ports.studio_store import StudioStorePort

__all__ = [
    "StudioDomainPort",
    "StudioStorePort",
]
