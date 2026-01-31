"""ActionDispatcher - Routes actions to MCPs, webhooks, and event buses.

This is the runtime component that fulfills ActionNode declarations.

The dispatcher:
1. Looks up the action in the pack manifest
2. Merges defaults with the provided payload
3. Routes to the configured destination:
   - original_channel → Use trigger context reply_to
   - mcp.<server>.<tool> → Call MCP tool
   - webhook.<topic> → Publish to webhook bus
   - event.<channel> → Publish to event bus

Example:
    dispatcher = ActionDispatcher(mcp_client=mcp, webhook_bus=bus)
    
    result = await dispatcher.dispatch(
        action_id="reply",
        payload={"body": "Hello!"},
        pack=my_pack,
        trigger_context=trigger_ctx,
        ctx=execution_ctx,
    )
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pathway_engine.domain.context import Context
    from pathway_engine.domain.pack import Pack, ActionDeclaration
    from pathway_engine.domain.trigger_context import TriggerContext
    from pathway_engine.infrastructure.mcp.client import McpClientService
    from pathway_engine.domain.streaming import WebhookBus
    from pathway_engine.domain.event_bus import AsyncEventBus

logger = logging.getLogger(__name__)


class ActionDispatchError(Exception):
    """Error dispatching an action."""

    pass


class ActionNotFoundError(ActionDispatchError):
    """Action not found in pack manifest."""

    pass


class ActionDispatcher:
    """Routes actions to their configured destinations.

    This is the bridge between pack declarations and runtime execution.
    ActionNodes call dispatcher.dispatch() and the dispatcher handles
    all the routing logic.
    """

    def __init__(
        self,
        *,
        mcp_client: "McpClientService | None" = None,
        webhook_bus: "WebhookBus | None" = None,
        event_bus: "AsyncEventBus | None" = None,
    ):
        self._mcp_client = mcp_client
        self._webhook_bus = webhook_bus
        self._event_bus = event_bus
        self._custom_handlers: dict[str, Any] = {}

    def register_handler(self, dispatch_prefix: str, handler: Any) -> None:
        """Register a custom dispatch handler.

        Args:
            dispatch_prefix: Prefix to match (e.g., "custom.my_system")
            handler: Async callable(payload, context) -> result
        """
        self._custom_handlers[dispatch_prefix] = handler

    async def dispatch(
        self,
        action_id: str,
        payload: dict[str, Any],
        *,
        pack: "Pack | None" = None,
        trigger_context: "TriggerContext | None" = None,
        ctx: "Context | None" = None,
    ) -> dict[str, Any]:
        """Dispatch an action to its configured destination.

        Args:
            action_id: Action ID from pack manifest
            payload: Resolved payload to send
            pack: Pack containing the action declaration
            trigger_context: Trigger context for reply routing
            ctx: Execution context

        Returns:
            Result from the dispatch target

        Raises:
            ActionNotFoundError: Action not in pack manifest
            ActionDispatchError: Dispatch failed
        """
        # Get action declaration
        action_decl = self._get_action_declaration(action_id, pack)
        if action_decl is None:
            raise ActionNotFoundError(f"Action not found: {action_id}")

        # Merge defaults with payload
        merged_payload = {**action_decl.defaults, **payload}

        # Route based on dispatch type
        dispatch = action_decl.dispatch
        dispatch_type = action_decl.dispatch_type

        logger.debug(
            "Dispatching action %s via %s (type=%s)",
            action_id,
            dispatch,
            dispatch_type,
        )

        if dispatch_type == "original_channel":
            return await self._dispatch_to_original(
                merged_payload, trigger_context, ctx
            )

        elif dispatch_type == "mcp":
            return await self._dispatch_to_mcp(dispatch, merged_payload, ctx)

        elif dispatch_type == "webhook":
            return await self._dispatch_to_webhook(dispatch, merged_payload)

        elif dispatch_type == "event":
            return await self._dispatch_to_event(dispatch, merged_payload)

        else:
            # Check custom handlers
            for prefix, handler in self._custom_handlers.items():
                if dispatch.startswith(prefix):
                    return await handler(merged_payload, ctx)

            raise ActionDispatchError(
                f"Unknown dispatch type: {dispatch} for action {action_id}"
            )

    def _get_action_declaration(
        self,
        action_id: str,
        pack: "Pack | None",
    ) -> "ActionDeclaration | None":
        """Get action declaration from pack or fallback."""
        if pack:
            return pack.get_action(action_id)

        # Fallback: try to find in context's pack registry
        return None

    async def _dispatch_to_original(
        self,
        payload: dict[str, Any],
        trigger_context: "TriggerContext | None",
        ctx: "Context | None",
    ) -> dict[str, Any]:
        """Dispatch via the original trigger's reply channel."""
        if trigger_context is None or trigger_context.reply_to is None:
            raise ActionDispatchError(
                "Cannot dispatch to original_channel: no reply_to in trigger context"
            )

        reply_to = trigger_context.reply_to
        channel = reply_to.channel
        method = reply_to.method
        context = reply_to.context

        # Merge reply context into payload
        full_payload = {**context, **payload}

        logger.debug(
            "Dispatching to original channel: %s.%s",
            channel,
            method,
        )

        # Route based on channel type
        if channel.startswith("mcp."):
            # Extract server and construct tool name
            mcp_server = channel.split(".", 1)[1]
            tool_name = method  # e.g., "reply", "send"

            return await self._call_mcp_tool(mcp_server, tool_name, full_payload, ctx)

        elif channel.startswith("webhook."):
            # Extract topic
            topic = channel.split(".", 1)[1]
            return await self._publish_webhook(topic, full_payload)

        elif channel.startswith("event."):
            # Extract event channel
            event_channel = channel.split(".", 1)[1]
            return await self._publish_event(event_channel, full_payload)

        else:
            # Unknown channel type - log and return success
            logger.warning("Unknown reply channel type: %s", channel)
            return {
                "success": True,
                "channel": channel,
                "method": method,
                "payload": full_payload,
                "note": "channel_not_implemented",
            }

    async def _dispatch_to_mcp(
        self,
        dispatch: str,
        payload: dict[str, Any],
        ctx: "Context | None",
    ) -> dict[str, Any]:
        """Dispatch to an MCP tool.

        dispatch format: "mcp.<server>.<tool>" or "mcp.<server>"
        """
        parts = dispatch.split(".")
        if len(parts) < 2:
            raise ActionDispatchError(f"Invalid MCP dispatch: {dispatch}")

        server = parts[1]
        tool = parts[2] if len(parts) > 2 else payload.pop("_tool", "send")

        return await self._call_mcp_tool(server, tool, payload, ctx)

    async def _call_mcp_tool(
        self,
        server: str,
        tool: str,
        arguments: dict[str, Any],
        ctx: "Context | None",
    ) -> dict[str, Any]:
        """Call an MCP tool."""
        if self._mcp_client is None:
            raise ActionDispatchError(
                f"MCP client not available for dispatch to {server}.{tool}"
            )

        try:
            result = await self._mcp_client.call_tool(
                server_id=server,
                tool=tool,
                arguments=arguments,
            )

            return {
                "success": True,
                "mcp_server": server,
                "tool": tool,
                "result": result,
            }

        except Exception as e:
            logger.error("MCP dispatch failed: %s.%s - %s", server, tool, e)
            raise ActionDispatchError(f"MCP call failed: {e}") from e

    async def _dispatch_to_webhook(
        self,
        dispatch: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch to webhook bus.

        dispatch format: "webhook.<topic>"
        """
        parts = dispatch.split(".", 1)
        if len(parts) < 2:
            raise ActionDispatchError(f"Invalid webhook dispatch: {dispatch}")

        topic = parts[1]
        return await self._publish_webhook(topic, payload)

    async def _publish_webhook(
        self,
        topic: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Publish to webhook bus."""
        if self._webhook_bus is None:
            # Fallback: import the global webhook bus
            from pathway_engine.domain.streaming import WEBHOOK_BUS

            self._webhook_bus = WEBHOOK_BUS

        delivered = self._webhook_bus.publish(topic, payload)

        return {
            "success": True,
            "webhook_topic": topic,
            "delivered": delivered,
        }

    async def _dispatch_to_event(
        self,
        dispatch: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch to internal event bus.

        dispatch format: "event.<channel>"
        """
        parts = dispatch.split(".", 1)
        if len(parts) < 2:
            raise ActionDispatchError(f"Invalid event dispatch: {dispatch}")

        channel = parts[1]
        return await self._publish_event(channel, payload)

    async def _publish_event(
        self,
        channel: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Publish to internal event bus."""
        if self._event_bus is None:
            raise ActionDispatchError(f"Event bus not available for channel: {channel}")

        self._event_bus.publish(channel, payload)

        return {
            "success": True,
            "event_channel": channel,
            "published": True,
        }


__all__ = [
    "ActionDispatcher",
    "ActionDispatchError",
    "ActionNotFoundError",
]
