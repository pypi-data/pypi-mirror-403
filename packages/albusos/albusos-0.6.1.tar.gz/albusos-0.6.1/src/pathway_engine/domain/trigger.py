"""Trigger - Event trigger that starts a pathway.

This module defines the core trigger types used by TriggerManager
to wire pathways to event sources (timer, webhook, MCP, event bus).

Triggers can be attached directly to pathways via the pathway.trigger field,
or used standalone with TriggerManager.setup_pathway_trigger().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TriggerSource(Enum):
    """Supported trigger source types."""

    MCP = "mcp"  # MCP resource subscription
    TIMER = "timer"  # Cron-based scheduler
    WEBHOOK = "webhook"  # HTTP webhook endpoint
    MANUAL = "manual"  # API-invoked (always available)
    EVENT_BUS = "event"  # Internal event bus subscription


@dataclass
class Trigger:
    """Event trigger that starts a pathway.

    The runtime reads triggers and wires them to event sources.

    Attributes:
        id: Unique trigger ID
        source: Event source type and identifier:
            - "mcp.<server_id>" → Subscribe to MCP resource events
            - "timer" → Cron-scheduled trigger
            - "webhook" → HTTP POST to /triggers/{trigger_id}
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


__all__ = [
    "Trigger",
    "TriggerSource",
]
