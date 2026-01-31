"""StateMachineRepository - Store and retrieve state machine definitions.

State machines can come from:
1. Built-in definitions (registered at startup)
2. Persistent storage (user-created state machines)

The repository provides a unified interface regardless of source.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from albus.domain.runs.state_machine import StateMachine

if TYPE_CHECKING:
    from persistence.application.ports import StudioStore

logger = logging.getLogger(__name__)


class StateMachineRepository:
    """Repository for state machine definitions.

    Usage:
        repo = StateMachineRepository()

        # Register built-in state machines
        repo.register(chat_state_machine)

        # Get by ID
        sm = repo.get("chat.turn.v1")

        # List all
        all_machines = repo.list()
    """

    def __init__(
        self,
        *,
        store: "StudioStore | None" = None,
    ):
        """Create repository.

        Args:
            store: Optional persistence store for user state machines.
        """
        self._store = store
        self._builtin: dict[str, StateMachine] = {}

    def register(self, state_machine: StateMachine) -> None:
        """Register a built-in state machine.

        Built-in machines are available immediately without persistence.
        """
        self._builtin[state_machine.id] = state_machine
        logger.debug("Registered state machine: %s", state_machine.id)

    def get(self, state_machine_id: str) -> StateMachine | None:
        """Get a state machine by ID.

        Checks built-in first, then persistence.
        """
        # Check built-in
        if state_machine_id in self._builtin:
            return self._builtin[state_machine_id]

        # Check persistence
        if self._store is not None:
            try:
                doc = self._store.get_document(state_machine_id)
                if doc is not None and doc.get("type") == "state_machine":
                    content = doc.get("content", {})
                    if isinstance(content, dict):
                        return StateMachine.model_validate(content)
            except Exception as e:
                logger.warning(
                    "Failed to load state machine %s: %s", state_machine_id, e
                )

        return None

    def save(self, state_machine: StateMachine) -> None:
        """Save a state machine to persistence.

        Note: Built-in machines are not saved; they're registered.
        """
        if self._store is None:
            raise RuntimeError("No persistence store configured")

        self._store.upsert_document(
            {
                "id": state_machine.id,
                "type": "state_machine",
                "name": state_machine.name,
                "content": state_machine.model_dump(),
            }
        )
        logger.info("Saved state machine: %s", state_machine.id)

    def list(self) -> list[StateMachine]:
        """List all available state machines."""
        result = list(self._builtin.values())

        if self._store is not None:
            try:
                docs = self._store.list_documents()
                for doc in docs:
                    if doc.get("type") == "state_machine":
                        sm_id = doc.get("id")
                        if sm_id and sm_id not in self._builtin:
                            content = doc.get("content", {})
                            if isinstance(content, dict):
                                try:
                                    result.append(StateMachine.model_validate(content))
                                except Exception:
                                    pass
            except Exception as e:
                logger.warning("Failed to list state machines from store: %s", e)

        return result

    def exists(self, state_machine_id: str) -> bool:
        """Check if a state machine exists."""
        return self.get(state_machine_id) is not None


__all__ = ["StateMachineRepository"]
