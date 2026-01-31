"""pathway_engine.contracts - Engine-level contracts.

This package contains engine-level DTOs for pathway execution.
Studio/product contracts live in persistence.contracts.
"""

from __future__ import annotations

from pathway_engine.application.ports.contracts.errors import (
    StudioConflict,
    StudioError,
    StudioNotFound,
    StudioValidationError,
)
from pathway_engine.application.ports.contracts.knowledge import (
    WorkspaceKnowledgeSearchRequest,
    WorkspaceKnowledgeSearchResponse,
    WorkspaceKnowledgeSnippet,
)
from pathway_engine.application.ports.contracts.tool_policy import (
    ToolImpact,
    ToolPolicyContext,
    ToolPolicyDecision,
)

__all__ = [
    # Errors
    "StudioError",
    "StudioNotFound",
    "StudioValidationError",
    "StudioConflict",
    # Policy
    "ToolPolicyContext",
    "ToolImpact",
    "ToolPolicyDecision",
    # Knowledge
    "WorkspaceKnowledgeSearchRequest",
    "WorkspaceKnowledgeSearchResponse",
    "WorkspaceKnowledgeSnippet",
]
