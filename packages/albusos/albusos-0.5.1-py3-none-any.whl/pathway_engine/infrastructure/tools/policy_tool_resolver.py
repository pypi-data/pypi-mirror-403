"""ToolRegistry wrapper that enforces host-owned policy and emits audit events."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from pathway_engine.infrastructure.llm.tools import ToolSpec
from pathway_engine.application.ports.tool_registry import (
    ToolContext,
    ToolRegistryPort,
    ToolSchema,
)
from pathway_engine.infrastructure.tools.audit import AuditSink
from pathway_engine.application.ports.runtime import get_tool_policy_context
from pathway_engine.application.ports.contracts.tool_policy import ToolPolicyDecision


class ToolPolicyDenied(PermissionError):
    """Raised when tool execution is denied by host policy."""


def _redact_params(params: dict[str, Any]) -> dict[str, Any]:
    # Best-effort redaction; do not store secrets in audit logs.
    out: dict[str, Any] = {}
    for k, v in (params or {}).items():
        key = str(k)
        lk = key.lower()
        if any(
            tok in lk
            for tok in ("key", "token", "secret", "password", "auth", "bearer")
        ):
            out[key] = "[redacted]"
        else:
            out[key] = v
    return out


@dataclass
class PolicyToolResolver(ToolRegistryPort):
    """ToolRegistry wrapper that enforces policy and emits audit events."""

    inner: ToolRegistryPort
    classify_tool: Callable[[str, ToolSpec | None], ToolPolicyDecision] | None = None
    audit: AuditSink | None = None
    enforce_for_all_origins: bool = False

    # ------------------------------------------------------------------
    # ToolRegistryPort implementation - delegate to inner
    # ------------------------------------------------------------------

    def list_tools(self, *, privileged: bool = False) -> list[ToolSchema]:
        """Delegate tool listing to inner registry."""
        return self.inner.list_tools(privileged=privileged)

    def get_tool(self, tool_id: str) -> ToolSchema | None:
        """Delegate tool lookup to inner registry."""
        return self.inner.get_tool(tool_id)

    # ------------------------------------------------------------------
    # Optional capability passthroughs (keep planner/tooling UX intact)
    # ------------------------------------------------------------------

    def list_tool_names(self, *, limit: int = 200) -> list[str]:
        """Best-effort passthrough for UI/planner tool listing."""
        try:
            fn = getattr(self.inner, "list_tool_names", None)
            if callable(fn):
                out = fn(limit=limit)  # type: ignore[misc]
                return list(out) if isinstance(out, list) else []
        except Exception:
            return []
        return []

    def get_tool_spec(self, tool_name: str) -> ToolSpec | None:
        """Best-effort passthrough so policy classification can see specs when available."""
        try:
            fn = getattr(self.inner, "get_tool_spec", None)
            if callable(fn):
                spec = fn(tool_name)  # type: ignore[misc]
                return spec if isinstance(spec, ToolSpec) else None
        except Exception:
            return None
        return None

    def set_runtime_services(self, *, memory_store: Any | None) -> None:
        """Passthrough so dynamic/builtin tools can access runtime services.

        Note: LLM and vector capabilities are now accessed via tool_registry.invoke().
        """
        try:
            fn = getattr(self.inner, "set_runtime_services", None)
            if callable(fn):
                fn(memory_store=memory_store)  # type: ignore[misc]
        except Exception:
            return

    def set_pathway_catalog(self, *, list_pathways: Any | None = None) -> None:
        """Passthrough to enable pathway.list/search tools when supported by inner registry."""
        try:
            fn = getattr(self.inner, "set_pathway_catalog", None)
            if callable(fn):
                fn(list_pathways=list_pathways)  # type: ignore[misc]
        except Exception:
            return

    def _get_spec_best_effort(self, tool_name: str) -> ToolSpec | None:
        # If the inner registry can expose ToolSpec, use it (optional capability).
        try:
            fn = getattr(self.inner, "get_tool_spec", None)
            if callable(fn):
                spec = fn(tool_name)  # type: ignore[misc]
                return spec if isinstance(spec, ToolSpec) else None
        except Exception:
            return None
        return None

    def _should_enforce(self, *, origin: str) -> bool:
        if self.enforce_for_all_origins:
            return True
        # Primary focus: chat governance (explicit approval required).
        return origin == "chat"

    @staticmethod
    def _require_chat_approval_for_all_tools() -> bool:
        """Hosted-beta default: in chat, deny *all* tool calls unless approved."""
        raw = (os.getenv("PATHWAY_CHAT_TOOLS_REQUIRE_APPROVAL") or "").strip().lower()
        if raw in ("1", "true", "yes", "y", "on"):
            return True
        if raw in ("0", "false", "no", "n", "off"):
            return False
        # Default: enforce in production.
        return (os.getenv("PATHWAY_ENV") or "development").strip().lower() in (
            "production",
            "prod",
        )

    async def invoke(
        self,
        tool_id: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Invoke tool with policy enforcement and audit logging."""
        ctx = get_tool_policy_context()
        origin = str(ctx.origin or "unknown")
        tool_name = tool_id

        # Policy Profiles (v1): explicit tool allow/deny lists.
        try:
            allow = ctx.policy_profile_tool_allowlist
            deny = ctx.policy_profile_tool_denylist
            tname = str(tool_name or "")
            if isinstance(deny, list) and any(
                str(x).strip() == tname for x in deny if str(x).strip()
            ):
                raise ToolPolicyDenied("tool_policy_denied:policy_profile_denylist")
            if isinstance(allow, list) and allow:
                allowed = {str(x).strip() for x in allow if str(x).strip()}
                if allowed and tname not in allowed:
                    raise ToolPolicyDenied(
                        "tool_policy_denied:policy_profile_allowlist"
                    )
        except ToolPolicyDenied:
            # Denials are audited below in the normal deny path.
            raise
        except Exception:
            # Never block tool calls due to malformed policy profiles.
            pass

        spec = self._get_spec_best_effort(tool_name)
        # Host-owned classification. If not provided, default to conservative network impact.
        if self.classify_tool is None:
            decision = ToolPolicyDecision(
                impact="network",
                requires_approval=True,
                reason="no_policy_classifier_configured",
            )
        else:
            decision = self.classify_tool(str(tool_name), spec)

        if (
            self._should_enforce(origin=origin)
            and origin == "chat"
            and self._require_chat_approval_for_all_tools()
            and not bool(ctx.approved)
        ):
            # Hosted/prod default: fail-closed for anything that is not a safe read.
            # This allows "internal retrieval" tools (read-only) to run without interrupting UX,
            # while keeping mutate/network/execute behind explicit approval.
            if decision.impact != "read":
                if self.audit is not None:
                    self.audit.emit(
                        {
                            "type": "tool_call_denied",
                            "origin": origin,
                            "request_id": ctx.request_id,
                            "session_id": ctx.session_id,
                            "workspace_id": ctx.workspace_id,
                            "project_id": ctx.project_id,
                            "doc_id": ctx.doc_id,
                            "actor_id": ctx.actor_id,
                            "approved_plan_id": ctx.approved_plan_id,
                            "tool_name": str(tool_name),
                            "impact": decision.impact,
                            "reason": "approval_required_non_read",
                            "parameters": _redact_params(arguments or {}),
                        }
                    )
                raise ToolPolicyDenied("tool_policy_denied:approval_required_non_read")

        if (
            self._should_enforce(origin=origin)
            and decision.requires_approval
            and not bool(ctx.approved)
        ):
            if self.audit is not None:
                self.audit.emit(
                    {
                        "type": "tool_call_denied",
                        "origin": origin,
                        "request_id": ctx.request_id,
                        "session_id": ctx.session_id,
                        "workspace_id": ctx.workspace_id,
                        "project_id": ctx.project_id,
                        "doc_id": ctx.doc_id,
                        "actor_id": ctx.actor_id,
                        "approved_plan_id": ctx.approved_plan_id,
                        "tool_name": str(tool_name),
                        "impact": decision.impact,
                        "reason": decision.reason,
                        "parameters": _redact_params(arguments or {}),
                    }
                )
            raise ToolPolicyDenied(
                f"tool_policy_denied:{decision.impact}:{decision.reason}"
            )

        if self.audit is not None:
            self.audit.emit(
                {
                    "type": "tool_call_started",
                    "origin": origin,
                    "request_id": ctx.request_id,
                    "session_id": ctx.session_id,
                    "workspace_id": ctx.workspace_id,
                    "project_id": ctx.project_id,
                    "doc_id": ctx.doc_id,
                    "actor_id": ctx.actor_id,
                    "approved_plan_id": ctx.approved_plan_id,
                    "tool_name": str(tool_name),
                    "impact": decision.impact,
                    "parameters": _redact_params(arguments or {}),
                }
            )

        try:
            out = await self.inner.invoke(tool_id, arguments, context)
            if self.audit is not None:
                self.audit.emit(
                    {
                        "type": "tool_call_completed",
                        "origin": origin,
                        "request_id": ctx.request_id,
                        "session_id": ctx.session_id,
                        "workspace_id": ctx.workspace_id,
                        "project_id": ctx.project_id,
                        "doc_id": ctx.doc_id,
                        "actor_id": ctx.actor_id,
                        "approved_plan_id": ctx.approved_plan_id,
                        "tool_name": str(tool_name),
                        "impact": decision.impact,
                        "ok": True,
                    }
                )
            return out
        except Exception as e:
            if self.audit is not None:
                self.audit.emit(
                    {
                        "type": "tool_call_completed",
                        "origin": origin,
                        "request_id": ctx.request_id,
                        "session_id": ctx.session_id,
                        "workspace_id": ctx.workspace_id,
                        "project_id": ctx.project_id,
                        "doc_id": ctx.doc_id,
                        "actor_id": ctx.actor_id,
                        "approved_plan_id": ctx.approved_plan_id,
                        "tool_name": str(tool_name),
                        "impact": decision.impact,
                        "ok": False,
                        "error": str(e),
                    }
                )
            raise


__all__ = [
    "PolicyToolResolver",
    "ToolPolicyDenied",
]
