"""StateMachineController - The brain that runs agents.

This is the core executor that:
1. Receives events
2. Finds matching transitions
3. Evaluates guards
4. Executes pathways (exit → action → entry)
5. Updates agent state
6. Handles auto-events (emit_event_on_complete)

The controller is the bridge between events and pathway execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from shared_types.expressions import safe_eval_bool

from albus.domain.runs.state_machine import (
    AgentState,
    AgentTransition,
    StateMachine,
)
from albus.domain.world.thread import AgentInstance, AgentInstanceStatus

if TYPE_CHECKING:
    from albus.application.pathways import PathwayService
    from albus.infrastructure.repositories.state_machine_repository import (
        StateMachineRepository,
    )
    from albus.infrastructure.observability import EventEmitter
    from pathway_engine.application.kernel import PathwayVM

logger = logging.getLogger(__name__)


@dataclass
class TransitionResult:
    """Result of processing an event through the state machine."""

    success: bool
    from_state: str
    to_state: str | None = None
    transition: AgentTransition | None = None

    # Pathway execution results
    exit_pathway_result: dict[str, Any] | None = None
    action_pathway_result: dict[str, Any] | None = None
    entry_pathway_result: dict[str, Any] | None = None

    # Error info
    error: str | None = None

    # Auto-emitted events (for chaining)
    emitted_events: list[str] = field(default_factory=list)


class StateMachineController:
    """Controller that executes state machines.

    The controller is responsible for:
    - Loading state machine definitions
    - Processing events against the current state
    - Executing pathways in the correct order
    - Updating agent instance state
    - Emitting observability events

    Usage:
        controller = StateMachineController(
            state_machine_repo=repo,
            pathway_service=service,
            pathway_vm=vm,
        )

        result = await controller.process_event(
            instance=agent_instance,
            event="user_message",
            payload={"message": "hello"},
        )
    """

    def __init__(
        self,
        *,
        state_machine_repo: "StateMachineRepository",
        pathway_service: "PathwayService",
        pathway_vm: "PathwayVM",
        events: "EventEmitter | None" = None,
    ):
        self._sm_repo = state_machine_repo
        self._pathway_service = pathway_service
        self._vm = pathway_vm
        self._events = events

    async def process_event(
        self,
        instance: AgentInstance,
        event: str,
        payload: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """Process an event for an agent instance.

        This is the main entry point. It:
        1. Loads the state machine
        2. Finds matching transitions
        3. Evaluates guards
        4. Executes the transition (pathways)
        5. Updates instance state

        Args:
            instance: The agent instance to process
            event: Event type (e.g., "user_message", "timeout")
            payload: Event payload data

        Returns:
            TransitionResult with execution details
        """
        payload = payload or {}
        current_state = instance.current_state

        # 1. Load state machine
        state_machine = self._sm_repo.get(instance.state_machine_id)
        if state_machine is None:
            return TransitionResult(
                success=False,
                from_state=current_state,
                error=f"State machine not found: {instance.state_machine_id}",
            )

        # 2. Find matching transitions
        candidates = self._find_matching_transitions(
            state_machine=state_machine,
            current_state=current_state,
            event=event,
            context=self._build_eval_context(instance, payload),
        )

        if not candidates:
            # No matching transition - stay in current state
            logger.debug(
                "No transition for state=%s event=%s (instance=%s)",
                current_state,
                event,
                instance.id,
            )
            return TransitionResult(
                success=True,  # Not an error, just no transition
                from_state=current_state,
                to_state=current_state,
            )

        # 3. Select transition (uses weights/priority)
        transition = state_machine.select_from_candidates(
            candidates,
            exploration_rate=(
                getattr(state_machine.learning, "exploration_rate", 0.0)
                if state_machine.learning
                else 0.0
            ),
        )

        if transition is None:
            return TransitionResult(
                success=True,
                from_state=current_state,
                to_state=current_state,
            )

        # 4. Execute the transition
        result = await self._execute_transition(
            instance=instance,
            state_machine=state_machine,
            transition=transition,
            payload=payload,
        )

        return result

    def _find_matching_transitions(
        self,
        state_machine: StateMachine,
        current_state: str,
        event: str,
        context: dict[str, Any],
    ) -> list[AgentTransition]:
        """Find all transitions matching state + event with passing guards."""
        candidates = []

        for transition in state_machine.transitions:
            # Match state and event
            if transition.from_state != current_state:
                continue
            if transition.event != event:
                continue

            # Evaluate guard (if present)
            if transition.guard:
                try:
                    if not safe_eval_bool(transition.guard, context):
                        continue
                except Exception as e:
                    logger.warning(
                        "Guard evaluation failed for %s→%s: %s",
                        transition.from_state,
                        transition.to_state,
                        e,
                    )
                    continue

            candidates.append(transition)

        return candidates

    def _build_eval_context(
        self,
        instance: AgentInstance,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Build context for guard evaluation."""
        return {
            # Payload data
            **payload,
            # Agent context
            "context": instance.context.data,
            "messages": instance.context.messages,
            "current_state": instance.current_state,
            "status": instance.status.value,
            "workspace_id": instance.workspace_id,
            "thread_id": instance.context.data.get("thread_id"),
            # Convenience
            "message_count": len(instance.context.messages),
        }

    async def _execute_transition(
        self,
        instance: AgentInstance,
        state_machine: StateMachine,
        transition: AgentTransition,
        payload: dict[str, Any],
    ) -> TransitionResult:
        """Execute a state transition.

        Order:
        1. Execute exit_pathway of current state
        2. Execute action_pathway of transition
        3. Update state
        4. Execute entry_pathway of new state
        5. Handle emit_event_on_complete
        """
        from_state = instance.current_state
        to_state = transition.to_state

        result = TransitionResult(
            success=True,
            from_state=from_state,
            to_state=to_state,
            transition=transition,
        )

        # Build execution payload
        exec_payload = {
            **payload,
            "from_state": from_state,
            "to_state": to_state,
            "event": transition.event,
            "context": instance.context.data,
            "messages": instance.context.messages,
            "chat_history": instance.context.messages,
            "workspace_id": instance.workspace_id,
            "thread_id": instance.context.data.get("thread_id"),
        }

        try:
            # 1. Exit pathway (current state)
            current_state_def = state_machine.states.get(from_state)
            if current_state_def and current_state_def.exit_pathway:
                exit_result = await self._execute_pathway(
                    current_state_def.exit_pathway,
                    exec_payload,
                )
                result.exit_pathway_result = exit_result
                if exit_result and exit_result.get("error"):
                    result.success = False
                    result.error = f"Exit pathway failed: {exit_result['error']}"
                    return result

            # 2. Action pathway (transition)
            if transition.action_pathway:
                action_result = await self._execute_pathway(
                    transition.action_pathway,
                    exec_payload,
                )
                result.action_pathway_result = action_result
                if action_result and action_result.get("error"):
                    result.success = False
                    result.error = f"Action pathway failed: {action_result['error']}"
                    return result

            # 3. Update state
            instance.current_state = to_state
            instance.context.last_event = transition.event
            instance.context.last_event_at = datetime.utcnow()
            instance.context.transition_count += 1
            instance.updated_at = datetime.utcnow()

            # 4. Entry pathway (new state)
            new_state_def = state_machine.states.get(to_state)
            if new_state_def and new_state_def.entry_pathway:
                entry_result = await self._execute_pathway(
                    new_state_def.entry_pathway,
                    exec_payload,
                )
                result.entry_pathway_result = entry_result
                if entry_result and entry_result.get("error"):
                    result.success = False
                    result.error = f"Entry pathway failed: {entry_result['error']}"
                    return result

            # 5. Handle emit_event_on_complete
            if new_state_def and new_state_def.emit_event_on_complete:
                result.emitted_events.append(new_state_def.emit_event_on_complete)

            # 6. Check for terminal state
            if new_state_def and new_state_def.is_terminal:
                instance.status = AgentInstanceStatus.TERMINATED

            logger.info(
                "Transition: %s → %s (event=%s, instance=%s)",
                from_state,
                to_state,
                transition.event,
                instance.id,
            )

        except Exception as e:
            logger.exception("Transition execution failed: %s", e)
            result.success = False
            result.error = str(e)
            instance.error = str(e)
            instance.error_count += 1

        return result

    async def _execute_pathway(
        self,
        pathway_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a pathway and return results."""
        try:
            pathway = self._pathway_service.load(pathway_id)
            if pathway is None:
                return {"error": f"Pathway not found: {pathway_id}"}

            # Keep a stable execution_id when invoked as part of a turn.
            execution_id = str(payload.get("turn_id") or "").strip() or None
            record = await self._vm.execute(pathway, payload, execution_id=execution_id)

            return {
                "success": record.success,
                "outputs": record.outputs,
                "error": record.error if not record.success else None,
            }
        except Exception as e:
            logger.exception("Pathway execution failed: %s", e)
            return {"error": str(e)}

    async def spawn_instance(
        self,
        state_machine_id: str,
        instance_id: str,
        *,
        workspace_id: str | None = None,
        initial_context: dict[str, Any] | None = None,
    ) -> AgentInstance:
        """Spawn a new agent instance.

        Creates an instance in the initial state of the state machine.
        """
        state_machine = self._sm_repo.get(state_machine_id)
        if state_machine is None:
            raise ValueError(f"State machine not found: {state_machine_id}")

        # Merge initial contexts
        context_data = dict(state_machine.initial_context)
        if initial_context:
            context_data.update(initial_context)

        from albus.domain.world.thread import AgentContext

        instance = AgentInstance(
            id=instance_id,
            state_machine_id=state_machine_id,
            current_state=state_machine.initial_state,
            status=AgentInstanceStatus.RUNNING,
            workspace_id=workspace_id,
            context=AgentContext(data=context_data),
        )

        logger.info(
            "Spawned instance %s (state_machine=%s, initial_state=%s)",
            instance_id,
            state_machine_id,
            state_machine.initial_state,
        )

        return instance


__all__ = ["StateMachineController", "TransitionResult"]
