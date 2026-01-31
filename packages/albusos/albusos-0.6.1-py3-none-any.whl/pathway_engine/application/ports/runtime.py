"""Runtime ports.

These Protocols describe the minimal runtime/execution surfaces that outer layers
can depend on without importing `pathway_engine.execution` implementation types.

Also includes the policy context management for cross-layer access without
creating circular dependencies.
"""

from __future__ import annotations

import contextlib
import contextvars
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pathway_engine.application.ports.contracts import ToolPolicyContext

# ==============================================================================
# POLICY CONTEXT (request-scoped via contextvars)
# ==============================================================================

# Provide a safe default "null" context.
_CTX: contextvars.ContextVar[ToolPolicyContext] = contextvars.ContextVar(
    "tool_policy_context", default=ToolPolicyContext(origin="unknown", approved=False)
)


def get_tool_policy_context() -> ToolPolicyContext:
    """Get the current tool policy context from the contextvar."""
    return _CTX.get()


@contextlib.contextmanager
def tool_policy_context(ctx: ToolPolicyContext):
    """Set the tool policy context for a block of code."""
    token = _CTX.set(ctx)
    try:
        yield
    finally:
        _CTX.reset(token)


# ==============================================================================
# PROTOCOLS
# ==============================================================================


@runtime_checkable
class PathwayExecutorPort(Protocol):
    """Minimal execution surface used by copilot + modes.

    Matches the shape of `PathwayVM.execute(...)` without importing `pathway_engine`.
    """

    async def execute(
        self, pathway: Any, inputs: dict[str, Any], **kwargs: Any
    ) -> Any: ...


class ExecutePathwayFn(Protocol):
    """Callable protocol for pathway execution.

    This is the minimal contract for executing pathways - just "run this pathway".
    Studio wires how execution actually happens.

    Usage:
        async def my_executor(pathway, inputs, **kwargs) -> Any: ...
        # Pass to any service that needs to execute pathways
    """

    async def __call__(
        self,
        pathway: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """Execute a pathway with inputs.

        Args:
            pathway: The Pathway to execute
            inputs: Input values for the pathway
            **kwargs: Additional execution options (execution_id, timeout, etc.)

        Returns:
            Execution result (PathwayRecord or similar)
        """
        ...


@runtime_checkable
class MemoryStorePort(Protocol):
    """Minimal memory store interface for pathway execution."""

    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> None: ...


@runtime_checkable
class KernelProtocol(Protocol):
    """Protocol defining what a kernel must provide to PathwayVM.

    This is the contract between PathwayVM and its runtime environment.
    Different kernels (UserKernel, PrivilegedKernel) implement this protocol
    with different configurations and capabilities.

    All capabilities (LLM, vector memory, MCP, etc) are accessed via
    tool_registry.invoke() - the tools-as-capabilities pattern.

    Lives in pathway_engine so all layers can depend on this contract without
    importing pathway_engine.execution implementation types.
    """

    @property
    def tool_registry(self) -> Any:
        """Tool registry for all capabilities (LLM, vector, MCP, etc).

        This is the ONLY way to access capabilities. Use:
        - tool_registry.invoke("llm.generate", {...})
        - tool_registry.invoke("vector.search", {...})
        - tool_registry.invoke("mcp.call", {...})
        """
        ...

    @property
    def memory_store(self) -> Any:
        """Memory store for pathway state (KV storage during execution)."""
        ...


@dataclass
class KernelConfig:
    """Configuration for building a kernel.

    This is the serializable/exportable configuration that defines
    how a kernel should be constructed. Used for:
    - User agent configs (exportable)
    - Saving/loading kernel configurations

    All capabilities (LLM, vector, etc) are configured via tools.
    LLM model/provider selection happens at tool invocation time.

    Lives in pathway_engine for cross-layer access.
    """

    # Tool configuration
    tool_ids: list[str] = field(default_factory=list)  # Allowed tools (empty = all)
    enable_builtin_tools: bool = True

    # Memory configuration
    memory_namespace: str = "default"

    # Isolation settings
    sandboxed: bool = True  # If True, no studio tools
    exportable: bool = True  # If True, config can be exported

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "tool_ids": self.tool_ids,
            "enable_builtin_tools": self.enable_builtin_tools,
            "memory_namespace": self.memory_namespace,
            "sandboxed": self.sandboxed,
            "exportable": self.exportable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KernelConfig":
        """Create configuration from dictionary."""
        return cls(
            tool_ids=list(data.get("tool_ids", [])),
            enable_builtin_tools=bool(data.get("enable_builtin_tools", True)),
            memory_namespace=str(data.get("memory_namespace", "default")),
            sandboxed=bool(data.get("sandboxed", True)),
            exportable=bool(data.get("exportable", True)),
        )


__all__ = [
    # Policy context
    "get_tool_policy_context",
    "tool_policy_context",
    # Protocols
    "PathwayExecutorPort",
    "ExecutePathwayFn",
    "MemoryStorePort",
    "KernelProtocol",
    "KernelConfig",
]
