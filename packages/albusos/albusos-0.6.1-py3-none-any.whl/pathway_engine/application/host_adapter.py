"""Host-facing runtime adapter (ports + wiring helpers).

Goal: keep `albus` from importing deep runtime internals.

The host owns *boundaries* (DB, MCP processes, HTTP), while the runtime owns
*execution wiring* (tool resolution + VM construction).

All operations go through Context.tools - no direct service access.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from pathway_engine.application.ports.tool_registry import ToolRegistryPort


class CoordinatorPort(Protocol):
    """Minimal port for runtime coordination (events, cross-protocol fanout)."""

    pass


@dataclass(frozen=True)
class HostRuntimeWiring:
    """Wired runtime components for the host boundary."""

    tool_registry: ToolRegistryPort
    make_pathway_vm: Callable[[], Any]


def build_host_runtime_wiring(
    *,
    coordinator: CoordinatorPort,
    mcp_client: Any | None = None,
    audit_sink: Any | None = None,
) -> HostRuntimeWiring:
    """Build runtime wiring for `albus`.

    Args:
        coordinator: Runtime coordination port for events/fanout.
        mcp_client: Optional MCP client (MCPClientPort) for external tools.
        audit_sink: Optional audit sink for governance logging.
    """
    from pathway_engine.infrastructure.adapters.tool_registry import ToolRegistry
    from pathway_engine.application.kernel import PathwayVM
    from pathway_engine.domain.context import Context

    # Build tool registry (includes all LLM, vector, MCP tools)
    tool_registry: ToolRegistryPort = ToolRegistry(mcp_client=mcp_client)

    def make_pathway_vm() -> Any:
        ctx = Context(tools=tool_registry.as_dict())
        return PathwayVM(ctx=ctx)

    return HostRuntimeWiring(
        tool_registry=tool_registry, make_pathway_vm=make_pathway_vm
    )
