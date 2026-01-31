"""Debug Handler - Pretty-prints events for debugging.

Usage:
    albus = AlbusService(debug=True)  # Enables this automatically
    
    # Or manually:
    from albus.infrastructure.observability import DebugHandler
    albus.events.on_all(DebugHandler())
"""

from __future__ import annotations

import json
import sys
from datetime import datetime

from albus.infrastructure.observability.events import (
    Event,
    EventType,
    StateTransitionEvent,
    TurnStartedEvent,
    TurnCompletedEvent,
    TurnFailedEvent,
    PathwayCreatedEvent,
    PathwayStartedEvent,
    PathwayCompletedEvent,
    NodeStartedEvent,
    NodeCompletedEvent,
    NodeFailedEvent,
    ToolCalledEvent,
    ToolCompletedEvent,
    ToolFailedEvent,
    LLMRequestEvent,
    LLMResponseEvent,
)


# ANSI colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def _truncate(s: str, max_len: int = 80) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


class DebugHandler:
    """Pretty-prints events to stdout for debugging."""

    def __init__(self, show_timestamps: bool = True, verbose: bool = False):
        self.show_timestamps = show_timestamps
        self.verbose = verbose
        self._indent = 0

    def __call__(self, event: Event) -> None:
        """Handle an event."""
        method = getattr(self, f"_handle_{event.type.value}", None)
        if method:
            method(event)
        elif self.verbose:
            self._print_generic(event)

    def _prefix(self) -> str:
        ts = (
            f"{Colors.DIM}{_timestamp()}{Colors.RESET} " if self.show_timestamps else ""
        )
        indent = "  " * self._indent
        return f"{ts}{indent}"

    def _print(self, *args, **kwargs):
        print(self._prefix(), *args, **kwargs, file=sys.stderr)

    def _print_generic(self, event: Event):
        self._print(f"{Colors.DIM}[{event.type.value}]{Colors.RESET}")

    # =========================================================================
    # STATE MACHINE EVENTS
    # =========================================================================

    def _handle_state_transition(self, event: StateTransitionEvent):
        arrow = f"{Colors.YELLOW}→{Colors.RESET}"
        self._print(
            f"{Colors.CYAN}[STATE]{Colors.RESET} "
            f"{event.from_state} {arrow} {Colors.BOLD}{event.to_state}{Colors.RESET} "
            f"{Colors.DIM}({event.trigger}){Colors.RESET}"
        )

    # =========================================================================
    # TURN EVENTS
    # =========================================================================

    def _handle_turn_started(self, event: TurnStartedEvent):
        self._print(
            f"{Colors.GREEN}┌─ TURN STARTED{Colors.RESET} "
            f"{Colors.DIM}[{event.turn_id}]{Colors.RESET}"
        )
        self._print(
            f"{Colors.GREEN}│{Colors.RESET} "
            f"{Colors.WHITE}User:{Colors.RESET} {_truncate(event.message, 60)}"
        )
        self._indent += 1

    def _handle_turn_completed(self, event: TurnCompletedEvent):
        self._indent = max(0, self._indent - 1)
        response_preview = _truncate(event.response or "", 60)
        self._print(
            f"{Colors.GREEN}└─ TURN COMPLETED{Colors.RESET} "
            f"{Colors.DIM}{event.duration_ms:.0f}ms{Colors.RESET}"
        )
        if response_preview:
            self._print(f"   {Colors.WHITE}Response:{Colors.RESET} {response_preview}")

    def _handle_turn_failed(self, event: TurnFailedEvent):
        self._indent = max(0, self._indent - 1)
        self._print(
            f"{Colors.RED}└─ TURN FAILED{Colors.RESET} "
            f"{Colors.RED}{event.error}{Colors.RESET}"
        )

    # =========================================================================
    # PATHWAY EVENTS
    # =========================================================================

    def _handle_pathway_created(self, event: PathwayCreatedEvent):
        name = event.pathway_name or event.pathway_id
        self._print(
            f"{Colors.GREEN}✨ PATHWAY CREATED{Colors.RESET} "
            f"{Colors.BOLD}{name}{Colors.RESET} "
            f"{Colors.DIM}({event.node_count} nodes){Colors.RESET}"
        )
        # Show nodes
        if event.nodes:
            for node in event.nodes:
                prompt_preview = ""
                if node.prompt:
                    prompt_preview = (
                        f" {Colors.DIM}→ {_truncate(node.prompt, 40)}{Colors.RESET}"
                    )
                self._print(
                    f"   {Colors.CYAN}├─{Colors.RESET} "
                    f"{node.id} {Colors.DIM}({node.type}){Colors.RESET}"
                    f"{prompt_preview}"
                )
        # Show connections
        if event.connections:
            conns = " → ".join([f"{c[0]}→{c[1]}" for c in event.connections[:3]])
            if len(event.connections) > 3:
                conns += f" +{len(event.connections) - 3} more"
            self._print(f"   {Colors.DIM}Connections: {conns}{Colors.RESET}")

    def _handle_pathway_started(self, event: PathwayStartedEvent):
        name = event.pathway_name or event.pathway_id
        node_count = event.node_count or len(event.nodes) if event.nodes else 0
        self._print(
            f"{Colors.BLUE}▶ PATHWAY{Colors.RESET} "
            f"{Colors.BOLD}{name}{Colors.RESET} "
            f"{Colors.DIM}({node_count} nodes){Colors.RESET}"
        )
        # Show nodes if available
        if event.nodes:
            for node in event.nodes:
                self._print(f"   {Colors.DIM}├─ {node.id} ({node.type}){Colors.RESET}")
        self._indent += 1

    def _handle_pathway_completed(self, event: PathwayCompletedEvent):
        self._indent = max(0, self._indent - 1)
        name = event.pathway_name or event.pathway_id
        status = (
            f"{Colors.GREEN}✓{Colors.RESET}"
            if event.success
            else f"{Colors.RED}✗{Colors.RESET}"
        )
        duration = f"{event.duration_ms:.0f}ms" if event.duration_ms is not None else ""
        self._print(
            f"{Colors.BLUE}■ PATHWAY{Colors.RESET} "
            f"{name} {status} "
            f"{Colors.DIM}{duration}{Colors.RESET}"
        )

    # =========================================================================
    # NODE EVENTS
    # =========================================================================

    def _handle_node_started(self, event: NodeStartedEvent):
        self._print(
            f"{Colors.MAGENTA}○{Colors.RESET} "
            f"{event.node_id} {Colors.DIM}({event.node_type}){Colors.RESET}"
        )

    def _handle_node_completed(self, event: NodeCompletedEvent):
        status = f"{Colors.GREEN}●{Colors.RESET}"
        output_preview = ""
        if self.verbose and event.outputs:
            output_preview = f" → {_truncate(json.dumps(event.outputs), 50)}"
        duration = (
            f"{event.duration_ms:.0f}ms" if event.duration_ms is not None else "?"
        )
        self._print(
            f"{status} "
            f"{event.node_id} "
            f"{Colors.DIM}{duration}{Colors.RESET}"
            f"{output_preview}"
        )

    def _handle_node_failed(self, event: NodeFailedEvent):
        self._print(
            f"{Colors.RED}●{Colors.RESET} "
            f"{event.node_id} "
            f"{Colors.RED}ERROR: {event.error}{Colors.RESET}"
        )

    # =========================================================================
    # TOOL EVENTS
    # =========================================================================

    def _handle_tool_called(self, event: ToolCalledEvent):
        args_preview = (
            _truncate(json.dumps(event.tool_args), 40) if event.tool_args else ""
        )
        self._print(
            f"{Colors.YELLOW}⚡{Colors.RESET} "
            f"{Colors.BOLD}{event.tool_name}{Colors.RESET}"
            f"{Colors.DIM}({args_preview}){Colors.RESET}"
        )

    def _handle_tool_completed(self, event: ToolCompletedEvent):
        status = (
            f"{Colors.GREEN}✓{Colors.RESET}"
            if event.success
            else f"{Colors.RED}✗{Colors.RESET}"
        )
        result_preview = ""
        if self.verbose and event.result:
            result_preview = f" → {_truncate(str(event.result), 50)}"
        duration = f"{event.duration_ms:.0f}ms" if event.duration_ms is not None else ""
        self._print(
            f"  {status} "
            f"{event.tool_name} "
            f"{Colors.DIM}{duration}{Colors.RESET}"
            f"{result_preview}"
        )

    def _handle_tool_failed(self, event: ToolFailedEvent):
        self._print(
            f"  {Colors.RED}✗{Colors.RESET} "
            f"{event.tool_name} "
            f"{Colors.RED}{event.error}{Colors.RESET}"
        )

    # =========================================================================
    # LLM EVENTS
    # =========================================================================

    def _handle_llm_request(self, event: LLMRequestEvent):
        prompt_preview = _truncate(event.prompt, 50)
        self._print(
            f"{Colors.CYAN}🤖{Colors.RESET} "
            f"{Colors.DIM}{event.model}{Colors.RESET} "
            f"← {prompt_preview}"
        )

    def _handle_llm_response(self, event: LLMResponseEvent):
        response_preview = _truncate(event.response, 50)
        tokens = ""
        if event.tokens_in or event.tokens_out:
            tokens = f" [{event.tokens_in or '?'}→{event.tokens_out or '?'} tokens]"
        duration = f"{event.duration_ms:.0f}ms" if event.duration_ms is not None else ""
        self._print(
            f"  {Colors.CYAN}→{Colors.RESET} "
            f"{response_preview} "
            f"{Colors.DIM}{duration}{tokens}{Colors.RESET}"
        )


__all__ = ["DebugHandler", "Colors"]
