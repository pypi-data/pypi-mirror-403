"""Governance auditing (host boundary).

This is intentionally simple:
- JSONL append-only sink for local/dev
- Hook point for future Postgres/Supabase auditing
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol


class AuditSink(Protocol):
    def emit(self, event: dict[str, Any]) -> None: ...


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass(frozen=True)
class JsonlAuditSink:
    path: str

    def emit(self, event: dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            payload = dict(event)
            payload.setdefault("ts_ms", _now_ms())
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            # Auditing must never break execution.
            return


@dataclass(frozen=True)
class LoggerAuditSink:
    logger_name: str = "ice.audit.tools"

    def emit(self, event: dict[str, Any]) -> None:
        try:
            logging.getLogger(self.logger_name).info("%s", event)
        except Exception:
            return


def default_audit_sink() -> AuditSink | None:
    """Create the default audit sink.

    Defaults:
    - Always log to the Python logger (safe observability baseline)
    - Optionally also append JSONL when configured

    Env:
    - PATHWAY_TOOL_AUDIT_ENABLED=0: disable all auditing
    - PATHWAY_TOOL_AUDIT_JSONL_PATH: file path for jsonl (enables JSONL append)
    - PATHWAY_TOOL_AUDIT_ENABLED=1 with no path: enable JSONL at default path
    """
    enabled = (os.getenv("PATHWAY_TOOL_AUDIT_ENABLED", "1") or "1").strip() == "1"
    path = (os.getenv("PATHWAY_TOOL_AUDIT_JSONL_PATH") or "").strip()
    if not enabled:
        return None
    if path:
        return JsonlAuditSink(path=path)
    # If explicitly enabled, default to JSONL for durable local observability.
    if (os.getenv("PATHWAY_TOOL_AUDIT_ENABLED", "1") or "1").strip() == "1":
        # Unified governance audit stream (tools + runs + writes).
        return JsonlAuditSink(path="./data/studio/audit/governance.jsonl")
    return LoggerAuditSink()


__all__ = [
    "AuditSink",
    "JsonlAuditSink",
    "LoggerAuditSink",
    "default_audit_sink",
]
