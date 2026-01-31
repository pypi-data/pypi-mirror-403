"""State Machine execution - the brain that runs agents.

This module contains:
- StateMachineController: Processes events and executes transitions
- Built-in state machines for common patterns
"""

from albus.application.state_machine.controller import (
    StateMachineController,
    TransitionResult,
)
from albus.application.state_machine.builtin import (
    WORKFLOW_STATE_MACHINE,
    ALL_BUILTIN_STATE_MACHINES,
    register_builtin_state_machines,
)

__all__ = [
    "StateMachineController",
    "TransitionResult",
    "WORKFLOW_STATE_MACHINE",
    "ALL_BUILTIN_STATE_MACHINES",
    "register_builtin_state_machines",
]
