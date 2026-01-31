"""Execution Context - Services available to nodes during execution.

This is a simple services bag. No resolvers, no magic - just a dict of tools
and optional extras.

Nodes access capabilities via:
    result = await ctx.tools["llm.generate"](args, ctx)
    result = await ctx.tools["workspace.read_file"](args, ctx)

The Context is built at boot time (albus/boot.py) and passed
to PathwayVM. Nodes receive it in their compute() method.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Tool handler signature: async (args: dict, ctx: Context) -> dict
ToolHandler = Callable[[dict[str, Any], "Context"], Awaitable[dict[str, Any]]]


@dataclass
class Context:
    """Services available during graph execution.

    This is the ONLY way nodes access external capabilities.
    No globals, no service locators - everything through ctx.

    Attributes:
        tools: Dict of tool_name -> async handler function.
               Nodes call: await ctx.tools["tool.name"](args, ctx)

        memory: Optional memory store for read/write nodes.

        extras: Arbitrary additional services (domain, mcp_client, etc.)
                Access via ctx.extras.get("key")

        pathway_id: ID of the pathway being executed.
        execution_id: Unique ID for this execution.
        workspace_id: Current workspace (if any).
        thread_id: Current thread/session (if any).
    """

    # Core: tools as flat dict (no resolver needed)
    tools: dict[str, ToolHandler] = field(default_factory=dict)

    # Optional memory store
    memory: Any = None

    # Additional services (domain, mcp_client, learning_store, etc.)
    extras: dict[str, Any] = field(default_factory=dict)

    # Runtime identifiers
    pathway_id: str = ""
    execution_id: str = ""
    workspace_id: str | None = None
    thread_id: str | None = None

    # Policy context (for governance)
    policy_approved: bool = False
    policy_actor_id: str | None = None

    def get_tool(self, name: str) -> ToolHandler | None:
        """Get a tool handler by name. Returns None if not found."""
        return self.tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is available."""
        return name in self.tools

    def list_tools(self) -> list[str]:
        """List all available tool names."""
        return list(self.tools.keys())

    def get_extra(self, key: str, default: Any = None) -> Any:
        """Get an extra service by key."""
        return self.extras.get(key, default)

    @property
    def services(self) -> "ContextServices":
        """Typed view over `extras` for core cross-layer services.

        This reduces drift by giving important wiring points stable names, while
        keeping `extras` as the underlying storage for gradual adoption.
        """
        from pathway_engine.domain.services import ContextServices

        return ContextServices(self.extras)


__all__ = [
    "Context",
    "ToolHandler",
]
