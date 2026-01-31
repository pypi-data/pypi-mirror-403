"""Context schemas - budgets and context management."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextBudgetV1(BaseModel):
    """Token budget allocation for context gathering.

    Controls how much context Albus gathers for each category.
    """

    model_config = {"extra": "allow"}

    # Total token budget
    total_tokens: int = Field(default=8000, description="Total tokens to allocate")

    # Category allocations (fractions of total)
    system_prompt_fraction: float = Field(
        default=0.1, description="System prompt allocation"
    )
    chat_history_fraction: float = Field(
        default=0.3, description="Chat history allocation"
    )
    workspace_fraction: float = Field(
        default=0.2, description="Workspace context allocation"
    )
    memory_fraction: float = Field(default=0.2, description="Vector memory allocation")
    tools_fraction: float = Field(
        default=0.2, description="Tool definitions allocation"
    )

    # Hard limits
    max_messages: int = Field(default=20, description="Max chat history messages")
    max_memory_results: int = Field(default=10, description="Max vector memory results")
    max_workspace_files: int = Field(
        default=5, description="Max workspace files to include"
    )


__all__ = ["ContextBudgetV1"]
