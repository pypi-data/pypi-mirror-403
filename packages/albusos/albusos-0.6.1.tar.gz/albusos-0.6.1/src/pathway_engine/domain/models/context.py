"""Context models - context bundles, budgets, and evidence receipts.

These contracts define how context is compiled and tracked:
- Budgets for truncation (chars, items per section)
- Receipts for evidence provenance
- Bundles for compiled context output
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContextBudgetV1(BaseModel):
    """Hard budgets for context compilation (deterministic truncation rules)."""

    model_config = {"extra": "forbid"}

    max_chars_total: int = 6000
    max_chars_per_section: dict[str, int] = Field(
        default_factory=lambda: {
            "policy": 800,
            "chat_history": 900,
            "run_reports": 1400,
            "recipes": 1400,
            "ledger_hints": 800,
            "attachments": 1200,
            "flow": 1200,
        }
    )
    max_items_per_section: dict[str, int] = Field(
        default_factory=lambda: {
            "chat_history": 6,
            "run_reports": 3,
            "recipes": 3,
            "ledger_hints": 10,
            "attachments": 10,
            "flow": 6,
        }
    )


class ContextReceiptV1(BaseModel):
    """One 'Used Evidence' receipt entry."""

    model_config = {"extra": "forbid"}

    scope: str
    source_type: str
    source_id: str
    title: str
    excerpt: str | None = None
    digest: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContextSourceRefV1(BaseModel):
    """A stable reference to a context source candidate (V1)."""

    model_config = {"extra": "forbid"}

    scope: str
    source_type: str
    source_id: str
    title: str | None = None
    digest: str | None = None


class ContextBundleV1(BaseModel):
    """Compiled context bundle (V1)."""

    model_config = {"extra": "forbid"}

    bundle_id: str
    scope: str
    budgets: ContextBudgetV1 = Field(default_factory=ContextBudgetV1)
    sections: dict[str, Any] = Field(default_factory=dict)
    used_evidence: list[ContextReceiptV1] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    "ContextBudgetV1",
    "ContextReceiptV1",
    "ContextSourceRefV1",
    "ContextBundleV1",
]
