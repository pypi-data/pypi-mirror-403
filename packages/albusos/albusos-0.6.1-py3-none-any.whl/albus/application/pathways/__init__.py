"""Unified pathway management.

This package provides the single source of truth for ALL pathways:
- Pack-defined pathways (deployed from pathway_engine Python code)
- User-created pathways (created via tools/API/chat)

All pathways use the Pathway IR from pathway_engine.

Authoring Options:
    1. pathway_engine (Python) - Direct Pathway construction
    2. pathway.create tool - LLM-assisted via chat
"""

from albus.application.pathways.service import (
    PathwayService,
    PathwaySource,
    PathwayMeta,
)

__all__ = [
    # Service
    "PathwayService",
    "PathwaySource",
    "PathwayMeta",
]
