"""Agent registry for AlbusOS.

Agents are registered via the @agent decorator at import time.
This mirrors the pack registry pattern for consistency.

Usage:
    # In your agent module (e.g., src/agents/my_assistant/agent.py)
    from agents.registry import agent

    @agent
    def MY_ASSISTANT():
        return (
            agent_builder()
            .id("my_assistant")
            .name("My Assistant")
            .skill(my_skill)
            .build()
        )

The agent is automatically registered when its module is imported.
"""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import TYPE_CHECKING, Callable, Iterable, TypeVar

if TYPE_CHECKING:
    from pathway_engine.domain.agent.core import Agent

logger = logging.getLogger(__name__)

# Registry of available agents
_AGENT_REGISTRY: dict[str, "Agent"] = {}

# Flag to track if agents have been bootstrapped
_BOOTSTRAPPED = False

T = TypeVar("T")


def agent(
    func: Callable[[], "Agent"] | None = None,
    *,
    enabled: bool = True,
    env_gate: str | None = None,
) -> Callable[[], "Agent"] | Callable[[Callable[[], "Agent"]], Callable[[], "Agent"]]:
    """Decorator that registers an agent builder at import time.

    The decorated function should return an Agent. The agent is registered
    immediately when the module is imported.

    Args:
        func: Agent builder function (when used without arguments)
        enabled: Whether to register the agent (default True)
        env_gate: Optional env var that must be truthy to enable

    Examples:
        # Simple usage
        @agent
        def MY_AGENT():
            return agent_builder().id("my_agent").build()

        # With env gate
        @agent(env_gate="ALBUS_ENABLE_EXPERIMENTAL")
        def EXPERIMENTAL_AGENT():
            return agent_builder().id("experimental").build()

        # Disabled (for development)
        @agent(enabled=False)
        def WIP_AGENT():
            return agent_builder().id("wip").build()
    """

    def decorator(fn: Callable[[], "Agent"]) -> Callable[[], "Agent"]:
        @wraps(fn)
        def wrapper() -> "Agent":
            return fn()

        # Check if enabled
        should_register = enabled
        if env_gate:
            gate_val = os.getenv(env_gate, "").strip().lower()
            should_register = should_register and gate_val in ("1", "true", "yes", "on")

        if should_register:
            try:
                agent_instance = fn()
                register_agent(agent_instance)
                logger.debug("Registered agent: %s", agent_instance.id)
            except Exception as e:
                logger.warning("Failed to register agent from %s: %s", fn.__name__, e)

        return wrapper

    if func is not None:
        # Called without arguments: @agent
        return decorator(func)
    else:
        # Called with arguments: @agent(env_gate="...")
        return decorator


def register_agent(agent_instance: "Agent") -> None:
    """Register an agent in the registry."""
    _AGENT_REGISTRY[agent_instance.id] = agent_instance


def _bootstrap_agents() -> None:
    """Import agent modules to trigger @agent registration."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    _BOOTSTRAPPED = True

    # Add new agents here
    try:
        import agents.competitor_analyst.agent  # noqa: F401
    except ImportError:
        pass


def list_available_agents() -> list["Agent"]:
    """Return all registered agents."""
    _bootstrap_agents()
    return list(_AGENT_REGISTRY.values())


def get_agent_by_id(agent_id: str) -> "Agent | None":
    """Get an agent by ID."""
    _bootstrap_agents()
    return _AGENT_REGISTRY.get(agent_id)


def resolve_agent_ids(ids: Iterable[str]) -> tuple[list["Agent"], list[str]]:
    """Resolve agent IDs to Agent objects.

    Returns (agents, missing_ids).
    """
    agents: list["Agent"] = []
    missing: list[str] = []
    for aid in ids:
        a = get_agent_by_id(aid)
        if a is None:
            missing.append(aid)
        else:
            agents.append(a)
    return agents, missing


def clear_registry() -> None:
    """Clear all registered agents (for testing)."""
    global _BOOTSTRAPPED
    _AGENT_REGISTRY.clear()
    _BOOTSTRAPPED = False


__all__ = [
    "agent",
    "register_agent",
    "list_available_agents",
    "get_agent_by_id",
    "resolve_agent_ids",
    "clear_registry",
]
