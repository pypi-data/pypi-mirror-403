"""TriggerManager - Wires pathway triggers to event sources.

The TriggerManager reads trigger configurations from pathways and:
1. Subscribes to the appropriate event sources (MCP, timer, webhook, event bus)
2. Creates TriggerContext when events fire
3. Invokes the configured pathway with the event data

This is the bridge between external events and pathway execution.

Example:
    manager = TriggerManager(
        pathway_invoker=invoke_pathway,
        mcp_client=mcp,
        webhook_bus=webhook_bus,
        event_bus=event_bus,
    )
    
    # Wire up a pathway trigger
    await manager.setup_pathway_trigger(
        "my_pathway",
        {"type": "timer", "schedule": "0 9 * * *"}
    )
    
    # Start listening (runs until cancelled)
    await manager.start()
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, TYPE_CHECKING

from pathway_engine.domain.trigger_context import TriggerContext, ReplyChannel
from pathway_engine.domain.trigger import Trigger, TriggerSource

if TYPE_CHECKING:
    from pathway_engine.infrastructure.mcp.client import McpClientService
    from pathway_engine.domain.streaming import WebhookBus
    from pathway_engine.domain.event_bus import AsyncEventBus

logger = logging.getLogger(__name__)


class TriggerError(Exception):
    """Error setting up or firing a trigger."""

    pass


@dataclass
class TriggerSubscription:
    """Active subscription for a trigger."""

    trigger_id: str
    pack_id: str
    source: str
    pathway_id: str
    task: asyncio.Task | None = None
    active: bool = True

    def cancel(self) -> None:
        """Cancel this subscription."""
        self.active = False
        if self.task and not self.task.done():
            self.task.cancel()


# Type for pathway invoker callback
PathwayInvoker = Callable[
    [str, dict[str, Any], TriggerContext], Awaitable[dict[str, Any]]
]


@dataclass
class TriggerManager:
    """Manages trigger subscriptions and event routing.

    This component:
    - Sets up triggers from pathways (pathway.trigger field)
    - Listens to event sources (MCP, timers, webhooks, event bus)
    - Creates TriggerContext for each event
    - Invokes pathways when triggers fire
    """

    # Services
    _pathway_invoker: PathwayInvoker | None = None
    _mcp_client: "McpClientService | None" = None
    _webhook_bus: "WebhookBus | None" = None
    _event_bus: "AsyncEventBus | None" = None

    # Scheduler for cron triggers
    _scheduler: Any | None = None

    # Active subscriptions
    _subscriptions: dict[str, TriggerSubscription] = field(default_factory=dict)


    # Background tasks
    _tasks: list[asyncio.Task] = field(default_factory=list)

    def __init__(
        self,
        *,
        pathway_invoker: PathwayInvoker | None = None,
        mcp_client: "McpClientService | None" = None,
        webhook_bus: "WebhookBus | None" = None,
        event_bus: "AsyncEventBus | None" = None,
    ):
        self._pathway_invoker = pathway_invoker
        self._mcp_client = mcp_client
        self._webhook_bus = webhook_bus
        self._event_bus = event_bus
        self._subscriptions = {}
        self._tasks = []

    def set_pathway_invoker(self, invoker: PathwayInvoker) -> None:
        """Set the pathway invoker callback."""
        self._pathway_invoker = invoker


    async def setup_trigger(
        self,
        trigger: Trigger,
        *,
        pack_id: str,
    ) -> TriggerSubscription:
        """Set up a single trigger.

        Args:
            trigger: Trigger declaration
            pack_id: Pack ID for namespacing

        Returns:
            Active subscription
        """
        sub_key = f"{pack_id}.{trigger.id}"

        # Check for existing subscription
        if sub_key in self._subscriptions:
            existing = self._subscriptions[sub_key]
            if existing.active:
                logger.warning("Trigger already subscribed: %s", sub_key)
                return existing
            # Clean up old subscription
            existing.cancel()

        # Create subscription
        subscription = TriggerSubscription(
            trigger_id=trigger.id,
            pack_id=pack_id,
            source=trigger.source,
            pathway_id=trigger.pathway,
        )

        # Set up based on source type
        source_type = trigger.source_type

        if source_type == TriggerSource.TIMER:
            await self._setup_timer_trigger(trigger, subscription)

        elif source_type == TriggerSource.WEBHOOK:
            await self._setup_webhook_trigger(trigger, subscription)

        elif source_type == TriggerSource.EVENT_BUS:
            await self._setup_event_trigger(trigger, subscription)

        elif source_type == TriggerSource.MCP:
            await self._setup_mcp_trigger(trigger, subscription)

        elif source_type == TriggerSource.MANUAL:
            # Manual triggers don't need setup - they're invoked via API
            logger.debug("Manual trigger registered: %s", sub_key)

        else:
            raise TriggerError(f"Unknown trigger source type: {trigger.source}")

        self._subscriptions[sub_key] = subscription
        logger.debug("Trigger subscribed: %s -> %s", sub_key, trigger.pathway)

        return subscription

    async def setup_pathway_trigger(
        self,
        pathway_id: str,
        trigger_config: dict[str, Any],
    ) -> TriggerSubscription | None:
        """Set up a trigger directly from a pathway's trigger config.

        This enables pathways to have triggers without needing a pack wrapper.
        The pathway itself declares when it should run.

        Args:
            pathway_id: ID of the pathway to trigger
            trigger_config: Trigger configuration dict with keys:
                - type: "timer", "webhook", "event" (required)
                - schedule: Cron expression for timer triggers
                - topic: Webhook topic name
                - channel: Event bus channel name

        Returns:
            Active subscription, or None if trigger_config is empty

        Example:
            # Daily at 9am
            await manager.setup_pathway_trigger(
                "my_pathway",
                {"type": "timer", "schedule": "0 9 * * *"}
            )

            # On webhook
            await manager.setup_pathway_trigger(
                "my_pathway",
                {"type": "webhook", "topic": "github-events"}
            )
        """
        if not trigger_config:
            return None

        trigger_type = trigger_config.get("type", "manual")

        # Map simple type to source string
        if trigger_type == "timer":
            source = "timer"
        elif trigger_type == "webhook":
            source = "webhook"
        elif trigger_type == "event":
            channel = trigger_config.get("channel", "default")
            source = f"event.{channel}"
        elif trigger_type.startswith("mcp."):
            source = trigger_type
        else:
            source = "manual"

        # Create Trigger from config
        trigger = Trigger(
            id=f"trigger_{pathway_id}",
            source=source,
            pathway=pathway_id,
            schedule=trigger_config.get("schedule"),
            event=trigger_config.get("event"),
            filter=trigger_config.get("filter", {}),
            inputs_map=trigger_config.get("inputs_map", {}),
            enabled=trigger_config.get("enabled", True),
            description=trigger_config.get("description"),
        )

        # Use pathway_id as the "pack_id" namespace for standalone pathways
        return await self.setup_trigger(trigger, pack_id=f"pathway:{pathway_id}")

    async def _setup_timer_trigger(
        self,
        trigger: Trigger,
        subscription: TriggerSubscription,
    ) -> None:
        """Set up a cron-based timer trigger."""
        if not trigger.schedule:
            raise TriggerError(f"Timer trigger requires schedule: {trigger.id}")

        # Create a task that fires on schedule
        async def timer_loop():
            try:
                # Simple implementation: use croniter for cron parsing
                # For now, just use a fixed interval based on schedule
                interval = self._parse_cron_interval(trigger.schedule)

                while subscription.active:
                    await asyncio.sleep(interval)

                    if not subscription.active:
                        break

                    # Create trigger context
                    ctx = TriggerContext.for_timer(
                        trigger_id=trigger.id,
                        pack_id=subscription.pack_id,
                        schedule=trigger.schedule,
                    )

                    # Fire the trigger
                    await self._fire_trigger(trigger, ctx)

            except asyncio.CancelledError:
                logger.debug("Timer trigger cancelled: %s", trigger.id)
            except Exception as e:
                logger.error("Timer trigger error: %s - %s", trigger.id, e)

        task = asyncio.create_task(timer_loop())
        subscription.task = task
        self._tasks.append(task)

    def _parse_cron_interval(self, schedule: str) -> float:
        """Parse a cron expression to an interval in seconds.

        This is a simplified implementation. For production,
        use croniter or similar for proper cron parsing.
        """
        # Simple patterns
        if schedule == "* * * * *":  # Every minute
            return 60.0
        elif schedule.startswith("*/"):
            # */N * * * * = every N minutes
            try:
                parts = schedule.split()
                minutes = int(parts[0].split("/")[1])
                return minutes * 60.0
            except (IndexError, ValueError):
                pass
        elif schedule == "0 * * * *":  # Every hour
            return 3600.0
        elif schedule.startswith("0 "):
            # Likely daily - default to 24h
            return 86400.0

        # Default: every 5 minutes
        logger.warning(
            "Could not parse cron '%s', defaulting to 5min interval",
            schedule,
        )
        return 300.0

    async def _setup_webhook_trigger(
        self,
        trigger: Trigger,
        subscription: TriggerSubscription,
    ) -> None:
        """Set up a webhook trigger subscription."""
        # Extract topic from trigger config or ID
        topic = trigger.filter.get("topic", trigger.id)

        if self._webhook_bus is None:
            # Use global webhook bus
            from pathway_engine.domain.streaming import WEBHOOK_BUS

            self._webhook_bus = WEBHOOK_BUS

        # Subscribe to webhook topic
        queue = self._webhook_bus.subscribe(topic)

        async def webhook_loop():
            try:
                while subscription.active:
                    payload = await queue.get()

                    if not subscription.active:
                        break

                    # Check filter (exclude 'topic' which is used for subscription, not content)
                    content_filter = {
                        k: v for k, v in trigger.filter.items() if k != "topic"
                    }
                    if not self._matches_filter(payload, content_filter):
                        continue

                    # Create trigger context
                    callback_url = payload.pop("_callback_url", None)
                    ctx = TriggerContext.for_webhook(
                        trigger_id=trigger.id,
                        pack_id=subscription.pack_id,
                        topic=topic,
                        payload=payload,
                        callback_url=callback_url,
                    )

                    # Fire the trigger
                    await self._fire_trigger(trigger, ctx)

            except asyncio.CancelledError:
                logger.debug("Webhook trigger cancelled: %s", trigger.id)
            finally:
                self._webhook_bus.unsubscribe(topic, queue)

        task = asyncio.create_task(webhook_loop())
        subscription.task = task
        self._tasks.append(task)

    async def _setup_event_trigger(
        self,
        trigger: Trigger,
        subscription: TriggerSubscription,
    ) -> None:
        """Set up an internal event bus trigger."""
        channel = trigger.event_channel
        if not channel:
            raise TriggerError(f"Event trigger requires channel: {trigger.id}")

        if self._event_bus is None:
            raise TriggerError("Event bus not available for trigger")

        async def event_loop():
            try:
                async for event in self._event_bus.subscribe(channel):
                    if not subscription.active:
                        break

                    # Check filter
                    if not self._matches_filter(event, trigger.filter):
                        continue

                    # Create trigger context
                    ctx = TriggerContext.for_event_bus(
                        trigger_id=trigger.id,
                        pack_id=subscription.pack_id,
                        channel=channel,
                        event_data=event,
                    )

                    # Fire the trigger
                    await self._fire_trigger(trigger, ctx)

            except asyncio.CancelledError:
                logger.debug("Event trigger cancelled: %s", trigger.id)
            except Exception as e:
                logger.error("Event trigger error: %s - %s", trigger.id, e)

        task = asyncio.create_task(event_loop())
        subscription.task = task
        self._tasks.append(task)

    async def _setup_mcp_trigger(
        self,
        trigger: Trigger,
        subscription: TriggerSubscription,
    ) -> None:
        """Set up an MCP resource subscription trigger.

        Note: MCP resource subscriptions are not fully standardized yet.
        This implementation provides a placeholder that can be extended
        when MCP servers support resource subscriptions.
        """
        mcp_server = trigger.mcp_server_id
        if not mcp_server:
            raise TriggerError(f"MCP trigger requires server ID: {trigger.id}")

        if self._mcp_client is None:
            raise TriggerError("MCP client not available for trigger")

        # Check if server is available
        available_servers = self._mcp_client.list_server_ids()
        if mcp_server not in available_servers:
            raise TriggerError(f"MCP server not available: {mcp_server}")

        # MCP resource subscription is server-specific
        # For now, log a warning and treat as manual
        logger.warning(
            "MCP resource subscription not fully implemented for %s. "
            "Trigger %s will be manual-only until MCP server supports subscriptions.",
            mcp_server,
            trigger.id,
        )

        # TODO: When MCP servers support resource subscriptions:
        # - Call mcp_client.subscribe_resource(server_id, resource_uri, callback)
        # - The callback creates TriggerContext and fires the trigger

    def _matches_filter(
        self,
        data: dict[str, Any],
        filter_spec: dict[str, Any],
    ) -> bool:
        """Check if data matches filter criteria."""
        if not filter_spec:
            return True

        for key, expected in filter_spec.items():
            # Skip internal keys
            if key.startswith("_"):
                continue

            actual = data.get(key)

            if isinstance(expected, list):
                # Any match in list
                if actual not in expected:
                    return False
            elif isinstance(expected, dict):
                # Nested match
                if not isinstance(actual, dict):
                    return False
                if not self._matches_filter(actual, expected):
                    return False
            else:
                # Exact match
                if actual != expected:
                    return False

        return True

    async def _fire_trigger(
        self,
        trigger: Trigger,
        ctx: TriggerContext,
    ) -> None:
        """Fire a trigger by invoking its pathway."""
        if self._pathway_invoker is None:
            logger.error(
                "Cannot fire trigger %s: no pathway invoker configured",
                trigger.id,
            )
            return

        # Map event to inputs using inputs_map
        inputs = self._map_inputs(ctx.event, trigger.inputs_map)

        logger.info(
            "Firing trigger %s.%s -> %s",
            ctx.pack_id,
            trigger.id,
            trigger.pathway,
        )

        try:
            result = await self._pathway_invoker(
                trigger.pathway,
                inputs,
                ctx,
            )

            logger.debug(
                "Trigger %s.%s completed: %s",
                ctx.pack_id,
                trigger.id,
                "success" if result.get("success", True) else "failed",
            )

        except Exception as e:
            logger.error(
                "Trigger %s.%s failed: %s",
                ctx.pack_id,
                trigger.id,
                e,
            )

    def _map_inputs(
        self,
        event: dict[str, Any],
        inputs_map: dict[str, str],
    ) -> dict[str, Any]:
        """Map event data to pathway inputs using inputs_map.

        inputs_map example:
            {"message": "event.body", "user": "event.from"}

        This transforms:
            event = {"body": "Hello", "from": "user@example.com"}
        To:
            inputs = {"message": "Hello", "user": "user@example.com"}
        """
        if not inputs_map:
            # Default: pass event as "trigger" input
            return {"trigger": event}

        inputs = {}
        for input_key, event_path in inputs_map.items():
            # Resolve path in event
            value = self._resolve_path(event, event_path)
            inputs[input_key] = value

        # Always include trigger context
        inputs["trigger"] = event

        return inputs

    def _resolve_path(
        self,
        data: dict[str, Any],
        path: str,
    ) -> Any:
        """Resolve a dot-path in nested dict.

        path examples:
            "event.body" → data["event"]["body"]
            "body" → data["body"]
            "user.profile.name" → data["user"]["profile"]["name"]
        """
        parts = path.split(".")
        result: Any = data

        for part in parts:
            if isinstance(result, dict):
                result = result.get(part)
            else:
                return None

        return result

    async def fire_manual(
        self,
        trigger_id: str,
        pack_id: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Fire a manual trigger via API.

        Args:
            trigger_id: Trigger ID
            pack_id: Pack ID
            inputs: Input data

        Returns:
            Pathway execution result
        """
        pack = self._packs.get(pack_id)
        if not pack:
            raise TriggerError(f"Pack not found: {pack_id}")

        trigger = pack.get_trigger(trigger_id)
        if not trigger:
            raise TriggerError(f"Trigger not found: {trigger_id}")

        # Create trigger context for manual invocation
        ctx = TriggerContext.for_manual(
            trigger_id=trigger_id,
            pack_id=pack_id,
            inputs=inputs,
        )

        if self._pathway_invoker is None:
            raise TriggerError("No pathway invoker configured")

        # Map inputs
        mapped_inputs = self._map_inputs(inputs, trigger.inputs_map)

        return await self._pathway_invoker(
            trigger.pathway,
            mapped_inputs,
            ctx,
        )

    def list_subscriptions(self) -> list[dict[str, Any]]:
        """List all active subscriptions."""
        return [
            {
                "trigger_id": sub.trigger_id,
                "pack_id": sub.pack_id,
                "source": sub.source,
                "pathway_id": sub.pathway_id,
                "active": sub.active,
            }
            for sub in self._subscriptions.values()
        ]

    def get_subscription(
        self,
        pack_id: str,
        trigger_id: str,
    ) -> TriggerSubscription | None:
        """Get a specific subscription."""
        key = f"{pack_id}.{trigger_id}"
        return self._subscriptions.get(key)

    async def cancel_trigger(
        self,
        pack_id: str,
        trigger_id: str,
    ) -> bool:
        """Cancel a trigger subscription.

        Returns:
            True if cancelled, False if not found
        """
        key = f"{pack_id}.{trigger_id}"
        sub = self._subscriptions.get(key)

        if not sub:
            return False

        sub.cancel()
        del self._subscriptions[key]

        logger.info("Cancelled trigger: %s", key)
        return True

    async def cancel_pack(self, pack_id: str) -> int:
        """Cancel all triggers for a pack.

        Returns:
            Number of triggers cancelled
        """
        cancelled = 0
        keys_to_remove = [
            key for key in self._subscriptions if key.startswith(f"{pack_id}.")
        ]

        for key in keys_to_remove:
            sub = self._subscriptions.pop(key)
            sub.cancel()
            cancelled += 1

        if pack_id in self._packs:
            del self._packs[pack_id]

        logger.info("Cancelled %d triggers for pack '%s'", cancelled, pack_id)
        return cancelled

    async def shutdown(self) -> None:
        """Shutdown all trigger subscriptions."""
        logger.info("Shutting down trigger manager...")

        # Cancel all subscriptions
        for sub in self._subscriptions.values():
            sub.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._subscriptions.clear()
        self._packs.clear()
        self._tasks.clear()

        logger.info("Trigger manager shutdown complete")


__all__ = [
    "TriggerManager",
    "TriggerSubscription",
    "TriggerError",
]
