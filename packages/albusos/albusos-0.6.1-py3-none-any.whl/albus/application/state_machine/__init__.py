"""State Machine execution - the brain that runs agents.

This module contains:
- StateMachineController: Processes events and executes transitions
- Host: The meta-agent orchestrator (state machine + pathways)
- Built-in state machines for common patterns
"""

from albus.application.state_machine.controller import (
    StateMachineController,
    TransitionResult,
)
from albus.application.state_machine.builtin import (
    HOST_STATE_MACHINE,
    WORKFLOW_STATE_MACHINE,
    ALL_BUILTIN_STATE_MACHINES,
    register_builtin_state_machines,
)
from albus.application.state_machine.host_pathways import (
    HOST_PATHWAY_BUILDERS,
    register_host_pathways,
)

__all__ = [
    "StateMachineController",
    "TransitionResult",
    "HOST_STATE_MACHINE",
    "HOST_PATHWAY_BUILDERS",
    "WORKFLOW_STATE_MACHINE",
    "ALL_BUILTIN_STATE_MACHINES",
    "register_builtin_state_machines",
    "register_host_pathways",
]
