from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VectorUpsertInput(BaseModel):
    """Input for vector memory upsert (chunk + embed + store)."""

    model_config = {"extra": "forbid"}

    scope: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_id: str | None = None
    chunk_max_chars: int = 1200
    chunk_overlap: int = 200
    embedding_provider: str | None = None
    embedding_model: str | None = None


class VectorUpsertOutput(BaseModel):
    """Output for vector memory upsert."""

    model_config = {"extra": "forbid"}

    chunks_added: int
    ids: list[str] = Field(default_factory=list)


class VectorSearchInput(BaseModel):
    """Input for vector memory search."""

    model_config = {"extra": "forbid"}

    scope: str
    query: str
    k: int = 8
    filters: dict[str, Any] = Field(default_factory=dict)
    embedding_provider: str | None = None
    embedding_model: str | None = None


class VectorSearchResult(BaseModel):
    """One search result from vector memory."""

    model_config = {"extra": "forbid"}

    id: str
    score: float
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorSearchOutput(BaseModel):
    """Output for vector memory search."""

    model_config = {"extra": "forbid"}

    results: list[VectorSearchResult] = Field(default_factory=list)


__all__ = [
    "VectorSearchInput",
    "VectorSearchOutput",
    "VectorSearchResult",
    "VectorUpsertInput",
    "VectorUpsertOutput",
]
