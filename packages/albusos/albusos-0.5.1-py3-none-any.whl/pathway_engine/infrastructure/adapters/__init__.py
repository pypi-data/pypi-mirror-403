"""Wiring - connects PathwayVM to execution services."""

from pathway_engine.infrastructure.adapters.runtime_bridge import RuntimeBridge
from pathway_engine.infrastructure.adapters.tool_registry import ToolRegistry

__all__ = [
    "RuntimeBridge",
    "ToolRegistry",
]
