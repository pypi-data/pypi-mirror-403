"""pathway_engine.execution.api - stable public surface for host/runtime integration.

This module exists purely for **import hygiene** and dev UX:
- Host code should import runtime wiring + policy context from here,
  not from deep `pathway_engine.execution.*` modules.

Implementation details still live in their subsystem modules.
"""

from __future__ import annotations

# Host/runtime wiring boundary (keeps host from importing VM/tool internals).
from pathway_engine.application.host_adapter import (  # noqa: F401
    HostRuntimeWiring,
    build_host_runtime_wiring,
)

# Tool policy context (request-scoped contextvars; used by host + runtime policy wrapper).
from pathway_engine.application.ports.runtime import (  # noqa: F401
    ToolPolicyContext,
    get_tool_policy_context,
    tool_policy_context,
)

__all__ = [
    # Wiring
    "HostRuntimeWiring",
    "build_host_runtime_wiring",
    # Policy context
    "ToolPolicyContext",
    "get_tool_policy_context",
    "tool_policy_context",
]
