"""Built-in state machines for common OS agent patterns.

These are registered at startup and available to all agents.

Packs may ship additional state machines, but those belong in `packs/`,
not the product runtime.
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
# WORKFLOW STATE MACHINE (for multi-step workflows)
# =============================================================================
# A state machine for workflows that need human approval:
#   pending → (start) → running → (complete) → completed
#                     → (approve_needed) → waiting_approval → (approved) → running
#                                                          → (rejected) → failed

WORKFLOW_STATE_MACHINE = StateMachine(
    id="workflow.approval.v1",
    name="Workflow with Approval",
    description="Multi-step workflow with optional human approval",
    version="1",
    initial_state="pending",
    states={
        "pending": AgentState(
            id="pending",
            name="Pending",
            description="Workflow not yet started",
        ),
        "running": AgentState(
            id="running",
            name="Running",
            description="Workflow is executing",
        ),
        "waiting_approval": AgentState(
            id="waiting_approval",
            name="Waiting for Approval",
            description="Workflow paused, waiting for human approval",
        ),
        "completed": AgentState(
            id="completed",
            name="Completed",
            description="Workflow finished successfully",
            is_terminal=True,
        ),
        "failed": AgentState(
            id="failed",
            name="Failed",
            description="Workflow failed or was rejected",
            is_terminal=True,
        ),
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
        AgentTransition(
            from_state="running", event="approve_needed", to_state="waiting_approval"
        ),
        AgentTransition(from_state="running", event="complete", to_state="completed"),
        AgentTransition(from_state="running", event="error", to_state="failed"),
        AgentTransition(
            from_state="waiting_approval", event="approved", to_state="running"
        ),
        AgentTransition(
            from_state="waiting_approval", event="rejected", to_state="failed"
        ),
    ],
)


# =============================================================================
# REGISTRATION
# =============================================================================

ALL_BUILTIN_STATE_MACHINES = [
    WORKFLOW_STATE_MACHINE,
]


def register_builtin_state_machines(repo: "StateMachineRepository") -> None:
    """Register all built-in state machines with a repository."""
    for sm in ALL_BUILTIN_STATE_MACHINES:
        repo.register(sm)


__all__ = [
    "WORKFLOW_STATE_MACHINE",
    "ALL_BUILTIN_STATE_MACHINES",
    "register_builtin_state_machines",
]
