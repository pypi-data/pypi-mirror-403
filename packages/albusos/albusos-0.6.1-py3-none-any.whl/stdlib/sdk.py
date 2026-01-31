"""stdlib.sdk - Small, stable stdlib surface for tool registration.

This is intentionally tiny:
- `load_stdlib()` explicitly imports all built-in tool modules for side-effect
  registration via @register_tool decorators.
- The registry exports let runtimes build a `pathway_engine.Context` with tools,
  and optionally expose tool schemas for function-calling nodes.
"""

from stdlib.bootstrap import load_stdlib
from stdlib.registry import (
    TOOL_DEFINITIONS,
    TOOL_HANDLERS,
    get_tool_schemas_for_llm,
    list_tool_schemas,
    register_tool,
)

__all__ = [
    "load_stdlib",
    "register_tool",
    "TOOL_HANDLERS",
    "TOOL_DEFINITIONS",
    "get_tool_schemas_for_llm",
    "list_tool_schemas",
]
