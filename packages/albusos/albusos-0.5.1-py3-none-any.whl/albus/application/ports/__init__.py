"""Albus application ports - Service interfaces.

Ports define contracts between layers:
- RuntimePort: What transport sees
- ThreadRepositoryPort: Thread storage abstraction
"""

# Transport-facing port
from albus.application.ports.runtime_port import RuntimePort

# Repository ports
from albus.application.ports.thread_repository import ThreadRepositoryPort

# Re-export storage ports from persistence for convenience
from persistence.application.ports import (
    NullThreadStore,
    NullWorldStore,
    ThreadStorePort,
    WorldStorePort,
)

__all__ = [
    # Transport-facing
    "RuntimePort",
    # Repositories
    "ThreadRepositoryPort",
    # Storage (from persistence)
    "WorldStorePort",
    "NullWorldStore",
    "ThreadStorePort",
    "NullThreadStore",
]
