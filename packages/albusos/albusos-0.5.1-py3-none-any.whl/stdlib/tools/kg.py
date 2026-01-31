"""Knowledge Graph tools - structured relational memory for Albus.

This is the MVP "AKG" (Albus Knowledge Graph):
- In-memory store (process-local) with namespaces
- Nodes + edges with provenance (evidence) and confidence
- Query returns a compact prompt-ready context bundle

Design goals:
- Simple interface (tools), robust implementation (defensive, best-effort IDs)
- Traceability: every edge can carry evidence (turn_id, pathway_id, node_id, etc.)
- Works alongside vector memory, not instead of it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Iterable
import re

from pathway_engine.application.ports.tool_registry import ToolContext

from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _stable_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _norm_text(x: Any) -> str:
    try:
        return str(x or "").strip()
    except Exception:
        return ""


def _tokenize(q: str) -> list[str]:
    q = _norm_text(q).lower()
    if not q:
        return []
    # simple tokenizer; good enough for MVP
    toks = [t for t in "".join(ch if ch.isalnum() else " " for ch in q).split() if t]
    # keep a few unique tokens, preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in toks:
        if t not in seen:
            out.append(t)
            seen.add(t)
        if len(out) >= 12:
            break
    return out


_ID_PREFIXES_TO_SLUGIFY = {"goal", "project", "task", "decision"}


def _slugify(s: str) -> str:
    s = _norm_text(s).lower()
    if not s:
        return ""
    # keep alnum; collapse to underscores
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:64] if len(s) > 64 else s


def _canonical_entity_id(raw_id: str) -> str:
    rid = _norm_text(raw_id)
    if not rid:
        return ""
    if ":" not in rid:
        return rid
    prefix, rest = rid.split(":", 1)
    p = _norm_text(prefix).lower()
    if p in _ID_PREFIXES_TO_SLUGIFY:
        slug = _slugify(rest)
        return f"{p}:{slug}" if slug else f"{p}:{_stable_hash(rest)}"
    return rid


@dataclass
class KGNode:
    id: str
    type: str = "entity"
    label: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    created_at_ms: int = field(default_factory=_now_ms)
    updated_at_ms: int = field(default_factory=_now_ms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "properties": self.properties,
            "evidence": self.evidence,
            "created_at_ms": self.created_at_ms,
            "updated_at_ms": self.updated_at_ms,
        }


@dataclass
class KGEdge:
    id: str
    subject: str
    predicate: str
    object: str
    properties: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.7
    created_at_ms: int = field(default_factory=_now_ms)
    updated_at_ms: int = field(default_factory=_now_ms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "properties": self.properties,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "created_at_ms": self.created_at_ms,
            "updated_at_ms": self.updated_at_ms,
        }


class _InMemoryKG:
    def __init__(self) -> None:
        # namespace -> id -> node/edge
        self._nodes: dict[str, dict[str, KGNode]] = {}
        self._edges: dict[str, dict[str, KGEdge]] = {}

    def _ns_nodes(self, ns: str) -> dict[str, KGNode]:
        self._nodes.setdefault(ns, {})
        return self._nodes[ns]

    def _ns_edges(self, ns: str) -> dict[str, KGEdge]:
        self._edges.setdefault(ns, {})
        return self._edges[ns]

    def upsert(
        self,
        *,
        namespace: str,
        nodes: Iterable[dict[str, Any]] | None = None,
        edges: Iterable[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        ns = namespace or "default"
        nmap = self._ns_nodes(ns)
        emap = self._ns_edges(ns)
        n_written = 0
        e_written = 0

        for raw in list(nodes or []):
            try:
                raw_node_id = _norm_text(raw.get("id") or "")
                node_id = _canonical_entity_id(raw_node_id)
                if not node_id:
                    # best-effort stable id
                    node_id = f"node:{_stable_hash(json.dumps(raw, sort_keys=True, default=str))}"
                node_type = _norm_text(raw.get("type") or "entity") or "entity"
                label = raw.get("label")
                props = (
                    raw.get("properties")
                    if isinstance(raw.get("properties"), dict)
                    else {}
                )
                evidence = (
                    raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}
                )
                now = _now_ms()
                existing = nmap.get(node_id)
                if existing is None:
                    if (
                        raw_node_id
                        and raw_node_id != node_id
                        and isinstance(props, dict)
                    ):
                        props = dict(props)
                        props.setdefault("_raw_id", raw_node_id)
                    nmap[node_id] = KGNode(
                        id=node_id,
                        type=node_type,
                        label=_norm_text(label) if label is not None else None,
                        properties=dict(props),
                        evidence=dict(evidence),
                        created_at_ms=now,
                        updated_at_ms=now,
                    )
                else:
                    # merge props; last writer wins on conflicts
                    existing.type = node_type or existing.type
                    if label is not None:
                        existing.label = _norm_text(label) or existing.label
                    if isinstance(props, dict):
                        if raw_node_id and raw_node_id != node_id:
                            props = dict(props)
                            props.setdefault("_raw_id", raw_node_id)
                        existing.properties.update(props)
                    if isinstance(evidence, dict) and evidence:
                        existing.evidence.update(evidence)
                    existing.updated_at_ms = now
                n_written += 1
            except Exception:
                continue

        for raw in list(edges or []):
            try:
                s = _canonical_entity_id(_norm_text(raw.get("subject")))
                p = _norm_text(raw.get("predicate"))
                o = _canonical_entity_id(_norm_text(raw.get("object")))
                if not (s and p and o):
                    continue
                props = (
                    raw.get("properties")
                    if isinstance(raw.get("properties"), dict)
                    else {}
                )
                evidence = (
                    raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}
                )
                conf = raw.get("confidence", 0.7)
                try:
                    conf_f = float(conf)
                except Exception:
                    conf_f = 0.7
                conf_f = max(0.0, min(1.0, conf_f))

                edge_id = _norm_text(raw.get("id") or "")
                if not edge_id:
                    # stable-ish, but allow multiple evidences by including evidence.turn_id when present
                    turn = (
                        _norm_text(evidence.get("turn_id"))
                        if isinstance(evidence, dict)
                        else ""
                    )
                    edge_id = f"edge:{_stable_hash(f'{s}|{p}|{o}|{turn}')}"
                now = _now_ms()
                existing = emap.get(edge_id)
                if existing is None:
                    emap[edge_id] = KGEdge(
                        id=edge_id,
                        subject=s,
                        predicate=p,
                        object=o,
                        properties=dict(props),
                        evidence=dict(evidence),
                        confidence=conf_f,
                        created_at_ms=now,
                        updated_at_ms=now,
                    )
                else:
                    existing.subject = s or existing.subject
                    existing.predicate = p or existing.predicate
                    existing.object = o or existing.object
                    if isinstance(props, dict):
                        existing.properties.update(props)
                    if isinstance(evidence, dict) and evidence:
                        existing.evidence.update(evidence)
                    existing.confidence = max(existing.confidence, conf_f)
                    existing.updated_at_ms = now
                e_written += 1
            except Exception:
                continue

        return {"namespace": ns, "nodes_written": n_written, "edges_written": e_written}

    def explain(self, *, namespace: str, id: str) -> dict[str, Any] | None:
        ns = namespace or "default"
        node = self._ns_nodes(ns).get(id)
        if node is not None:
            return {"kind": "node", "item": node.to_dict()}
        edge = self._ns_edges(ns).get(id)
        if edge is not None:
            return {"kind": "edge", "item": edge.to_dict()}
        return None

    def query(
        self,
        *,
        namespace: str,
        query: str | None = None,
        limit: int = 12,
        entity_id: str | None = None,
        depth: int = 1,
    ) -> dict[str, Any]:
        ns = namespace or "default"
        limit_n = max(1, min(50, int(limit or 12)))
        depth_n = max(0, min(4, int(depth or 1)))

        nmap = self._ns_nodes(ns)
        emap = self._ns_edges(ns)

        hits: list[dict[str, Any]] = []

        if entity_id:
            root = _norm_text(entity_id)
            if not root:
                return {"namespace": ns, "hits": [], "context": ""}
            # BFS out to depth
            frontier = {root}
            seen = {root}
            for _d in range(depth_n):
                nxt: set[str] = set()
                for e in emap.values():
                    if e.subject in frontier and e.object not in seen:
                        nxt.add(e.object)
                    if e.object in frontier and e.subject not in seen:
                        nxt.add(e.subject)
                for x in nxt:
                    seen.add(x)
                frontier = nxt

            # Collect edges touching the induced set
            for e in emap.values():
                if e.subject in seen or e.object in seen:
                    hits.append({"kind": "edge", **e.to_dict()})
                    if len(hits) >= limit_n:
                        break
        else:
            toks = _tokenize(query or "")
            if not toks:
                return {"namespace": ns, "hits": [], "context": ""}

            def _score_text(text: str) -> float:
                t = text.lower()
                score = 0.0
                for w in toks:
                    if w and w in t:
                        score += 1.0
                return score

            scored: list[tuple[float, dict[str, Any]]] = []
            for node in nmap.values():
                blob = " ".join(
                    [
                        node.id,
                        _norm_text(node.type),
                        _norm_text(node.label),
                        json.dumps(node.properties, default=str),
                    ]
                )
                s = _score_text(blob)
                if s > 0:
                    # tiny recency bias (keeps "latest state" nearer the top)
                    scored.append(
                        (
                            s + (node.updated_at_ms / 1e15),
                            {"kind": "node", **node.to_dict()},
                        )
                    )
            for edge in emap.values():
                blob = " ".join(
                    [
                        edge.subject,
                        edge.predicate,
                        edge.object,
                        json.dumps(edge.properties, default=str),
                    ]
                )
                s = (
                    _score_text(blob)
                    + float(edge.confidence) * 0.1
                    + (edge.updated_at_ms / 1e15)
                )
                if s > 0:
                    scored.append((s, {"kind": "edge", **edge.to_dict()}))
            scored.sort(key=lambda x: x[0], reverse=True)
            hits = [item for _s, item in scored[:limit_n]]

        # Build prompt-ready context lines (compact, readable)
        lines: list[str] = []
        for h in hits[:limit_n]:
            if h.get("kind") == "edge":
                lines.append(
                    f'- ({float(h.get("confidence", 0.0)):.2f}) {h.get("subject")} --{h.get("predicate")}--> {h.get("object")}'
                )
            else:
                label = _norm_text(h.get("label")) or _norm_text(h.get("id"))
                ntype = _norm_text(h.get("type")) or "entity"
                lines.append(f"- [{ntype}] {label}")
        context = "\n".join(lines).strip()

        return {"namespace": ns, "hits": hits, "context": context}

    def current(
        self,
        *,
        namespace: str,
        user_id: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return a 'current state' view for the namespace.

        MVP semantics:
        - Resolve revisions via `replaces` edges: if X replaces Y, Y is not current.
        - Return current goals/projects/tasks plus a compact context string.
        """
        ns = namespace or "default"
        nmap = self._ns_nodes(ns)
        emap = self._ns_edges(ns)

        limit_n = max(1, min(100, int(limit or 20)))
        uid = _canonical_entity_id(_norm_text(user_id)) if user_id else ""

        replaced: set[str] = set()
        for e in emap.values():
            if _norm_text(e.predicate).lower() == "replaces":
                replaced.add(_canonical_entity_id(e.object))

        def is_current(node_id: str) -> bool:
            return _canonical_entity_id(node_id) not in replaced

        # Gather nodes by type (current only)
        goals: list[dict[str, Any]] = []
        projects: list[dict[str, Any]] = []
        tasks: list[dict[str, Any]] = []

        for node in nmap.values():
            if not is_current(node.id):
                continue
            t = _norm_text(node.type).lower()
            if t == "goal":
                goals.append(node.to_dict())
            elif t == "project":
                projects.append(node.to_dict())
            elif t == "task":
                tasks.append(node.to_dict())

        # Sort by recency
        goals.sort(key=lambda x: int(x.get("updated_at_ms") or 0), reverse=True)
        projects.sort(key=lambda x: int(x.get("updated_at_ms") or 0), reverse=True)
        tasks.sort(key=lambda x: int(x.get("updated_at_ms") or 0), reverse=True)

        goals = goals[:limit_n]
        projects = projects[:limit_n]
        tasks = tasks[:limit_n]

        # Filter edges to the "current" set (and optionally to user neighborhood)
        current_ids = {
            n["id"]
            for n in goals + projects + tasks
            if isinstance(n, dict) and n.get("id")
        }
        if uid:
            current_ids.add(uid)

        edges: list[dict[str, Any]] = []
        for e in emap.values():
            if (
                not is_current(e.object)
                and _norm_text(e.predicate).lower() != "replaces"
            ):
                continue
            if uid:
                if e.subject != uid and e.object != uid:
                    # only show edges attached to the user if user_id specified
                    continue
            if current_ids and (
                e.subject in current_ids
                or e.object in current_ids
                or _norm_text(e.predicate).lower() == "replaces"
            ):
                edges.append(e.to_dict())

        edges.sort(key=lambda x: int(x.get("updated_at_ms") or 0), reverse=True)
        edges = edges[: max(10, min(200, limit_n * 5))]

        # Prompt-ready context
        lines: list[str] = []
        if goals:
            lines.append("Goals:")
            for g in goals[: min(8, len(goals))]:
                lines.append(f'- {g.get("label") or g.get("id")}')
        if projects:
            lines.append("Projects:")
            for p in projects[: min(8, len(projects))]:
                lines.append(f'- {p.get("label") or p.get("id")}')
        if tasks:
            lines.append("Tasks:")
            for t in tasks[: min(10, len(tasks))]:
                lines.append(f'- {t.get("label") or t.get("id")}')
        context = "\n".join(lines).strip()

        return {
            "namespace": ns,
            "user_id": uid or None,
            "goals": goals,
            "projects": projects,
            "tasks": tasks,
            "edges": edges,
            "context": context,
        }


_KG = _InMemoryKG()


@register_tool(
    "kg.upsert",
    description="Upsert knowledge graph nodes/edges with evidence and confidence.",
    parameters={
        "type": "object",
        "properties": {
            "namespace": {"type": "string", "default": "default"},
            "nodes": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of nodes: {id,type,label,properties,evidence}",
            },
            "edges": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of edges: {id,subject,predicate,object,properties,evidence,confidence}",
            },
        },
        "required": [],
    },
)
async def kg_upsert(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    namespace = _norm_text(inputs.get("namespace") or "default") or "default"
    nodes = inputs.get("nodes")
    edges = inputs.get("edges")
    # ToolNode templates JSON-encode dict/list values. Accept either native lists
    # or JSON strings for ergonomic DSL usage.
    if isinstance(nodes, str):
        try:
            nodes = json.loads(nodes)
        except Exception:
            nodes = []
    if isinstance(edges, str):
        try:
            edges = json.loads(edges)
        except Exception:
            edges = []

    nodes_list = list(nodes) if isinstance(nodes, list) else []
    edges_list = list(edges) if isinstance(edges, list) else []

    result = _KG.upsert(namespace=namespace, nodes=nodes_list, edges=edges_list)
    return {"success": True, **result}


@register_tool(
    "kg.query",
    description="Query the knowledge graph and return prompt-ready context plus structured hits.",
    parameters={
        "type": "object",
        "properties": {
            "namespace": {"type": "string", "default": "default"},
            "query": {"type": "string", "description": "Free-text query"},
            "limit": {"type": "integer", "default": 12},
            "entity_id": {
                "type": "string",
                "description": "If provided, traverse from this entity",
            },
            "depth": {"type": "integer", "default": 1},
        },
        "required": [],
    },
)
async def kg_query(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    namespace = _norm_text(inputs.get("namespace") or "default") or "default"
    query = inputs.get("query")
    entity_id = inputs.get("entity_id")
    limit = inputs.get("limit", 12)
    depth = inputs.get("depth", 1)

    out = _KG.query(
        namespace=namespace,
        query=_norm_text(query),
        limit=int(limit or 12),
        entity_id=_norm_text(entity_id) if entity_id is not None else None,
        depth=int(depth or 1),
    )
    return {"success": True, **out}


@register_tool(
    "kg.explain",
    description="Explain a KG node/edge by returning its evidence and fields.",
    parameters={
        "type": "object",
        "properties": {
            "namespace": {"type": "string", "default": "default"},
            "id": {"type": "string", "description": "Node ID or edge ID"},
        },
        "required": ["id"],
    },
)
async def kg_explain(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    namespace = _norm_text(inputs.get("namespace") or "default") or "default"
    item_id = _norm_text(inputs.get("id"))
    if not item_id:
        return {"success": False, "error": "id is required"}
    out = _KG.explain(namespace=namespace, id=item_id)
    if out is None:
        return {"success": False, "found": False, "id": item_id, "namespace": namespace}
    return {
        "success": True,
        "found": True,
        "id": item_id,
        "namespace": namespace,
        **out,
    }


@register_tool(
    "kg.clear",
    description="Clear the knowledge graph (optionally by namespace).",
    parameters={
        "type": "object",
        "properties": {
            "namespace": {
                "type": "string",
                "description": "Namespace to clear (omit for all)",
            }
        },
        "required": [],
    },
)
async def kg_clear(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    ns = inputs.get("namespace")
    # best-effort; this is a dev/test tool
    try:
        if ns:
            _KG._nodes.pop(str(ns), None)  # noqa: SLF001 (intentional for dev tool)
            _KG._edges.pop(str(ns), None)  # noqa: SLF001
            return {"success": True, "cleared": True, "namespace": str(ns)}
        _KG._nodes.clear()  # noqa: SLF001
        _KG._edges.clear()  # noqa: SLF001
        return {"success": True, "cleared": True, "namespace": "all"}
    except Exception as e:
        logger.warning("kg.clear failed: %s", e)
        return {"success": False, "error": str(e)}


@register_tool(
    "kg.current",
    description="Get the current goals/projects/tasks for a namespace (resolves replaces edges).",
    parameters={
        "type": "object",
        "properties": {
            "namespace": {"type": "string", "default": "default"},
            "thread_id": {
                "type": "string",
                "description": "Optional convenience: namespace becomes thread_{thread_id}",
            },
            "user_id": {
                "type": "string",
                "description": "Optional: filter edges to this user neighborhood",
            },
            "limit": {"type": "integer", "default": 20},
        },
        "required": [],
    },
)
async def kg_current(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    ns = _norm_text(inputs.get("namespace") or "default") or "default"
    thread_id = _norm_text(inputs.get("thread_id") or "")
    if thread_id:
        ns = f"thread_{thread_id}"
    user_id = inputs.get("user_id")
    limit = inputs.get("limit", 20)
    out = _KG.current(
        namespace=ns,
        user_id=_norm_text(user_id) if user_id is not None else None,
        limit=int(limit or 20),
    )
    return {"success": True, **out}


__all__ = ["kg_upsert", "kg_query", "kg_explain", "kg_clear", "kg_current"]
