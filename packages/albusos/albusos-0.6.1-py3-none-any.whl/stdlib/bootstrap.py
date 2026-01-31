"""stdlib bootstrap.

This module exists to make it explicit (and auditable) which stdlib modules
are imported for side-effect tool registration.

No shims: runtime must import this (or explicitly import modules) to register tools.
"""

from __future__ import annotations


def load_stdlib() -> None:
    # Import tool modules to register them via @register_tool decorators.
    # Keep this list explicit.
    #
    # NOTE: Streaming event sources (timer.interval, webhook.listen) moved to
    # pathway_engine.domain.streaming - they are VM primitives, not general tools.
    from stdlib import registry as _registry  # noqa: F401

    from stdlib.tools import (  # noqa: F401
        # Tools for LLM agents and pathways
        agent,  # Agent tools (spawn, turn, list)
        code,
        graph_ops,
        introspection,
        kg,
        llm,
        mcp,
        memory,
        pathway,
        search,
        skill,
        speech,
        vector,
        vision,
        viz,
        web,
        workspace,
    )


__all__ = ["load_stdlib"]
