"""Tool Registry Port - Contract for tool discovery and invocation.

This port is used by ALL pathway execution, not just Albus. The port defines
how pathways discover and invoke tools.

Access Control via Kernels:
- PrivilegedKernel: Full access (builtin + MCP tools like GitHub, Notion)
- UserKernel: Sandboxed access (restricted builtin tools, no MCP)

The registry implementation decides what tools are available based on the
kernel context. The port is generic; policy is in the implementation.

Architecture:
- ToolContext: Injected dependencies for tool execution
- ToolSchema: Tool metadata for pathway/LLM reasoning
- ToolRegistryPort: Discovery and invocation protocol
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathway_engine.application.ports.mcp import MCPClientPort
    from pathway_engine.application.ports.runtime import PathwayExecutorPort


# =============================================================================
# Errors
# =============================================================================


class ToolNotFoundError(Exception):
    """Raised when a tool is not found in the registry."""

    def __init__(self, tool_id: str):
        self.tool_id = tool_id
        super().__init__(f"Tool not found: {tool_id}")


class ToolInvocationError(Exception):
    """Raised when tool invocation fails."""

    def __init__(self, tool_id: str, reason: str, cause: Exception | None = None):
        self.tool_id = tool_id
        self.reason = reason
        self.cause = cause
        super().__init__(f"Tool invocation failed [{tool_id}]: {reason}")


# =============================================================================
# Context
# =============================================================================


@dataclass
class ToolContext:
    """Context passed to tool handlers with injected dependencies.

    Tools receive everything they need via this context - no _get_runtime(),
    no globals, no service locators.

    This context is built by the kernel/execution layer and passed to tools.
    Different kernels provide different context:
    - PrivilegedKernel: Full services (domain, mcp_client, etc.)
    - UserKernel: Sandboxed services (restricted domain, no mcp_client)

    Usage:
        async def read_file(inputs: dict, context: ToolContext) -> dict:
            doc = context.domain.get_document(inputs["path"])
            ...
    """

    # Core services - may be None for minimal/sandboxed contexts
    # Type is Any to avoid engine depending on studio layer
    domain: Any = None

    # Execution services
    pathway_executor: PathwayExecutorPort | None = None

    # External services (PrivilegedKernel only)
    mcp_client: MCPClientPort | None = None

    # Session context
    workspace_id: str | None = None
    thread_id: str | None = None

    # Kernel identity (for policy decisions)
    kernel: str = "user"  # "privileged" | "user"

    # Additional context
    extras: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get an extra context value."""
        return self.extras.get(key, default)

    @property
    def is_privileged(self) -> bool:
        """Check if this is a privileged kernel context."""
        return self.kernel == "privileged"


# =============================================================================
# Schema
# =============================================================================


@dataclass(frozen=True)
class ToolSchema:
    """Schema for a tool available in the registry.

    Used by pathways and LLMs to understand what tools are available
    and how to call them.
    """

    id: str  # e.g., "workspace.read_file", "github.search_code"
    name: str  # Human-readable name
    description: str  # What the tool does
    input_schema: dict[str, Any]  # JSON Schema for inputs
    category: str = "builtin"  # "builtin" | "mcp" | "pathway" | "user"
    source: str | None = None  # e.g., "mcp:github" for MCP tools
    requires_privileged: bool = False  # True for MCP tools, dangerous operations


# =============================================================================
# Port
# =============================================================================


@runtime_checkable
class ToolRegistryPort(Protocol):
    """Port for tool discovery and invocation.

    Used by:
    - PathwayVM for tool_node execution
    - Albus for LLM function calling
    - Any pathway that needs tool access

    Implementations control access based on kernel type:
    - PrivilegedKernel gets all tools
    - UserKernel gets sandboxed subset

    Key principle: Tools receive ToolContext with injected dependencies.
    No globals. No service locators. Everything explicit.
    """

    def list_tools(self, *, privileged: bool = False) -> list[ToolSchema]:
        """List available tools.

        Args:
            privileged: If True, include privileged-only tools (MCP, etc.)

        Returns:
            List of tool schemas available for the given access level.
        """
        ...

    def get_tool(self, tool_id: str) -> ToolSchema | None:
        """Get a specific tool's schema by ID."""
        ...

    async def invoke(
        self,
        tool_id: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Invoke a tool with given arguments.

        Args:
            tool_id: Tool identifier (e.g., "workspace.read_file")
            arguments: Tool input arguments
            context: Injected dependencies and kernel context

        Returns:
            Tool output as a dict

        Raises:
            ToolNotFoundError: If tool not found
            ToolInvocationError: If tool execution fails
            PermissionError: If tool requires privileged but context is not
        """
        ...

    def get_schemas_for_prompt(self, *, privileged: bool = False) -> str:
        """Get tool schemas formatted for LLM prompts.

        Args:
            privileged: If True, include privileged-only tools

        Returns:
            String representation of available tools for system prompts.
        """
        ...


__all__ = [
    # Errors
    "ToolNotFoundError",
    "ToolInvocationError",
    # Context
    "ToolContext",
    # Schema
    "ToolSchema",
    # Port
    "ToolRegistryPort",
]
