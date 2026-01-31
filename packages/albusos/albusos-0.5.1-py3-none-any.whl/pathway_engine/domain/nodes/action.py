"""ActionNode - Declare intent, runtime handles dispatch.

ActionNode is the pack-centric way to emit outputs. Instead of hardcoding
tool calls or MCP invocations, pathways declare actions by ID.

The runtime:
1. Looks up the action in the pack manifest
2. Resolves the dispatch target (MCP, webhook, event bus, reply channel)
3. Routes the payload to the appropriate handler

This achieves full decoupling - pathways don't know HOW actions are delivered.

Example in pack.yaml:
    actions:
      reply:
        description: "Reply to the original message"
        dispatch: original_channel  # Uses trigger context
      
      notify_staff:
        description: "Alert staff"
        dispatch: mcp.slack.send
        defaults:
          channel: "#property-alerts"

Example in pathway:
    send_response = ActionNode(
        id="send_response",
        action="reply",
        payload={
            "body": "{{output.response_text}}",
            "subject": "Re: {{trigger.event.subject}}",
        },
    )
    
    notify = ActionNode(
        id="notify_staff",
        action="notify_staff",
        payload={
            "message": "🚨 Urgent: {{trigger.event.body[:100]}}",
        },
        condition="{{output.urgency == 'emergency'}}",
    )

The ActionNode computes to:
    {
        "dispatched": True,
        "action": "reply",
        "result": <dispatch result>,
    }
"""

from __future__ import annotations

import re
from typing import Any, Literal, TYPE_CHECKING

from pydantic import Field

from pathway_engine.domain.nodes.base import NodeBase

if TYPE_CHECKING:
    from pathway_engine.domain.context import Context
    from pathway_engine.domain.trigger_context import TriggerContext
    from pathway_engine.domain.pack import ActionDeclaration


class ActionNode(NodeBase):
    """Declare an action to be dispatched by the runtime.

    The pack defines action types in its manifest (actions dict).
    The runtime routes to the correct MCP/handler based on the dispatch config.

    Attributes:
        action: Action ID from pack manifest (e.g., "reply", "notify_staff")
        payload: Data to send - supports {{template}} variables
        condition: Optional condition expression - action skipped if false
        on_error: Error handling: "fail" (default), "skip", or "default"
        default_result: Result to return if on_error="default" and dispatch fails
    """

    type: Literal["action"] = "action"

    # Action declaration
    action: str  # Action ID from pack.yaml
    payload: dict[str, Any] = Field(default_factory=dict)

    # Conditional execution
    condition: str | None = None  # Expression: skip if false

    # Error handling
    on_error: Literal["fail", "skip", "default"] = "fail"
    default_result: dict[str, Any] = Field(default_factory=dict)

    async def compute(self, inputs: dict[str, Any], ctx: "Context") -> dict[str, Any]:
        """Execute the action via the runtime's action dispatcher.

        1. Check condition (if any)
        2. Resolve payload templates
        3. Look up action config from pack
        4. Dispatch via ctx.services.action_dispatcher
        """
        # Check condition
        if self.condition:
            from pathway_engine.domain.expressions import safe_eval

            # Build evaluation context
            eval_ctx = self._build_eval_context(inputs, ctx)
            should_execute = safe_eval(self.condition, eval_ctx)

            if not should_execute:
                return {
                    "dispatched": False,
                    "action": self.action,
                    "reason": "condition_false",
                    "condition": self.condition,
                }

        # Resolve payload templates
        template_ctx = self._build_template_context(inputs, ctx)
        resolved_payload = self._resolve_payload(self.payload, template_ctx)

        # Get action dispatcher from context
        dispatcher = ctx.services.action_dispatcher
        if dispatcher is None:
            # Fallback: return the resolved payload for testing/introspection
            return {
                "dispatched": False,
                "action": self.action,
                "payload": resolved_payload,
                "reason": "no_dispatcher",
            }

        # Get pack context
        pack = ctx.get_extra("pack")
        trigger_context: TriggerContext | None = ctx.get_extra("trigger_context")

        try:
            # Dispatch the action
            result = await dispatcher.dispatch(
                action_id=self.action,
                payload=resolved_payload,
                pack=pack,
                trigger_context=trigger_context,
                ctx=ctx,
            )

            return {
                "dispatched": True,
                "action": self.action,
                "result": result,
            }

        except Exception as e:
            if self.on_error == "fail":
                raise
            elif self.on_error == "skip":
                return {
                    "dispatched": False,
                    "action": self.action,
                    "error": str(e),
                    "reason": "error_skipped",
                }
            else:  # on_error == "default"
                return {
                    "dispatched": False,
                    "action": self.action,
                    "error": str(e),
                    "reason": "error_default",
                    "result": self.default_result,
                }

    def _build_eval_context(
        self,
        inputs: dict[str, Any],
        ctx: "Context",
    ) -> dict[str, Any]:
        """Build context for condition evaluation."""
        result: dict[str, Any] = {**inputs}

        # Add trigger context if available
        trigger_context: TriggerContext | None = ctx.get_extra("trigger_context")
        if trigger_context:
            result["trigger"] = trigger_context.to_template_dict()

        # Add output shorthand (common pattern)
        if "output" in inputs:
            result["output"] = inputs["output"]

        return result

    def _build_template_context(
        self,
        inputs: dict[str, Any],
        ctx: "Context",
    ) -> dict[str, Any]:
        """Build context for template resolution."""
        result: dict[str, Any] = {**inputs}

        # Add trigger context if available
        trigger_context: TriggerContext | None = ctx.get_extra("trigger_context")
        if trigger_context:
            result["trigger"] = trigger_context.to_template_dict()

        return result

    def _resolve_payload(
        self,
        payload: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve {{template}} variables in payload."""
        resolved: dict[str, Any] = {}

        for key, value in payload.items():
            if isinstance(value, str):
                resolved[key] = self._format_template(value, context)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_payload(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    (
                        self._format_template(item, context)
                        if isinstance(item, str)
                        else (
                            self._resolve_payload(item, context)
                            if isinstance(item, dict)
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                resolved[key] = value

        return resolved


__all__ = [
    "ActionNode",
]
