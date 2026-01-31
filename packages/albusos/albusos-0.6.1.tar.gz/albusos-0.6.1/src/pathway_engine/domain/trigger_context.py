"""TriggerContext - Event context that flows through triggered pathways.

When an event triggers a pathway, this context carries:
- The original event data
- Reply routing information
- Trigger metadata

This enables pathways to:
- Access event data via {{trigger.event.*}}
- Reply to the original channel via the trigger's reply_to

Example:
    # Trigger fires from gmail.message_received
    trigger_ctx = TriggerContext(
        trigger_id="inbox_watch",
        source="mcp.gmail",
        event_type="message_received",
        event={
            "message_id": "abc123",
            "from": "tenant@example.com",
            "subject": "Maintenance Request",
            "body": "My sink is leaking...",
        },
        reply_to=ReplyChannel(
            channel="mcp.gmail",
            method="reply",
            context={"thread_id": "abc123", "to": "tenant@example.com"},
        ),
    )
    
    # In pathway templates:
    # {{trigger.event.body}} → "My sink is leaking..."
    # {{trigger.source}} → "mcp.gmail"
    
    # ActionNode with action="reply" uses reply_to to route response
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ReplyChannel:
    """How to reply to the original event source.

    This is computed by the runtime when a trigger fires,
    enabling pathways to route responses correctly.

    Attributes:
        channel: Dispatch target (e.g., "mcp.gmail", "webhook.response")
        method: Channel-specific method (e.g., "reply", "send", "post")
        context: Additional context needed for the reply:
            - thread_id, message_id for email threading
            - channel_id, user_id for chat replies
            - callback_url for webhooks
    """

    channel: str  # "mcp.gmail", "webhook.callback", etc.
    method: str = "send"  # Channel method: "reply", "send", etc.
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "method": self.method,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplyChannel":
        return cls(
            channel=data.get("channel", ""),
            method=data.get("method", "send"),
            context=data.get("context", {}),
        )


@dataclass
class TriggerContext:
    """Context from the event that triggered a pathway run.

    This is created by the TriggerManager when an event fires,
    and flows through the entire pathway execution.

    Nodes access it via:
    - ctx.extras["trigger_context"] → TriggerContext object
    - {{trigger.*}} in templates → Resolved from this context

    Attributes:
        trigger_id: Which trigger fired
        pack_id: Optional namespace for the trigger (e.g., "pathway:my_pathway")
        source: Event source (e.g., "mcp.gmail", "timer", "webhook")
        event_type: Event type (e.g., "message_received")
        timestamp: When the event occurred
        event: Raw event payload (source-specific structure)
        reply_to: How to reply to this event (if applicable)
        metadata: Additional context (idempotency keys, trace IDs, etc.)
    """

    # Identity
    trigger_id: str
    source: str  # "mcp.gmail", "timer", "webhook.topic"

    # Optional fields (with defaults)
    pack_id: str = ""  # Optional namespace (e.g., "pathway:my_pathway")
    event_type: str = ""  # Event type (MCP resource type, etc.)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Event data
    event: dict[str, Any] = field(default_factory=dict)

    # Reply routing (set by runtime based on source)
    reply_to: ReplyChannel | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for template resolution and logging."""
        return {
            "trigger_id": self.trigger_id,
            "pack_id": self.pack_id,
            "source": self.source,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "event": self.event,
            "reply_to": self.reply_to.to_dict() if self.reply_to else None,
            "metadata": self.metadata,
        }

    def to_template_dict(self) -> dict[str, Any]:
        """Flatten for {{trigger.*}} template access.

        Returns dict with structure:
            trigger_id: "inbox_watch"
            pack_id: "my_pack"
            source: "mcp.gmail"
            event_type: "message_received"
            timestamp: "2024-..."
            event: {message_id: ..., from: ..., body: ...}
            reply_to: {channel: ..., method: ..., context: ...}

        Templates can access:
            {{trigger.event.body}} → "My sink is leaking..."
            {{trigger.source}} → "mcp.gmail"
        """
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TriggerContext":
        """Deserialize from dictionary."""
        reply_data = data.get("reply_to")
        reply_to = ReplyChannel.from_dict(reply_data) if reply_data else None

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            trigger_id=data.get("trigger_id", ""),
            pack_id=data.get("pack_id", ""),
            source=data.get("source", ""),
            event_type=data.get("event_type", ""),
            timestamp=timestamp,
            event=data.get("event", {}),
            reply_to=reply_to,
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def for_timer(
        cls,
        *,
        trigger_id: str,
        pack_id: str,
        schedule: str | None = None,
    ) -> "TriggerContext":
        """Create a TriggerContext for a timer trigger."""
        return cls(
            trigger_id=trigger_id,
            pack_id=pack_id,
            source="timer",
            event_type="tick",
            event={
                "schedule": schedule,
                "fired_at": datetime.now(timezone.utc).isoformat(),
            },
            reply_to=None,  # Timer triggers have no reply channel
        )

    @classmethod
    def for_webhook(
        cls,
        *,
        trigger_id: str,
        pack_id: str,
        topic: str,
        payload: dict[str, Any],
        callback_url: str | None = None,
    ) -> "TriggerContext":
        """Create a TriggerContext for a webhook trigger."""
        reply_to = None
        if callback_url:
            reply_to = ReplyChannel(
                channel="webhook.callback",
                method="post",
                context={"url": callback_url},
            )

        return cls(
            trigger_id=trigger_id,
            pack_id=pack_id,
            source=f"webhook.{topic}",
            event_type="webhook_received",
            event=payload,
            reply_to=reply_to,
        )

    @classmethod
    def for_mcp_event(
        cls,
        *,
        trigger_id: str,
        pack_id: str,
        mcp_server: str,
        event_type: str,
        event_data: dict[str, Any],
        reply_context: dict[str, Any] | None = None,
    ) -> "TriggerContext":
        """Create a TriggerContext for an MCP event trigger.

        Args:
            trigger_id: Trigger ID
            pack_id: Pathway ID (legacy field)
            mcp_server: MCP server ID (e.g., "gmail")
            event_type: Event type (e.g., "message_received")
            event_data: Raw event payload
            reply_context: Optional context for replying (server-specific)
        """
        reply_to = None
        if reply_context:
            reply_to = ReplyChannel(
                channel=f"mcp.{mcp_server}",
                method=reply_context.get("method", "reply"),
                context=reply_context.get("context", {}),
            )

        return cls(
            trigger_id=trigger_id,
            pack_id=pack_id,
            source=f"mcp.{mcp_server}",
            event_type=event_type,
            event=event_data,
            reply_to=reply_to,
        )

    @classmethod
    def for_manual(
        cls,
        *,
        trigger_id: str,
        pack_id: str,
        inputs: dict[str, Any],
    ) -> "TriggerContext":
        """Create a TriggerContext for manual (API) invocation."""
        return cls(
            trigger_id=trigger_id,
            pack_id=pack_id,
            source="manual",
            event_type="api_call",
            event=inputs,
            reply_to=None,  # Manual triggers return via API response
        )

    @classmethod
    def for_event_bus(
        cls,
        *,
        trigger_id: str,
        pack_id: str,
        channel: str,
        event_data: dict[str, Any],
    ) -> "TriggerContext":
        """Create a TriggerContext for internal event bus trigger."""
        return cls(
            trigger_id=trigger_id,
            pack_id=pack_id,
            source=f"event.{channel}",
            event_type="event_bus",
            event=event_data,
            reply_to=ReplyChannel(
                channel=f"event.{channel}_response",
                method="publish",
                context={},
            ),
        )


__all__ = [
    "TriggerContext",
    "ReplyChannel",
]
