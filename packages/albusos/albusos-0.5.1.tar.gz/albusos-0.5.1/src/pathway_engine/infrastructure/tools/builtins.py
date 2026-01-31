"""Built-in tools available to all pathways.

Built-in tools are simple callables that receive **kwargs from the resolver.
They're registered by name and can be overridden or extended by hosts.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BuiltinToolFn = Callable[..., Any | Awaitable[Any]]


def default_builtin_tools() -> dict[str, BuiltinToolFn]:
    """Return the default set of built-in tools.

    Tools receive parameters as **kwargs:

        async def my_tool(query: str, limit: int = 10) -> dict:
            ...

    Returns:
        Dict mapping tool names to handler functions.
    """
    return {
        # Core tools can be added here as the system grows.
        # For now, hosts inject their own via builtin_tools_extra.
    }


__all__ = ["BuiltinToolFn", "default_builtin_tools"]
