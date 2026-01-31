"""Pack - Declarative pack manifest for event-driven pathways.

A pack declares EVERYTHING - the runtime provides the wiring.

Pack Schema:
    - id: Unique pack identifier
    - name: Human-readable name
    - version: Semantic version
    - requires: MCP and tool dependencies
    - triggers: Event sources that invoke pathways
    - actions: Output declarations routed by runtime
    - pathways: Exported pathway IDs

Example:
    pack = Pack(
        id="my_pack",
        name="My Pack",
        version="1.0.0",
        requires=PackRequirements(
            mcps=[MCPRequirement(id="gmail", required=True)],
        ),
        triggers=[
            Trigger(
                id="inbox_watch",
                source="mcp.gmail",
                event="message_received",
                filter={"labels": ["INBOX"]},
                pathway="my_pack.inbox_router.v1",
            ),
            Trigger(
                id="daily_batch",
                source="timer",
                schedule="0 9 * * *",
                pathway="my_pack.daily_task.v1",
            ),
        ],
        actions={
            "reply": ActionDeclaration(
                description="Reply to the original message",
                dispatch="original_channel",  # Special: uses trigger context
            ),
            "notify": ActionDeclaration(
                description="Send notification",
                dispatch="mcp.slack.send",
                defaults={"channel": "#alerts"},
            ),
        },
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from pathway_engine.domain.pathway import Pathway


class TriggerSource(Enum):
    """Supported trigger source types."""

    MCP = "mcp"  # MCP resource subscription
    TIMER = "timer"  # Cron-based scheduler
    WEBHOOK = "webhook"  # HTTP webhook endpoint
    MANUAL = "manual"  # API-invoked (always available)
    EVENT_BUS = "event"  # Internal event bus subscription


@dataclass
class MCPRequirement:
    """MCP server dependency declaration."""

    id: str  # MCP server ID (e.g., "gmail", "slack")
    required: bool = True  # Pack fails to load if MCP unavailable
    description: str | None = None  # Why this MCP is needed

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "required": self.required,
            "description": self.description,
        }


@dataclass
class ToolRequirement:
    """Tool dependency declaration."""

    name: str  # Tool name (e.g., "llm.generate")
    required: bool = True  # Pack fails to load if tool unavailable

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "required": self.required}


@dataclass
class PackRequirements:
    """Pack dependencies - MCPs, tools, and features."""

    mcps: list[MCPRequirement] = field(default_factory=list)
    tools: list[ToolRequirement] = field(default_factory=list)
    features: list[str] = field(
        default_factory=list
    )  # e.g., ["streaming", "code_sandbox"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mcps": [m.to_dict() for m in self.mcps],
            "tools": [t.to_dict() for t in self.tools],
            "features": self.features,
        }


@dataclass
class Trigger:
    """Event trigger that starts a pathway.

    The runtime reads triggers and wires them to event sources.

    Attributes:
        id: Unique trigger ID within the pack
        source: Event source type and identifier:
            - "mcp.<server_id>" → Subscribe to MCP resource events
            - "timer" → Cron-scheduled trigger
            - "webhook" → HTTP POST to /triggers/{pack}/{trigger_id}
            - "event.<channel>" → Internal event bus subscription
            - "manual" → API-invoked only
        event: Event type for MCP sources (e.g., "message_received")
        filter: Optional filter criteria (source-specific)
        schedule: Cron expression for timer triggers
        pathway: Pathway ID to invoke when trigger fires
        inputs_map: Template mapping to transform event → pathway inputs
        enabled: Whether this trigger is active
    """

    id: str
    source: str  # "mcp.gmail", "timer", "webhook", etc.
    pathway: str  # Pathway ID to invoke
    event: str | None = None  # Event type for MCP/event sources
    filter: dict[str, Any] = field(default_factory=dict)
    schedule: str | None = None  # Cron for timer triggers
    inputs_map: dict[str, str] = field(default_factory=dict)  # event → inputs template
    enabled: bool = True
    description: str | None = None

    @property
    def source_type(self) -> TriggerSource:
        """Parse the trigger source type."""
        if self.source.startswith("mcp."):
            return TriggerSource.MCP
        elif self.source == "timer":
            return TriggerSource.TIMER
        elif self.source == "webhook":
            return TriggerSource.WEBHOOK
        elif self.source.startswith("event."):
            return TriggerSource.EVENT_BUS
        elif self.source == "manual":
            return TriggerSource.MANUAL
        else:
            return TriggerSource.MANUAL  # Default to manual

    @property
    def mcp_server_id(self) -> str | None:
        """Extract MCP server ID if source is mcp.*"""
        if self.source.startswith("mcp."):
            return self.source.split(".", 1)[1]
        return None

    @property
    def event_channel(self) -> str | None:
        """Extract event channel if source is event.*"""
        if self.source.startswith("event."):
            return self.source.split(".", 1)[1]
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "event": self.event,
            "filter": self.filter,
            "schedule": self.schedule,
            "pathway": self.pathway,
            "inputs_map": self.inputs_map,
            "enabled": self.enabled,
            "description": self.description,
        }


@dataclass
class ActionDeclaration:
    """Action output declaration - pathways declare intent, runtime routes.

    This is the contract between pathways and the runtime's action dispatcher.

    Attributes:
        description: What this action does
        dispatch: Where to send the action:
            - "original_channel" → Reply via trigger context
            - "mcp.<server>.<method>" → Call MCP tool
            - "webhook.<topic>" → Publish to webhook
            - "event.<channel>" → Publish to internal event bus
        defaults: Default values merged with action payload
        schema: Optional JSON Schema for payload validation
    """

    description: str = ""
    dispatch: str = "original_channel"  # Where to route
    defaults: dict[str, Any] = field(default_factory=dict)
    schema: dict[str, Any] | None = None  # Payload JSON Schema

    @property
    def dispatch_type(self) -> str:
        """Extract dispatch type (mcp, webhook, event, original_channel)."""
        if self.dispatch == "original_channel":
            return "original_channel"
        elif self.dispatch.startswith("mcp."):
            return "mcp"
        elif self.dispatch.startswith("webhook."):
            return "webhook"
        elif self.dispatch.startswith("event."):
            return "event"
        else:
            return "custom"

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "dispatch": self.dispatch,
            "defaults": self.defaults,
            "schema": self.schema,
        }


@dataclass
class Pack:
    """Pack manifest - the complete declaration of an event-driven pack.

    Packs declare:
    - What they need (requires)
    - What triggers them (triggers)
    - What actions they emit (actions)
    - What pathways they export (pathways)
    The runtime provides:
    - MCP connections
    - Event wiring
    - Action dispatch
    - Pathway execution
    """

    # Identity
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""

    # Dependencies
    requires: PackRequirements = field(default_factory=PackRequirements)

    # Event triggers (source → pathway)
    triggers: list[Trigger] = field(default_factory=list)

    # Action declarations (pathway → output)
    actions: dict[str, ActionDeclaration] = field(default_factory=dict)

    # Pathway registry (id → builder)
    _pathways: dict[str, Callable[[], "Pathway"]] = field(default_factory=dict)

    # Metadata
    author: str | None = None
    license: str | None = None
    homepage: str | None = None
    tags: list[str] = field(default_factory=list)

    def get_pathways(self) -> dict[str, Callable[[], "Pathway"]]:
        """Return all pathway builders."""
        return dict(self._pathways)

    def register_pathway(
        self,
        pathway_id: str,
        builder: Callable[[], "Pathway"],
    ) -> None:
        """Register a pathway builder."""
        self._pathways[pathway_id] = builder

    def get_trigger(self, trigger_id: str) -> Trigger | None:
        """Get a trigger by ID."""
        for trigger in self.triggers:
            if trigger.id == trigger_id:
                return trigger
        return None

    def get_action(self, action_id: str) -> ActionDeclaration | None:
        """Get an action declaration by ID."""
        return self.actions.get(action_id)

    def list_trigger_ids(self) -> list[str]:
        """List all trigger IDs."""
        return [t.id for t in self.triggers]

    def list_action_ids(self) -> list[str]:
        """List all action IDs."""
        return list(self.actions.keys())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (for pack.yaml export)."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "homepage": self.homepage,
            "tags": self.tags,
            "requires": self.requires.to_dict(),
            "triggers": [t.to_dict() for t in self.triggers],
            "actions": {k: v.to_dict() for k, v in self.actions.items()},
            "pathways": list(self._pathways.keys()),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pack":
        """Create a Pack from dictionary (pack.yaml parsing)."""
        # Parse requirements
        requires_data = data.get("requires", {})
        requires = PackRequirements(
            mcps=[
                MCPRequirement(**m) if isinstance(m, dict) else MCPRequirement(id=m)
                for m in requires_data.get("mcps", [])
            ],
            tools=[
                ToolRequirement(**t) if isinstance(t, dict) else ToolRequirement(name=t)
                for t in requires_data.get("tools", [])
            ],
            features=requires_data.get("features", []),
        )

        # Parse triggers
        triggers = []
        for t in data.get("triggers", []):
            if isinstance(t, dict):
                triggers.append(Trigger(**t))

        # Parse actions
        actions = {}
        for action_id, action_data in data.get("actions", {}).items():
            if isinstance(action_data, dict):
                actions[action_id] = ActionDeclaration(**action_data)
            else:
                actions[action_id] = ActionDeclaration(dispatch=str(action_data))

        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", data.get("id", "Unknown")),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author"),
            license=data.get("license"),
            homepage=data.get("homepage"),
            tags=data.get("tags", []),
            requires=requires,
            triggers=triggers,
            actions=actions,
        )


def pack_builder() -> PackBuilder:
    """Create a fluent pack builder."""
    return PackBuilder()


class PackBuilder:
    """Fluent builder for Pack construction.

    Example:
        pack = (
            pack_builder()
            .id("my_pack")
            .name("My Pack")
            .version("1.0.0")
            .requires_mcp("gmail", required=True)
            .runtime(
                docker_image="albus-datascience:latest",
                allow_site_packages=True,
            )
            .trigger(
                id="inbox",
                source="mcp.gmail",
                event="message_received",
                pathway="my_pack.inbox.v1",
            )
            .action(
                id="reply",
                dispatch="original_channel",
            )
            .pathway("my_pack.inbox.v1", build_inbox_pathway)
            .build()
        )
    """

    def __init__(self):
        self._id: str = "pack"
        self._name: str = "Pack"
        self._version: str = "1.0.0"
        self._description: str = ""
        self._author: str | None = None
        self._tags: list[str] = []
        self._mcps: list[MCPRequirement] = []
        self._tools: list[ToolRequirement] = []
        self._features: list[str] = []
        self._triggers: list[Trigger] = []
        self._actions: dict[str, ActionDeclaration] = {}
        self._pathways: dict[str, Callable[[], "Pathway"]] = {}

    def id(self, pack_id: str) -> "PackBuilder":
        self._id = pack_id
        return self

    def name(self, name: str) -> "PackBuilder":
        self._name = name
        return self

    def version(self, version: str) -> "PackBuilder":
        self._version = version
        return self

    def description(self, desc: str) -> "PackBuilder":
        self._description = desc
        return self

    def author(self, author: str) -> "PackBuilder":
        self._author = author
        return self

    def tag(self, *tags: str) -> "PackBuilder":
        self._tags.extend(tags)
        return self

    def requires_mcp(
        self,
        mcp_id: str,
        *,
        required: bool = True,
        description: str | None = None,
    ) -> "PackBuilder":
        self._mcps.append(
            MCPRequirement(
                id=mcp_id,
                required=required,
                description=description,
            )
        )
        return self

    def requires_tool(self, tool_name: str, *, required: bool = True) -> "PackBuilder":
        self._tools.append(ToolRequirement(name=tool_name, required=required))
        return self

    def requires_feature(self, *features: str) -> "PackBuilder":
        self._features.extend(features)
        return self

    def trigger(
        self,
        id: str,
        source: str,
        pathway: str,
        *,
        event: str | None = None,
        filter: dict[str, Any] | None = None,
        schedule: str | None = None,
        inputs_map: dict[str, str] | None = None,
        enabled: bool = True,
        description: str | None = None,
    ) -> "PackBuilder":
        self._triggers.append(
            Trigger(
                id=id,
                source=source,
                pathway=pathway,
                event=event,
                filter=filter or {},
                schedule=schedule,
                inputs_map=inputs_map or {},
                enabled=enabled,
                description=description,
            )
        )
        return self

    def action(
        self,
        id: str,
        dispatch: str = "original_channel",
        *,
        description: str = "",
        defaults: dict[str, Any] | None = None,
        schema: dict[str, Any] | None = None,
    ) -> "PackBuilder":
        self._actions[id] = ActionDeclaration(
            description=description,
            dispatch=dispatch,
            defaults=defaults or {},
            schema=schema,
        )
        return self

    def pathway(
        self,
        pathway_id: str,
        builder: Callable[[], "Pathway"],
    ) -> "PackBuilder":
        self._pathways[pathway_id] = builder
        return self

    def build(self) -> Pack:
        """Build the Pack."""
        pack = Pack(
            id=self._id,
            name=self._name,
            version=self._version,
            description=self._description,
            author=self._author,
            tags=self._tags,
            requires=PackRequirements(
                mcps=self._mcps,
                tools=self._tools,
                features=self._features,
            ),
            triggers=self._triggers,
            actions=self._actions,
        )
        pack._pathways = self._pathways
        return pack


__all__ = [
    "Pack",
    "PackBuilder",
    "PackRequirements",
    "MCPRequirement",
    "ToolRequirement",
    "Trigger",
    "TriggerSource",
    "ActionDeclaration",
    "pack_builder",
]
