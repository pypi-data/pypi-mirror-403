"""AlbusRuntime - The Albus agent runtime.

This is the main entry point for running Albus OS. It:
- Wires together state machines, pathway execution, persistence, observability
- Exposes a transport-facing interface (threads, events, subscriptions)

Chat is intentionally *not* a first-class surface area here; it's a dev concern
and should not shape the architecture.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from albus.application.pathways import PathwayService
from albus.application.agents import AgentService
from albus.application.state_machine import (
    StateMachineController,
    register_builtin_state_machines,
)
from pathway_engine.domain.schemas.context import ContextBudgetV1
from albus.infrastructure.repositories import ThreadRepository, StateMachineRepository
from albus.infrastructure.observability import EventEmitter
from albus.infrastructure.observability.pathway_vm_bridge import (
    attach_pathway_vm_observability,
)

if TYPE_CHECKING:
    from pathway_engine.application.kernel import PathwayVM
    from persistence.ports import ThreadStorePort
    from persistence.application.ports import StudioStore

logger = logging.getLogger(__name__)


class AlbusRuntime:
    """The Albus agent runtime.

    This is the top-level entry point. Transport layers interact with this.

    Architecture:
        Transport → AlbusRuntime → Controllers → Domain

    Components:
        - events: EventEmitter for observability
        - threads: ThreadRepository for thread persistence
        - state_machines: StateMachineRepository for state machine definitions
        - state_machine_controller: StateMachineController for execution
        - pathway_service: PathwayService for pathway registry and storage
    """

    def __init__(
        self,
        *,
        events: EventEmitter,
        threads: ThreadRepository,
        state_machines: StateMachineRepository,
        state_machine_controller: StateMachineController,
        pathway_vm: "PathwayVM",
        pathway_service: "PathwayService",
        agent_service: "AgentService",
    ):
        """Create runtime with injected dependencies.

        Prefer using AlbusRuntime.create() for standard setup.
        """
        self.events = events
        self.threads = threads
        self.state_machines = state_machines
        self.state_machine_controller = state_machine_controller
        self._pathway_vm = pathway_vm
        self.pathway_service = pathway_service
        self.agent_service = agent_service

    @property
    def pathway_vm(self) -> "PathwayVM":
        """Access the PathwayVM used by this runtime."""
        return self._pathway_vm

    @classmethod
    def create(
        cls,
        *,
        pathway_vm: "PathwayVM",
        thread_store: "ThreadStorePort | None" = None,
        studio_store: "StudioStore | None" = None,
        pathway_service: "PathwayService | None" = None,
        debug: bool = False,
    ) -> "AlbusRuntime":
        """Create runtime with standard wiring.

        This is the recommended way to create an AlbusRuntime.

        Args:
            pathway_vm: PathwayVM for executing pathways
            thread_store: Optional persistent storage for threads
            studio_store: Optional studio store for state machines
            pathway_service: Optional PathwayService (creates default if not provided)
            debug: Enable debug logging

        Returns:
            Configured AlbusRuntime ready for use
        """
        # Create PathwayService if not provided
        if pathway_service is None:
            store = studio_store
            if store is None:
                try:
                    domain = pathway_vm.ctx.services.domain
                    if domain is not None:
                        store = getattr(domain, "_store", None)
                except Exception:
                    logger.debug(
                        "Failed to infer Studio store from VM domain", exc_info=True
                    )
            pathway_service = PathwayService(store=store)

        # Event emitter for observability
        events = EventEmitter()
        if debug:
            from albus.infrastructure.observability import DebugHandler

            handler = DebugHandler(show_timestamps=True)
            events.on_all(handler)

        # Best-effort: persist event stream as Studio run logs when a store is available.
        try:
            from albus.infrastructure.observability.run_recorder import RunRecorder

            store = studio_store
            if store is None:
                try:
                    # Prefer explicit domain wiring when present.
                    domain = pathway_vm.ctx.services.domain
                    if domain is not None:
                        store = getattr(domain, "_store", None)
                except Exception:
                    store = None
            # As a final fallback, PathwayService may hold a store reference.
            if store is None and pathway_service is not None:
                store = getattr(pathway_service, "_store", None)

            if (
                store is not None
                and callable(getattr(store, "append_run_event", None))
                and callable(getattr(store, "upsert_run_summary", None))
            ):
                events.on_all(RunRecorder(store=store).on_event)
        except Exception:
            logger.debug("Failed to attach RunRecorder (non-fatal)", exc_info=True)

        # Register model routing defaults
        try:
            from pathway_engine.domain.model_routing import set_model_router
            from stdlib.llm.capability_routing import (
                get_model_for_capability,
                set_runtime_model_config,
            )

            def _router(capability: str) -> str | None:
                return get_model_for_capability(capability)

            set_model_router(_router)
        except Exception:
            logger.debug("Failed to register model router defaults", exc_info=True)

        # Bridge PathwayVM events → Albus events
        try:
            attach_pathway_vm_observability(vm=pathway_vm, events=events)
        except Exception as e:
            logger.warning("Failed to attach PathwayVM observability: %s", e)

        # Default context budget
        try:
            if pathway_vm.ctx.services.context_budget is None:
                pathway_vm.ctx.services.context_budget = ContextBudgetV1()
        except Exception:
            logger.debug("Failed to set default context budget", exc_info=True)

        # Thread repository
        threads = ThreadRepository(store=thread_store)

        # Register Host pathways (must be before state machine setup)
        from albus.application.state_machine.host_pathways import register_host_pathways
        from albus.application.state_machine.intent_router import register_intent_pathways
        register_host_pathways(pathway_service)
        register_intent_pathways(pathway_service)

        # Agent service (Host is pre-registered)
        agent_service = AgentService(
            pathway_service=pathway_service,
            pathway_vm=pathway_vm,
        )
        
        # Skills loading is now handled in server.py as a background task
        # This ensures non-blocking startup - server starts immediately
        # Skills load in background and become available shortly after

        # State machine repository (with built-in state machines)
        state_machines = StateMachineRepository(store=studio_store)
        register_builtin_state_machines(state_machines)

        # State machine controller
        state_machine_controller = StateMachineController(
            state_machine_repo=state_machines,
            pathway_service=pathway_service,
            pathway_vm=pathway_vm,
            events=events,
        )

        logger.info("AlbusRuntime created (state machines + agents enabled)")

        return cls(
            events=events,
            threads=threads,
            state_machines=state_machines,
            state_machine_controller=state_machine_controller,
            pathway_vm=pathway_vm,
            pathway_service=pathway_service,
            agent_service=agent_service,
        )

    def apply_model_config(
        self,
        *,
        default_profile: str | None = None,
        routing: dict[str, str] | None = None,
    ) -> None:
        """Apply model routing config from deployment config.

        Called by server after loading albus.yaml to set model routing policy.

        Args:
            default_profile: Battery pack to use ("local", "balanced", etc.)
            routing: Capability → model overrides
        """
        try:
            from stdlib.llm.capability_routing import set_runtime_model_config

            set_runtime_model_config(
                default_profile=default_profile,
                routing=routing,
            )
        except Exception as e:
            logger.warning("Failed to apply model config: %s", e)

    async def send_event(
        self,
        *,
        thread_id: str,
        event: str,
        payload: dict[str, Any] | None = None,
        state_machine_id: str = "host.v1",
    ) -> dict[str, Any]:
        """Send an event to an agent instance.

        This allows sending arbitrary events (not just user messages)
        to trigger state machine transitions.

        If the thread doesn't exist, it's auto-created with the specified state machine.

        Args:
            thread_id: Thread/agent instance ID
            event: Event type (e.g., "task", "timeout", "approval_granted")
            payload: Event payload data
            state_machine_id: State machine to use (default: host.v1)

        Returns:
            TransitionResult as dict
        """
        from albus.domain.world.thread import AgentInstance, AgentContext
        
        instance = await self.threads.get(thread_id)
        if instance is None:
            # Auto-create thread with specified state machine
            state_machine = self.state_machines.get(state_machine_id)
            if state_machine is None:
                return {"success": False, "error": f"State machine not found: {state_machine_id}"}
            
            instance = AgentInstance(
                id=thread_id,
                state_machine_id=state_machine_id,
                current_state=state_machine.initial_state,
                context=AgentContext(data=dict(state_machine.initial_context)),
            )
            await self.threads.save(instance)

        result = await self.state_machine_controller.process_event(
            instance=instance,
            event=event,
            payload=payload,
        )

        all_emitted = list(result.emitted_events)
        final_state = result.to_state
        
        # Auto-process emitted events (chain reactions)
        while result.emitted_events and result.success:
            next_event = result.emitted_events[0]
            logger.info("Auto-processing emitted event: %s", next_event)
            
            # Process the emitted event (with entry pathway result as payload)
            entry_result = result.entry_pathway_result or {}
            result = await self.state_machine_controller.process_event(
                instance=instance,
                event=next_event,
                payload=entry_result,
            )
            
            final_state = result.to_state or final_state
            all_emitted.extend(result.emitted_events)

        # Save updated instance
        await self.threads.save(instance)

        return {
            "success": result.success,
            "from_state": result.from_state,
            "to_state": final_state,
            "error": result.error,
            "emitted_events": all_emitted,
        }

    # =========================================================================
    # Thread management
    # =========================================================================

    async def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        """Get thread information."""
        instance = await self.threads.get(thread_id)
        if instance is None:
            return None

        return {
            "thread_id": thread_id,
            "state_machine_id": instance.state_machine_id,
            "current_state": instance.current_state,
            "status": instance.status.value,
            "message_count": len(instance.context.messages),
            "transition_count": instance.context.transition_count,
            "created_at": (
                instance.created_at.isoformat() if instance.created_at else None
            ),
            "updated_at": (
                instance.updated_at.isoformat() if instance.updated_at else None
            ),
            "workspace_id": instance.workspace_id,
        }

    async def list_threads(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List threads."""
        instances = await self.threads.list(workspace_id=workspace_id, limit=limit)
        return [
            {
                "thread_id": inst.context.data.get("thread_id") or inst.id,
                "state_machine_id": inst.state_machine_id,
                "current_state": inst.current_state,
                "status": inst.status.value,
                "message_count": len(inst.context.messages),
                "created_at": inst.created_at.isoformat() if inst.created_at else None,
                "workspace_id": inst.workspace_id,
            }
            for inst in instances
        ]

    async def end_thread(self, thread_id: str) -> bool:
        """End/delete a thread."""
        return await self.threads.delete(thread_id)

    # =========================================================================
    # State machine management
    # =========================================================================

    def list_state_machines(self) -> list[dict[str, Any]]:
        """List available state machines."""
        return [
            {
                "id": sm.id,
                "name": sm.name,
                "description": sm.description,
                "version": sm.version,
                "initial_state": sm.initial_state,
                "state_count": len(sm.states),
                "event_count": len(sm.events),
                "transition_count": len(sm.transitions),
            }
            for sm in self.state_machines.list()
        ]

    def get_state_machine(self, state_machine_id: str) -> dict[str, Any] | None:
        """Get a state machine definition."""
        sm = self.state_machines.get(state_machine_id)
        if sm is None:
            return None
        return sm.model_dump()

    # =========================================================================
    # Event subscription (for streaming/observability)
    # =========================================================================

    def on(self, event_type: str, handler: Any) -> None:
        """Subscribe to events."""
        self.events.on(event_type, handler)

    def off(self, event_type: str, handler: Any) -> None:
        """Unsubscribe from events."""
        self.events.off(event_type, handler)

    def on_all(self, handler: Any) -> None:
        """Subscribe to ALL events."""
        self.events.on_all(handler)

    def off_all(self, handler: Any) -> None:
        """Unsubscribe from ALL events."""
        self.events.off_all(handler)


__all__ = [
    "AlbusRuntime",
]
