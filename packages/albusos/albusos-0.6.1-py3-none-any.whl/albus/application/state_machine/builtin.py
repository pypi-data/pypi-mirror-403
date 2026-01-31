"""Built-in state machines for AlbusOS.

These are the core agent behaviors available at startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from albus.domain.runs.state_machine import (
    AgentEvent,
    AgentState,
    AgentTransition,
    StateMachine,
)

if TYPE_CHECKING:
    from albus.infrastructure.repositories.state_machine_repository import (
        StateMachineRepository,
    )


# =============================================================================
# HOST - Fast single-agent with direct tool access
# =============================================================================
#
# Simple two-state machine:
#   idle → (task) → working → (done) → idle
#
# The "working" state runs a single AgentLoopNode with ALL tools.
# No planning/reviewing/delegating overhead - just do the work.

HOST_STATE_MACHINE = StateMachine(
    id="host.v1",
    name="Host",
    description="Fast single-agent - direct tool access, no planning overhead",
    version="1",
    initial_state="idle",
    states={
        "idle": AgentState(
            id="idle",
            name="Idle",
            description="Waiting for task",
        ),
        "working": AgentState(
            id="working",
            name="Working",
            description="Executing task with tools",
            entry_pathway="host.work",
            emit_event_on_complete="done",
        ),
    },
    events={
        "task": AgentEvent(id="task", name="Task", description="User task"),
        "done": AgentEvent(id="done", name="Done", internal=True),
    },
    transitions=[
        AgentTransition(from_state="idle", event="task", to_state="working"),
        AgentTransition(from_state="working", event="done", to_state="idle"),
    ],
    context_schema={
        "type": "object",
        "properties": {
            "task": {"type": "string"},
            "result": {"type": "string"},
        },
    },
    initial_context={"task": "", "result": ""},
)


# =============================================================================
# WORKFLOW STATE MACHINE (for multi-step workflows with approval)
# =============================================================================

WORKFLOW_STATE_MACHINE = StateMachine(
    id="workflow.approval.v1",
    name="Workflow with Approval",
    description="Multi-step workflow with optional human approval",
    version="1",
    initial_state="pending",
    states={
        "pending": AgentState(id="pending", name="Pending"),
        "running": AgentState(id="running", name="Running"),
        "waiting_approval": AgentState(id="waiting_approval", name="Waiting for Approval"),
        "completed": AgentState(id="completed", name="Completed", is_terminal=True),
        "failed": AgentState(id="failed", name="Failed", is_terminal=True),
    },
    events={
        "start": AgentEvent(id="start", name="Start"),
        "approve_needed": AgentEvent(id="approve_needed", name="Approval Needed"),
        "approved": AgentEvent(id="approved", name="Approved"),
        "rejected": AgentEvent(id="rejected", name="Rejected"),
        "complete": AgentEvent(id="complete", name="Complete"),
        "error": AgentEvent(id="error", name="Error"),
    },
    transitions=[
        AgentTransition(from_state="pending", event="start", to_state="running"),
        AgentTransition(from_state="running", event="approve_needed", to_state="waiting_approval"),
        AgentTransition(from_state="running", event="complete", to_state="completed"),
        AgentTransition(from_state="running", event="error", to_state="failed"),
        AgentTransition(from_state="waiting_approval", event="approved", to_state="running"),
        AgentTransition(from_state="waiting_approval", event="rejected", to_state="failed"),
    ],
)


# =============================================================================
# REGISTRATION
# =============================================================================

ALL_BUILTIN_STATE_MACHINES = [
    HOST_STATE_MACHINE,
    WORKFLOW_STATE_MACHINE,
]


def register_builtin_state_machines(repo: "StateMachineRepository") -> None:
    """Register all built-in state machines with a repository."""
    for sm in ALL_BUILTIN_STATE_MACHINES:
        repo.register(sm)


__all__ = [
    "HOST_STATE_MACHINE",
    "WORKFLOW_STATE_MACHINE",
    "ALL_BUILTIN_STATE_MACHINES",
    "register_builtin_state_machines",
]
