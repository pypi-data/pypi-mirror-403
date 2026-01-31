"""stdlib - runtime-neutral standard library for agent execution.

Provides:
- tool registry + schemas
- default tools (workspace/search/web/code/memory/vector/kg/mcp/pathway)
- default streaming event sources (timer/webhook)

This package must NOT depend on `albus`.
"""

from stdlib.registry import (
    TOOL_DEFINITIONS,
    TOOL_HANDLERS,
    get_tool_schemas_for_llm,
    list_tool_schemas,
    register_tool,
)

__all__ = [
    "register_tool",
    "TOOL_HANDLERS",
    "TOOL_DEFINITIONS",
    "get_tool_schemas_for_llm",
    "list_tool_schemas",
]
