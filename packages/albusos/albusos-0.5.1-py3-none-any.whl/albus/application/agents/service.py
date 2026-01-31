"""AgentService - Unified agent registry and storage.

Programs as data: Agents are fully serializable, storable, and editable at runtime.

This mirrors PathwayService but for the Agent layer:
- In-memory registry for fast lookup
- Persistent storage via StudioStore
- Full CRUD operations
- Import/export support

API:
    service = AgentService(store=store)
    
    # Create agent at runtime
    meta = service.create(agent_data, source="user:studio")
    
    # Load any agent
    agent = service.load("support_agent")
    
    # List all agents
    agents = service.list()
    
    # Run agent turn
    result = await service.turn("support_agent", message="Hello", thread_id="conv_1", ctx=ctx)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pathway_engine.domain.agent.core import Agent
from pathway_engine.domain.agent.skill import Skill
from pathway_engine.domain.agent.cognitive import CognitiveStyle, ReasoningMode, OrationMode, SupervisionMode
from pathway_engine.domain.agent.capabilities import AgentCapabilities
from pathway_engine.domain.agent.memory import AgentMemoryConfig, MemoryScope

if TYPE_CHECKING:
    from persistence.infrastructure.storage.store import StudioStore
    from pathway_engine.domain.context import Context

logger = logging.getLogger(__name__)


@dataclass
class AgentMeta:
    """Metadata for a registered agent."""

    id: str
    name: str
    description: str | None
    source: str  # "user:studio", "import:file", "code:module"
    version: str | None = None
    doc_id: str | None = None
    skill_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "version": self.version,
            "doc_id": self.doc_id,
            "skill_count": self.skill_count,
        }


@dataclass
class AgentService:
    """Unified agent registry and storage.

    This is THE single source of truth for all agents in the system.
    Agents are programs-as-data: fully serializable and runtime-editable.
    """

    # In-memory registry (agent_id -> Agent)
    _registry: dict[str, Agent] = field(default_factory=dict)

    # Metadata for all registered agents
    _meta: dict[str, AgentMeta] = field(default_factory=dict)

    # Persistent storage
    _store: "StudioStore | None" = None

    # Reference to pathway service (for skill pathway resolution)
    _pathway_service: Any = None

    # Default workspace for persistence
    _default_workspace_id: str | None = None

    def __init__(
        self,
        *,
        store: "StudioStore | None" = None,
        pathway_service: Any = None,
        default_workspace_id: str | None = None,
    ):
        self._registry = {}
        self._meta = {}
        self._store = store
        self._pathway_service = pathway_service
        self._default_workspace_id = default_workspace_id

    # =========================================================================
    # CREATE (Runtime agent creation)
    # =========================================================================

    def create(
        self,
        agent_data: dict[str, Any],
        *,
        source: str = "user:unknown",
        workspace_id: str | None = None,
    ) -> AgentMeta:
        """Create an agent from data.

        Args:
            agent_data: Agent definition dict
            source: Origin identifier
            workspace_id: Workspace to store in

        Returns:
            AgentMeta with creation info
        """
        agent = self._agent_from_dict(agent_data)
        agent_id = agent.id

        # Persist if store available
        doc_id = None
        if self._store:
            ws_id = workspace_id or self._default_workspace_id
            if ws_id:
                doc_id = self._persist_agent(agent, source=source, workspace_id=ws_id)

        # Register in memory
        self._registry[agent_id] = agent
        if doc_id:
            self._registry[doc_id] = agent

        meta = AgentMeta(
            id=agent_id,
            name=agent.name,
            description=agent.persona[:100] if agent.persona else None,
            source=source,
            doc_id=doc_id,
            skill_count=len(agent._skills),
        )
        self._meta[agent_id] = meta
        if doc_id:
            self._meta[doc_id] = meta

        logger.info("Created agent: %s (source=%s)", agent_id, source)
        return meta

    def register(
        self,
        agent: Agent,
        *,
        source: str = "code:module",
    ) -> AgentMeta:
        """Register a code-defined agent.

        Use this for agents defined in Python code (like today's model).
        """
        agent_id = agent.id
        self._registry[agent_id] = agent

        meta = AgentMeta(
            id=agent_id,
            name=agent.name,
            description=agent.persona[:100] if agent.persona else None,
            source=source,
            skill_count=len(agent._skills),
        )
        self._meta[agent_id] = meta

        logger.debug("Registered agent: %s (source=%s)", agent_id, source)
        return meta

    # =========================================================================
    # LOAD
    # =========================================================================

    def load(self, agent_id: str) -> Agent | None:
        """Load an agent by ID.

        Checks:
        1. In-memory registry
        2. Persistent storage
        """
        # Check in-memory first
        agent = self._registry.get(agent_id)
        if agent is not None:
            return agent

        # Try loading from storage
        if self._store:
            agent = self._load_from_storage(agent_id)
            if agent:
                self._registry[agent_id] = agent
                return agent

        return None

    def get_meta(self, agent_id: str) -> AgentMeta | None:
        """Get metadata for an agent."""
        return self._meta.get(agent_id)

    # =========================================================================
    # LIST
    # =========================================================================

    def list(
        self,
        *,
        source_filter: str | None = None,
    ) -> list[AgentMeta]:
        """List all registered agents."""
        results = []
        seen_ids = set()

        for agent_id, meta in self._meta.items():
            if meta.id in seen_ids:
                continue
            seen_ids.add(meta.id)

            if source_filter and not meta.source.startswith(source_filter):
                continue

            results.append(meta)

        return results

    # =========================================================================
    # UPDATE
    # =========================================================================

    def update(
        self,
        agent_id: str,
        updates: dict[str, Any],
    ) -> AgentMeta:
        """Update an agent's configuration.

        Args:
            agent_id: Agent ID
            updates: Partial updates (name, persona, goals, cognitive_style, etc.)

        Returns:
            Updated AgentMeta

        Raises:
            ValueError: If agent not found
        """
        agent = self.load(agent_id)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")

        # Get current data
        current_data = agent.to_dict()

        # Merge updates
        if "name" in updates:
            current_data["name"] = updates["name"]
        if "persona" in updates:
            current_data["persona"] = updates["persona"]
        if "goals" in updates:
            current_data["goals"] = updates["goals"]
        if "cognitive_style" in updates:
            current_data["cognitive_style"] = updates["cognitive_style"]
        if "capabilities" in updates:
            current_data["capabilities"].update(updates["capabilities"])
        if "skills" in updates:
            current_data["skills"] = updates["skills"]
        if "bundles" in updates:
            current_data["bundles"] = updates["bundles"]

        # Rebuild agent
        new_agent = self._agent_from_dict(current_data)

        # Update registry
        self._registry[agent_id] = new_agent

        # Persist changes
        meta = self._meta.get(agent_id)
        if meta and meta.doc_id and self._store:
            self._persist_agent_changes(agent_id, new_agent)

        # Update meta
        if meta:
            meta.name = new_agent.name
            meta.description = new_agent.persona[:100] if new_agent.persona else None
            meta.skill_count = len(new_agent._skills)
            meta.bundle_count = len(new_agent._bundles)

        logger.info("Updated agent: %s", agent_id)
        return meta or self._meta[agent_id]

    # =========================================================================
    # DELETE
    # =========================================================================

    def delete(self, agent_id: str) -> bool:
        """Delete an agent."""
        if agent_id not in self._registry and agent_id not in self._meta:
            return False

        self._registry.pop(agent_id, None)
        meta = self._meta.pop(agent_id, None)

        # Remove from storage
        if meta and meta.doc_id and self._store:
            try:
                delete_fn = getattr(self._store, "delete_document", None)
                if callable(delete_fn):
                    delete_fn(meta.doc_id)
            except Exception as e:
                logger.warning("Failed to delete agent document: %s", e)

        logger.info("Deleted agent: %s", agent_id)
        return True

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def turn(
        self,
        agent_id: str,
        *,
        message: str,
        thread_id: str,
        ctx: "Context",
        attachments: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run an agent turn.

        Args:
            agent_id: Agent to run
            message: User message
            thread_id: Conversation thread
            ctx: Execution context
            attachments: Optional attachments
            context: Optional additional context

        Returns:
            Turn result dict
        """
        agent = self.load(agent_id)
        if agent is None:
            return {"error": f"Agent not found: {agent_id}", "success": False}

        return await agent.turn(
            message=message,
            thread_id=thread_id,
            ctx=ctx,
            attachments=attachments,
            context=context,
        )

    # =========================================================================
    # SKILL MANAGEMENT
    # =========================================================================

    def add_skill(
        self,
        agent_id: str,
        skill_data: dict[str, Any],
    ) -> tuple[Agent, Skill]:
        """Add a skill to an agent."""
        agent = self.load(agent_id)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")

        skill = self._skill_from_dict(skill_data)
        agent.add_skill(skill)

        # Persist
        self._persist_agent_changes(agent_id, agent)

        # Update meta
        if agent_id in self._meta:
            self._meta[agent_id].skill_count = len(agent._skills)

        return agent, skill

    def remove_skill(
        self,
        agent_id: str,
        skill_id: str,
    ) -> Agent:
        """Remove a skill from an agent."""
        agent = self.load(agent_id)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")

        if skill_id not in agent._skills:
            raise ValueError(f"Skill not found: {skill_id}")

        del agent._skills[skill_id]

        # Persist
        self._persist_agent_changes(agent_id, agent)

        # Update meta
        if agent_id in self._meta:
            self._meta[agent_id].skill_count = len(agent._skills)

        return agent

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def export(self, agent_id: str) -> dict[str, Any] | None:
        """Export an agent as a portable JSON document."""
        agent = self.load(agent_id)
        if agent is None:
            return None

        meta = self._meta.get(agent_id)

        return {
            "format": "albus.agent.v1",
            "agent": agent.to_dict(),
            "meta": meta.to_dict() if meta else None,
        }

    def import_agent(
        self,
        data: dict[str, Any],
        *,
        new_id: str | None = None,
        workspace_id: str | None = None,
    ) -> AgentMeta:
        """Import an agent from an export."""
        if data.get("format") != "albus.agent.v1":
            raise ValueError(f"Unsupported format: {data.get('format')}")

        agent_data = data.get("agent", {})
        if new_id:
            agent_data["id"] = new_id

        return self.create(
            agent_data,
            source=f"import:{data.get('meta', {}).get('source', 'unknown')}",
            workspace_id=workspace_id,
        )

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def _agent_from_dict(self, data: dict[str, Any]) -> Agent:
        """Create an Agent from a dictionary."""
        agent_id = data.get("id", f"agent_{uuid.uuid4().hex[:8]}")

        # Parse cognitive style
        cognitive_data = data.get("cognitive_style", {})
        cognitive_style = CognitiveStyle(
            reasoning=ReasoningMode(cognitive_data.get("reasoning", "reactive")),
            oration=OrationMode(cognitive_data.get("oration", "conversational")),
            supervision=SupervisionMode(cognitive_data.get("supervision", "collaborative")),
        )

        # Parse capabilities
        cap_data = data.get("capabilities", {})
        capabilities = AgentCapabilities(
            tools=cap_data.get("tools", []),
            max_steps_per_turn=cap_data.get("max_steps_per_turn", 10),
            model=cap_data.get("model", "auto"),  # "auto" uses capability routing
            temperature=cap_data.get("temperature", 0.7),
            model_overrides=dict(cap_data.get("model_overrides", {})),
        )

        # Parse memory config
        mem_data = data.get("memory", {})
        memory = AgentMemoryConfig(
            short_term=MemoryScope(mem_data.get("short_term", "thread")),
            long_term=MemoryScope(mem_data.get("long_term", "agent")),
            namespace=mem_data.get("namespace", agent_id),
        )

        # Create agent
        agent = Agent(
            id=agent_id,
            name=data.get("name", agent_id),
            persona=data.get("persona", ""),
            goals=data.get("goals", []),
            cognitive_style=cognitive_style,
            capabilities=capabilities,
            memory=memory,
        )

        # Add skills
        for skill_data in data.get("skills", []):
            skill = self._skill_from_dict(skill_data)
            agent.add_skill(skill)

        return agent

    def _skill_from_dict(self, data: dict[str, Any]) -> Skill:
        """Create a Skill from a dictionary."""
        skill_id = data.get("id", f"skill_{uuid.uuid4().hex[:6]}")

        # Resolve pathway builder if pathway_id specified
        pathway_builder = None
        pathway_id = data.get("pathway_id")
        if pathway_id and self._pathway_service:
            pathway_builder = self._pathway_service.resolve(pathway_id)

        return Skill(
            id=skill_id,
            name=data.get("name", skill_id),
            description=data.get("description", ""),
            pathway_builder=pathway_builder,
            inputs_schema=data.get("inputs_schema", {}),
            outputs_schema=data.get("outputs_schema", {}),
        )

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _persist_agent(
        self,
        agent: Agent,
        *,
        source: str,
        workspace_id: str,
    ) -> str | None:
        """Persist an agent to storage."""
        if not self._store:
            return None

        # Ensure workspace exists
        try:
            ws = self._store.get_workspace(workspace_id)
            if not ws:
                self._store.upsert_workspace({
                    "id": workspace_id,
                    "name": f"Agents ({workspace_id})",
                })
        except Exception as e:
            logger.warning("Failed to ensure workspace: %s", e)

        doc_id = f"agent_{uuid.uuid4().hex[:12]}"

        try:
            # Create document
            self._store.upsert_document({
                "id": doc_id,
                "type": "agent",
                "name": agent.name,
                "workspace_id": workspace_id,
                "parent_id": None,
                "metadata": {
                    "agent_id": agent.id,
                    "source": source,
                },
                "head_rev": None,
            })

            # Write content as revision
            content = agent.to_dict()
            content["source"] = source

            rev_id = f"rev_{uuid.uuid4().hex[:12]}"
            self._store.write_revision(doc_id=doc_id, rev_id=rev_id, content=content)
            self._store.upsert_document({"id": doc_id, "head_rev": rev_id})

            return doc_id

        except Exception as e:
            logger.error("Failed to persist agent: %s", e)
            return None

    def _load_from_storage(self, agent_id: str) -> Agent | None:
        """Load an agent from storage."""
        if not self._store:
            return None

        # Try as doc_id first
        doc = self._store.get_document(agent_id)
        if doc and doc.get("type") == "agent":
            return self._load_doc_agent(agent_id)

        # Search by agent_id in metadata
        try:
            all_docs = self._store.list_documents(workspace_id=None)
            for doc in all_docs:
                if doc.get("type") != "agent":
                    continue
                meta = doc.get("metadata", {})
                if meta.get("agent_id") == agent_id:
                    return self._load_doc_agent(doc.get("id"))
        except Exception as e:
            logger.debug("Failed to search agents: %s", e)

        return None

    def _load_doc_agent(self, doc_id: str) -> Agent | None:
        """Load an agent from a document."""
        if not self._store:
            return None

        try:
            doc = self._store.get_document(doc_id)
            if not doc:
                return None

            head_rev = doc.get("head_rev")
            if not head_rev:
                return None

            rev = self._store.get_revision(doc_id=doc_id, rev_id=head_rev)
            if not rev:
                return None

            content = rev.get("content", {})
            return self._agent_from_dict(content)

        except Exception as e:
            logger.error("Failed to load agent %s: %s", doc_id, e)
            return None

    def _persist_agent_changes(self, agent_id: str, agent: Agent) -> None:
        """Persist agent changes to storage."""
        if not self._store:
            return

        meta = self._meta.get(agent_id)
        doc_id = meta.doc_id if meta else None

        if not doc_id:
            return

        try:
            content = agent.to_dict()
            content["source"] = meta.source if meta else "user:api"

            rev_id = f"rev_{uuid.uuid4().hex[:12]}"
            self._store.write_revision(doc_id=doc_id, rev_id=rev_id, content=content)
            self._store.upsert_document({
                "id": doc_id,
                "head_rev": rev_id,
                "name": agent.name,
            })

        except Exception as e:
            logger.error("Failed to persist agent changes: %s", e)


__all__ = [
    "AgentService",
    "AgentMeta",
]

