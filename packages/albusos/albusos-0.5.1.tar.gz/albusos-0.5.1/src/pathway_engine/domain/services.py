"""Typed context services - an explicit, low-drift surface over `Context.extras`.

`Context.extras` is a flexible escape hatch, but it tends to become a junk drawer.
To reduce architectural confusion, `Context.services` provides a *typed* view for
the most important cross-layer wiring points (domain, MCP, nested execution, etc).

This is intentionally a thin wrapper over `extras` (no new storage), so it can be
adopted incrementally without breaking callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class ContextServices:
    """Typed accessor for `Context.extras`."""

    extras: dict[str, Any]

    # ---- Core cross-layer services (most confusing in review) ----
    @property
    def domain(self) -> Any | None:
        return self.extras.get("domain")

    @domain.setter
    def domain(self, value: Any | None) -> None:
        self.extras["domain"] = value

    @property
    def mcp_client(self) -> Any | None:
        return self.extras.get("mcp_client")

    @mcp_client.setter
    def mcp_client(self, value: Any | None) -> None:
        self.extras["mcp_client"] = value

    @property
    def pathway_executor(self) -> Any | None:
        return self.extras.get("pathway_executor")

    @pathway_executor.setter
    def pathway_executor(self, value: Any | None) -> None:
        self.extras["pathway_executor"] = value

    @property
    def tool_definitions(self) -> Mapping[str, Any] | None:
        v = self.extras.get("tool_definitions")
        return v if isinstance(v, Mapping) else None

    @tool_definitions.setter
    def tool_definitions(self, value: Mapping[str, Any] | None) -> None:
        self.extras["tool_definitions"] = value

    @property
    def event_bus(self) -> Any | None:
        return self.extras.get("event_bus")

    @event_bus.setter
    def event_bus(self, value: Any | None) -> None:
        self.extras["event_bus"] = value

    @property
    def context_budget(self) -> Any | None:
        return self.extras.get("context_budget")

    @context_budget.setter
    def context_budget(self, value: Any | None) -> None:
        self.extras["context_budget"] = value

    # ---- Pack / Trigger / Action services ----
    @property
    def action_dispatcher(self) -> Any | None:
        """ActionDispatcher for routing action outputs."""
        return self.extras.get("action_dispatcher")

    @action_dispatcher.setter
    def action_dispatcher(self, value: Any | None) -> None:
        self.extras["action_dispatcher"] = value

    @property
    def trigger_context(self) -> Any | None:
        """TriggerContext for the event that triggered this pathway."""
        return self.extras.get("trigger_context")

    @trigger_context.setter
    def trigger_context(self, value: Any | None) -> None:
        self.extras["trigger_context"] = value

    @property
    def trigger_manager(self) -> Any | None:
        """TriggerManager for managing trigger subscriptions."""
        return self.extras.get("trigger_manager")

    @trigger_manager.setter
    def trigger_manager(self, value: Any | None) -> None:
        self.extras["trigger_manager"] = value

    @property
    def pack(self) -> Any | None:
        """The Pack that owns the current pathway."""
        return self.extras.get("pack")

    @pack.setter
    def pack(self, value: Any | None) -> None:
        self.extras["pack"] = value


__all__ = ["ContextServices"]
