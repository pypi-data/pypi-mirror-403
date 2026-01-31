"""Core contract-layer error types (no runtime/host deps)."""

from __future__ import annotations


class ValidationError(ValueError):
    """Raised when a contract/DTO validation fails."""


__all__ = ["ValidationError"]
