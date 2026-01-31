"""Storage-level errors for StudioStore implementations.

These are *not* domain errors. Domain/services may translate these into
`StudioConflict` / `StudioValidationError` as appropriate.
"""

from __future__ import annotations


class StudioStoreConflict(Exception):
    """Raised when an atomic store operation detects a conflict (e.g. head_rev CAS)."""
