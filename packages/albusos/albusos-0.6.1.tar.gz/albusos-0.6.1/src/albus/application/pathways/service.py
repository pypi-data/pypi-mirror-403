"""PathwayService - Unified pathway registry and storage.

This replaces the two-world problem:
- OLD: PackRegistry (in-memory) vs StudioDomainService (documents)
- NEW: PathwayService (single source of truth)

All pathways are stored as documents with versioning.
Pack pathways are "deployed" with source="pack:<pack_id>".
User pathways are created with source="user:<context>".

API:
    service = PathwayService(store=store)
    
    # Deploy pack pathways at startup
    service.deploy(pathway, source="pack:my_pack", version="1.0")
    
    # Create user pathway
    service.create(pathway, source="user:chat_session_xyz")
    
    # Load any pathway (unified)
    pathway = service.load("my_turn.pathway.v1")
    pathway = service.load("doc_fd7b70231af0")
    
    # List all pathways
    pathways = service.list()
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from pathway_engine.domain.pathway import Pathway, Connection

if TYPE_CHECKING:
    from persistence.infrastructure.storage.store import StudioStore

logger = logging.getLogger(__name__)


class PathwaySource(Enum):
    """Origin of a pathway."""

    PACK = "pack"  # Deployed from code (pathway_engine)
    USER = "user"  # Created via API/tools
    IMPORT = "import"  # Imported from export


@dataclass
class PathwayMeta:
    """Metadata for a registered pathway."""

    id: str
    name: str | None
    description: str | None
    source: str  # "pack:my_pack" or "user:session_xyz"
    version: str | None
    doc_id: str | None  # Document ID if persisted
    node_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "version": self.version,
            "doc_id": self.doc_id,
            "node_count": self.node_count,
        }


@dataclass
class PathwayService:
    """Unified pathway registry and storage.

    This is THE single source of truth for all pathways in the system.

    Architecture:
    - In-memory cache for fast lookup (all pathways indexed by ID)
    - Persistent storage for user pathways (via StudioStore)
    - Pack pathways are deployed at startup and cached
    """

    # In-memory registry (pathway_id -> builder or Pathway)
    _registry: dict[str, Callable[[], Pathway] | Pathway] = field(default_factory=dict)

    # Metadata for all registered pathways
    _meta: dict[str, PathwayMeta] = field(default_factory=dict)

    # Persistent storage (optional - enables user pathways)
    _store: "StudioStore | None" = None

    # Default workspace for user pathways
    _default_workspace_id: str | None = None

    def __init__(
        self,
        *,
        store: "StudioStore | None" = None,
        default_workspace_id: str | None = None,
    ):
        self._registry = {}
        self._meta = {}
        self._store = store
        self._default_workspace_id = default_workspace_id

    # =========================================================================
    # DEPLOYMENT (Pack pathways)
    # =========================================================================

    def deploy(
        self,
        pathway_or_builder: Pathway | Callable[[], Pathway],
        *,
        pathway_id: str | None = None,
        source: str = "pack:unknown",
        version: str | None = None,
        persist: bool = False,
    ) -> PathwayMeta:
        """Deploy a pathway to the runtime.

        Args:
            pathway_or_builder: Pathway object or lazy builder function
            pathway_id: ID to register under (defaults to pathway.id)
            source: Origin identifier (e.g., "host:authored", "user:api")
            version: Version string
            persist: Whether to persist to storage

        Returns:
            PathwayMeta with deployment info
        """
        # Resolve pathway if needed
        if callable(pathway_or_builder):
            pathway = pathway_or_builder()
            builder = pathway_or_builder
        else:
            pathway = pathway_or_builder
            builder = lambda p=pathway: p

        pid = pathway_id or pathway.id

        # Register in memory
        self._registry[pid] = builder

        # Store metadata
        meta = PathwayMeta(
            id=pid,
            name=pathway.name,
            description=pathway.description,
            source=source,
            version=version,
            doc_id=None,
            node_count=len(pathway.nodes),
        )

        # Persist if requested and store available
        if persist and self._store:
            doc_id = self._persist_pathway(pathway, source=source, version=version)
            meta.doc_id = doc_id

        self._meta[pid] = meta
        logger.debug("Deployed pathway: %s (source=%s)", pid, source)
        return meta

    # =========================================================================
    # CREATION (User pathways)
    # =========================================================================

    def create(
        self,
        pathway: Pathway,
        *,
        source: str = "user:unknown",
        workspace_id: str | None = None,
    ) -> PathwayMeta:
        """Create a user pathway.

        Args:
            pathway: Pathway to create
            source: Origin identifier (e.g., "user:chat_session_xyz")
            workspace_id: Workspace to store in

        Returns:
            PathwayMeta with creation info
        """
        pid = pathway.id

        # Persist if store available
        doc_id = None
        if self._store:
            ws_id = workspace_id or self._default_workspace_id
            if ws_id:
                doc_id = self._persist_pathway(
                    pathway,
                    source=source,
                    workspace_id=ws_id,
                )

        # Register in memory
        self._registry[pid] = pathway

        # Also register by doc_id if we have one
        if doc_id:
            self._registry[doc_id] = pathway

        meta = PathwayMeta(
            id=pid,
            name=pathway.name,
            description=pathway.description,
            source=source,
            version=None,
            doc_id=doc_id,
            node_count=len(pathway.nodes),
        )
        self._meta[pid] = meta
        if doc_id:
            self._meta[doc_id] = meta

        logger.debug("Created pathway: %s (source=%s, doc_id=%s)", pid, source, doc_id)
        return meta

    # =========================================================================
    # LOADING (Unified)
    # =========================================================================

    def load(self, pathway_id: str) -> Pathway | None:
        """Load a pathway by ID.

        Checks in order:
        1. In-memory registry (pack + user pathways)
        2. Persistent storage (user pathways by doc_id)

        Args:
            pathway_id: Pathway ID or document ID

        Returns:
            Pathway if found, None otherwise
        """
        # Check in-memory registry first
        entry = self._registry.get(pathway_id)
        if entry is not None:
            if callable(entry):
                return entry()
            return entry

        # Try loading from storage
        if self._store:
            pathway = self._load_from_storage(pathway_id)
            if pathway:
                # Cache for future lookups
                self._registry[pathway_id] = pathway
                return pathway

        return None

    def resolve(self, pathway_id: str) -> Callable[[], Pathway] | None:
        """Get a lazy loader for a pathway.

        Returns a callable that builds the pathway on demand.
        """
        entry = self._registry.get(pathway_id)
        if entry is not None:
            if callable(entry):
                return entry
            return lambda p=entry: p

        # Check storage
        if self._store:

            def _lazy_load(pid=pathway_id):
                return self._load_from_storage(pid)

            return _lazy_load

        return None

    def get_meta(self, pathway_id: str) -> PathwayMeta | None:
        """Get metadata for a pathway."""
        return self._meta.get(pathway_id)

    # =========================================================================
    # LISTING
    # =========================================================================

    def list(
        self,
        *,
        source_filter: str | None = None,
        include_pack: bool = True,
        include_user: bool = True,
    ) -> list[PathwayMeta]:
        """List all registered pathways.

        Args:
            source_filter: Filter by source prefix (e.g., "pack:my_pack")
            include_pack: Include pack pathways
            include_user: Include user pathways

        Returns:
            List of PathwayMeta
        """
        results = []
        seen_ids = set()

        for pid, meta in self._meta.items():
            # Dedupe (pathways may be registered under multiple IDs)
            if meta.id in seen_ids:
                continue
            seen_ids.add(meta.id)

            # Apply filters
            if source_filter and not meta.source.startswith(source_filter):
                continue

            is_pack = meta.source.startswith("pack:")
            if is_pack and not include_pack:
                continue
            if not is_pack and not include_user:
                continue

            results.append(meta)

        return results

    def list_pack_pathways(self) -> list[PathwayMeta]:
        """List only pack pathways."""
        return self.list(include_pack=True, include_user=False)

    def list_user_pathways(self) -> list[PathwayMeta]:
        """List only user pathways."""
        return self.list(include_pack=False, include_user=True)

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def export(self, pathway_id: str) -> dict[str, Any] | None:
        """Export a pathway as a portable JSON document.

        Returns:
            JSON-serializable dict or None if not found
        """
        pathway = self.load(pathway_id)
        if pathway is None:
            return None

        meta = self._meta.get(pathway_id)

        return {
            "format": "albus.pathway.v1",
            "pathway": {
                "id": pathway.id,
                "name": pathway.name,
                "description": pathway.description,
                "nodes": [
                    self._serialize_node(node) for node in pathway.nodes.values()
                ],
                "connections": [
                    {"from": c.from_node, "to": c.to_node} for c in pathway.connections
                ],
                "metadata": dict(pathway.metadata),
            },
            "meta": meta.to_dict() if meta else None,
        }

    def import_pathway(
        self,
        data: dict[str, Any],
        *,
        new_id: str | None = None,
        workspace_id: str | None = None,
    ) -> PathwayMeta:
        """Import a pathway from an export.

        Args:
            data: Export data from export()
            new_id: Override ID for the imported pathway
            workspace_id: Workspace to store in

        Returns:
            PathwayMeta for the imported pathway
        """
        if data.get("format") != "albus.pathway.v1":
            raise ValueError(f"Unsupported format: {data.get('format')}")

        pathway_data = data.get("pathway", {})
        pathway = self._pathway_from_dict(pathway_data)

        if new_id:
            pathway.id = new_id

        return self.create(
            pathway,
            source=f"import:{data.get('meta', {}).get('source', 'unknown')}",
            workspace_id=workspace_id,
        )

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _persist_pathway(
        self,
        pathway: Pathway,
        *,
        source: str,
        version: str | None = None,
        workspace_id: str | None = None,
    ) -> str | None:
        """Persist a pathway to storage."""
        if not self._store:
            return None

        ws_id = workspace_id or self._default_workspace_id
        if not ws_id:
            logger.warning("Cannot persist pathway: no workspace_id")
            return None

        # Ensure workspace exists
        try:
            ws = self._store.get_workspace(ws_id)
            if not ws:
                self._store.upsert_workspace(
                    {
                        "id": ws_id,
                        "name": f"Pathways ({ws_id})",
                    }
                )
        except Exception as e:
            logger.warning("Failed to ensure workspace: %s", e)

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        try:
            # Create document
            self._store.upsert_document(
                {
                    "id": doc_id,
                    "type": "pathway",
                    "name": pathway.name or pathway.id,
                    "workspace_id": ws_id,
                    "parent_id": None,
                    "metadata": {
                        "pathway_id": pathway.id,
                        "source": source,
                        "version": version,
                    },
                    "head_rev": None,
                }
            )

            # Write content as revision
            content = {
                "id": pathway.id,
                "name": pathway.name,
                "description": pathway.description,
                "source": source,
                "version": version,
                "nodes": [
                    self._serialize_node(node) for node in pathway.nodes.values()
                ],
                "connections": [
                    {"from": c.from_node, "to": c.to_node} for c in pathway.connections
                ],
                "metadata": dict(pathway.metadata),
            }

            rev_id = f"rev_{uuid.uuid4().hex[:12]}"
            self._store.write_revision(doc_id=doc_id, rev_id=rev_id, content=content)
            self._store.upsert_document({"id": doc_id, "head_rev": rev_id})

            return doc_id

        except Exception as e:
            logger.error("Failed to persist pathway: %s", e)
            return None

    def _load_from_storage(self, pathway_id: str) -> Pathway | None:
        """Load a pathway from storage by doc_id or pathway_id."""
        if not self._store:
            return None

        # Try as doc_id first
        doc = self._store.get_document(pathway_id)
        if doc:
            return self._load_doc_pathway(pathway_id)

        # Search by pathway_id in metadata
        # This is slower but handles the case where we're looking up by pathway.id
        try:
            all_docs = self._store.list_documents(workspace_id=None)
            for doc in all_docs:
                if doc.get("type") != "pathway":
                    continue
                meta = doc.get("metadata", {})
                if meta.get("pathway_id") == pathway_id:
                    return self._load_doc_pathway(doc.get("id"))
        except Exception as e:
            logger.debug("Failed to search pathways: %s", e)

        return None

    def _load_doc_pathway(self, doc_id: str) -> Pathway | None:
        """Load a pathway from a document."""
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
            return self._pathway_from_dict(content)

        except Exception as e:
            logger.error("Failed to load pathway %s: %s", doc_id, e)
            return None

    def _serialize_node(self, node: Any) -> dict[str, Any]:
        """Serialize a node to a dictionary."""
        result: dict[str, Any] = {
            "id": node.id,
            "type": node.type,
            "name": getattr(node, "name", None),
            "description": getattr(node, "description", None),
            "config": {},
        }

        # Extract config based on node type
        if node.type == "llm":
            result["config"]["prompt"] = getattr(node, "prompt", "")
            result["config"]["model"] = getattr(node, "model", "auto")
            result["config"]["temperature"] = getattr(node, "temperature", 0.7)
            if getattr(node, "max_tokens", None):
                result["config"]["max_tokens"] = node.max_tokens
            if getattr(node, "system", None):
                result["config"]["system"] = node.system
            if getattr(node, "response_format", None):
                result["config"]["response_format"] = node.response_format
            if getattr(node, "json_schema", None):
                result["config"]["json_schema"] = node.json_schema
            if getattr(node, "images", None):
                result["config"]["images"] = node.images

        elif node.type == "tool":
            result["config"]["tool"] = getattr(node, "tool", "")
            result["config"]["args"] = getattr(node, "args", {})

        elif node.type == "transform":
            result["config"]["expr"] = getattr(node, "expr", "input")

        elif node.type == "router":
            result["config"]["condition"] = getattr(node, "condition", "true")
            result["config"]["routes"] = getattr(node, "routes", {})
            result["config"]["default"] = getattr(node, "default", None)

        elif node.type == "gate":
            result["config"]["condition"] = getattr(node, "condition", "true")
            result["config"]["true_path"] = getattr(node, "true_path", "")
            result["config"]["false_path"] = getattr(node, "false_path", "")

        elif node.type == "code":
            result["config"]["code"] = getattr(node, "code", "")
            result["config"]["language"] = getattr(node, "language", "python")
            # Sandbox configuration (enables user-authored datascience/viz code)
            if getattr(node, "profile", None) is not None:
                result["config"]["profile"] = getattr(node, "profile")
            if getattr(node, "allow_site_packages", None) is not None:
                result["config"]["allow_site_packages"] = getattr(
                    node, "allow_site_packages"
                )
            if getattr(node, "timeout_ms", None) is not None:
                result["config"]["timeout_ms"] = getattr(node, "timeout_ms")
            if getattr(node, "memory_mb", None) is not None:
                result["config"]["memory_mb"] = getattr(node, "memory_mb")

        elif node.type == "memory_read":
            result["config"]["query"] = getattr(node, "query", None)
            result["config"]["key"] = getattr(node, "key", None)
            result["config"]["namespace"] = getattr(node, "namespace", "default")

        elif node.type == "memory_write":
            result["config"]["key"] = getattr(node, "key", "")
            result["config"]["value_expr"] = getattr(node, "value_expr", "{{input}}")
            result["config"]["namespace"] = getattr(node, "namespace", "default")

        return result

    def _node_from_dict(self, node_dict: dict[str, Any]) -> Any:
        """Create a typed node from a dictionary."""
        from pathway_engine.domain.nodes import (
            LLMNode,
            ToolNode,
            CodeNode,
            TransformNode,
            RouterNode,
            GateNode,
            MemoryReadNode,
            MemoryWriteNode,
        )

        node_type = node_dict.get("type", "transform")
        node_id = node_dict.get("id", f"node_{uuid.uuid4().hex[:6]}")

        TYPE_MAP = {
            "llm": LLMNode,
            "tool": ToolNode,
            "code": CodeNode,
            "transform": TransformNode,
            "router": RouterNode,
            "gate": GateNode,
            "memory_read": MemoryReadNode,
            "memory_write": MemoryWriteNode,
        }

        node_class = TYPE_MAP.get(node_type, TransformNode)

        kwargs: dict[str, Any] = {"id": node_id}

        if node_dict.get("name"):
            kwargs["name"] = node_dict["name"]
        if node_dict.get("description"):
            kwargs["description"] = node_dict["description"]

        config = node_dict.get("config", {})

        if node_type == "llm":
            kwargs["prompt"] = config.get("prompt", "")
            kwargs["model"] = config.get("model", "auto")
            kwargs["temperature"] = config.get("temperature", 0.7)
            if config.get("max_tokens"):
                kwargs["max_tokens"] = config["max_tokens"]
            if config.get("system"):
                kwargs["system"] = config["system"]
            if config.get("response_format"):
                kwargs["response_format"] = config["response_format"]
            if config.get("json_schema"):
                kwargs["json_schema"] = config["json_schema"]

        elif node_type == "tool":
            kwargs["tool"] = config.get("tool_name", config.get("tool", ""))
            kwargs["args"] = config.get("args", {})

        elif node_type == "transform":
            kwargs["expr"] = config.get("expr", config.get("expression", "input"))

        elif node_type == "router":
            kwargs["condition"] = config.get("condition", "true")
            kwargs["routes"] = config.get("routes", {})
            kwargs["default"] = config.get("default")

        elif node_type == "gate":
            kwargs["condition"] = config.get("condition", "true")
            kwargs["true_path"] = config.get("true_path", "")
            kwargs["false_path"] = config.get("false_path", "")

        elif node_type == "code":
            kwargs["code"] = config.get("code", "")
            kwargs["language"] = config.get("language", "python")
            # Sandbox configuration
            if config.get("profile") is not None:
                kwargs["profile"] = config.get("profile")
            if config.get("allow_site_packages") is not None:
                kwargs["allow_site_packages"] = bool(config.get("allow_site_packages"))
            if config.get("timeout_ms") is not None:
                kwargs["timeout_ms"] = int(config.get("timeout_ms"))
            if config.get("memory_mb") is not None:
                kwargs["memory_mb"] = int(config.get("memory_mb"))

        elif node_type == "memory_read":
            kwargs["query"] = config.get("query")
            kwargs["key"] = config.get("key")
            kwargs["namespace"] = config.get("namespace", "default")

        elif node_type == "memory_write":
            kwargs["key"] = config.get("key", "")
            kwargs["value_expr"] = config.get("value_expr", "{{input}}")
            kwargs["namespace"] = config.get("namespace", "default")

        return node_class(**kwargs)

    def _pathway_from_dict(self, data: dict[str, Any]) -> Pathway:
        """Create a Pathway from a dictionary representation."""
        nodes_data = data.get("nodes", [])
        connections_data = data.get("connections", [])

        nodes = {}
        for n in nodes_data:
            if isinstance(n, dict):
                node = self._node_from_dict(n)
                nodes[node.id] = node

        connections = []
        for c in connections_data:
            if isinstance(c, str):
                if "→" in c:
                    parts = c.split("→")
                elif "->" in c:
                    parts = c.split("->")
                else:
                    continue
                if len(parts) == 2:
                    connections.append(
                        Connection(
                            from_node=parts[0].strip(),
                            to_node=parts[1].strip(),
                        )
                    )
            elif isinstance(c, dict):
                connections.append(
                    Connection(
                        from_node=c.get("from", c.get("from_node", "")),
                        to_node=c.get("to", c.get("to_node", "")),
                        from_output=c.get("from_output", "output"),
                        to_input=c.get("to_input", "input"),
                    )
                )

        return Pathway(
            id=data.get("id", f"pathway_{uuid.uuid4().hex[:8]}"),
            name=data.get("name"),
            description=data.get("description"),
            nodes=nodes,
            connections=connections,
            metadata=data.get("metadata", {}),
        )

    # =========================================================================
    # NODE CRUD (Studio authoring)
    # =========================================================================

    def add_node(
        self,
        pathway_id: str,
        node_data: dict[str, Any],
    ) -> tuple[Pathway, Any]:
        """Add a node to a pathway.

        Args:
            pathway_id: Pathway ID
            node_data: Node configuration dict with 'type', 'config', optional 'id', 'name'

        Returns:
            Tuple of (updated Pathway, new node)

        Raises:
            ValueError: If pathway not found or node creation fails
        """
        pathway = self.load(pathway_id)
        if pathway is None:
            raise ValueError(f"Pathway not found: {pathway_id}")

        # Create the node
        node = self._node_from_dict(node_data)

        # Check for ID collision
        if node.id in pathway.nodes:
            raise ValueError(f"Node ID already exists: {node.id}")

        # Add to pathway
        pathway.nodes[node.id] = node

        # Persist changes
        self._persist_pathway_changes(pathway_id, pathway)

        # Update cache
        self._registry[pathway_id] = pathway

        # Update meta
        if pathway_id in self._meta:
            self._meta[pathway_id].node_count = len(pathway.nodes)

        logger.debug("Added node %s to pathway %s", node.id, pathway_id)
        return pathway, node

    def update_node(
        self,
        pathway_id: str,
        node_id: str,
        updates: dict[str, Any],
    ) -> tuple[Pathway, Any]:
        """Update a node's configuration.

        Args:
            pathway_id: Pathway ID
            node_id: Node ID to update
            updates: Partial config updates (name, description, config fields)

        Returns:
            Tuple of (updated Pathway, updated node)

        Raises:
            ValueError: If pathway or node not found
        """
        pathway = self.load(pathway_id)
        if pathway is None:
            raise ValueError(f"Pathway not found: {pathway_id}")

        if node_id not in pathway.nodes:
            raise ValueError(f"Node not found: {node_id}")

        old_node = pathway.nodes[node_id]

        # Build updated node data
        node_data = {
            "id": node_id,
            "type": old_node.type,
            "name": updates.get("name", getattr(old_node, "name", None)),
            "description": updates.get(
                "description", getattr(old_node, "description", None)
            ),
            "config": {},
        }

        # Get current config from old node
        current_config = self._serialize_node(old_node).get("config", {})

        # Merge with updates
        if "config" in updates:
            current_config.update(updates["config"])

        node_data["config"] = current_config

        # Create updated node
        new_node = self._node_from_dict(node_data)

        # Replace in pathway
        pathway.nodes[node_id] = new_node

        # Persist changes
        self._persist_pathway_changes(pathway_id, pathway)

        # Update cache
        self._registry[pathway_id] = pathway

        logger.debug("Updated node %s in pathway %s", node_id, pathway_id)
        return pathway, new_node

    def delete_node(
        self,
        pathway_id: str,
        node_id: str,
        *,
        remove_connections: bool = True,
    ) -> Pathway:
        """Delete a node from a pathway.

        Args:
            pathway_id: Pathway ID
            node_id: Node ID to delete
            remove_connections: Also remove connections involving this node

        Returns:
            Updated Pathway

        Raises:
            ValueError: If pathway or node not found
        """
        pathway = self.load(pathway_id)
        if pathway is None:
            raise ValueError(f"Pathway not found: {pathway_id}")

        if node_id not in pathway.nodes:
            raise ValueError(f"Node not found: {node_id}")

        # Remove node
        del pathway.nodes[node_id]

        # Remove associated connections
        if remove_connections:
            pathway.connections = [
                conn
                for conn in pathway.connections
                if conn.from_node != node_id and conn.to_node != node_id
            ]

            # Remove from gates
            pathway.gates = [
                gate
                for gate in pathway.gates
                if gate.true_path != node_id and gate.false_path != node_id
            ]

            # Remove from loops
            for loop in pathway.loops:
                loop.body_nodes = [n for n in loop.body_nodes if n != node_id]

        # Persist changes
        self._persist_pathway_changes(pathway_id, pathway)

        # Update cache
        self._registry[pathway_id] = pathway

        # Update meta
        if pathway_id in self._meta:
            self._meta[pathway_id].node_count = len(pathway.nodes)

        logger.debug("Deleted node %s from pathway %s", node_id, pathway_id)
        return pathway

    # =========================================================================
    # CONNECTION CRUD
    # =========================================================================

    def add_connection(
        self,
        pathway_id: str,
        conn_data: dict[str, Any],
    ) -> tuple[Pathway, Connection]:
        """Add a connection between nodes.

        Args:
            pathway_id: Pathway ID
            conn_data: Connection dict with from_node, to_node, optional from_output, to_input

        Returns:
            Tuple of (updated Pathway, new Connection)

        Raises:
            ValueError: If pathway not found, nodes not found, or connection exists
        """
        pathway = self.load(pathway_id)
        if pathway is None:
            raise ValueError(f"Pathway not found: {pathway_id}")

        from_node = conn_data.get("from_node") or conn_data.get("from", "")
        to_node = conn_data.get("to_node") or conn_data.get("to", "")

        if not from_node or not to_node:
            raise ValueError("Connection requires from_node and to_node")

        # Validate nodes exist
        if from_node not in pathway.nodes:
            raise ValueError(f"Source node not found: {from_node}")
        if to_node not in pathway.nodes:
            raise ValueError(f"Target node not found: {to_node}")

        # Check for self-loop
        if from_node == to_node:
            raise ValueError("Cannot connect a node to itself")

        # Check for duplicate connection
        for existing in pathway.connections:
            if existing.from_node == from_node and existing.to_node == to_node:
                raise ValueError(f"Connection already exists: {from_node} -> {to_node}")

        # Create connection
        connection = Connection(
            from_node=from_node,
            to_node=to_node,
            from_output=conn_data.get("from_output", "output"),
            to_input=conn_data.get("to_input", "input"),
        )

        # Add to pathway
        pathway.connections.append(connection)

        # Reject cycles early (common when agents/LLMs try to "loop" by wiring outputs back upstream).
        try:
            from pathway_engine.application.validation import find_cycle

            cycle = find_cycle(pathway)
        except Exception:
            cycle = None
        if cycle:
            # Undo the append before raising.
            pathway.connections.pop()
            raise ValueError(f"Connection would create a cycle: {' -> '.join(cycle)}")

        # Persist changes
        self._persist_pathway_changes(pathway_id, pathway)

        # Update cache
        self._registry[pathway_id] = pathway

        logger.debug(
            "Added connection %s -> %s in pathway %s", from_node, to_node, pathway_id
        )
        return pathway, connection

    def delete_connection(
        self,
        pathway_id: str,
        from_node: str,
        to_node: str,
    ) -> Pathway:
        """Delete a connection between nodes.

        Args:
            pathway_id: Pathway ID
            from_node: Source node ID
            to_node: Target node ID

        Returns:
            Updated Pathway

        Raises:
            ValueError: If pathway not found or connection not found
        """
        pathway = self.load(pathway_id)
        if pathway is None:
            raise ValueError(f"Pathway not found: {pathway_id}")

        # Find and remove connection
        original_count = len(pathway.connections)
        pathway.connections = [
            conn
            for conn in pathway.connections
            if not (conn.from_node == from_node and conn.to_node == to_node)
        ]

        if len(pathway.connections) == original_count:
            raise ValueError(f"Connection not found: {from_node} -> {to_node}")

        # Persist changes
        self._persist_pathway_changes(pathway_id, pathway)

        # Update cache
        self._registry[pathway_id] = pathway

        logger.debug(
            "Deleted connection %s -> %s in pathway %s", from_node, to_node, pathway_id
        )
        return pathway

    # =========================================================================
    # PATHWAY METADATA & DELETE
    # =========================================================================

    def update(
        self,
        pathway_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PathwayMeta:
        """Update pathway metadata.

        Args:
            pathway_id: Pathway ID
            name: New name (None to keep existing)
            description: New description (None to keep existing)
            metadata: Additional metadata to merge

        Returns:
            Updated PathwayMeta

        Raises:
            ValueError: If pathway not found
        """
        pathway = self.load(pathway_id)
        if pathway is None:
            raise ValueError(f"Pathway not found: {pathway_id}")

        # Update fields
        if name is not None:
            pathway.name = name
        if description is not None:
            pathway.description = description
        if metadata is not None:
            pathway.metadata.update(metadata)

        # Persist changes
        self._persist_pathway_changes(pathway_id, pathway)

        # Update cache
        self._registry[pathway_id] = pathway

        # Update meta
        meta = self._meta.get(pathway_id)
        if meta:
            if name is not None:
                meta.name = name
            if description is not None:
                meta.description = description
        else:
            meta = PathwayMeta(
                id=pathway_id,
                name=pathway.name,
                description=pathway.description,
                source="user:updated",
                version=None,
                doc_id=None,
                node_count=len(pathway.nodes),
            )
            self._meta[pathway_id] = meta

        logger.debug("Updated pathway metadata: %s", pathway_id)
        return meta

    def delete(self, pathway_id: str) -> bool:
        """Delete a pathway.

        Args:
            pathway_id: Pathway ID

        Returns:
            True if deleted, False if not found
        """
        # Check if exists
        if pathway_id not in self._registry and pathway_id not in self._meta:
            # Try to load from storage to verify existence
            pathway = self.load(pathway_id)
            if pathway is None:
                return False

        # Remove from registry
        self._registry.pop(pathway_id, None)

        # Remove from meta
        meta = self._meta.pop(pathway_id, None)

        # Remove from storage
        if meta and meta.doc_id and self._store:
            try:
                # Delete document if we have a store
                delete_fn = getattr(self._store, "delete_document", None)
                if callable(delete_fn):
                    delete_fn(meta.doc_id)
            except Exception as e:
                logger.warning("Failed to delete pathway document: %s", e)

        logger.debug("Deleted pathway: %s", pathway_id)
        return True

    # =========================================================================
    # PERSISTENCE HELPERS
    # =========================================================================

    def _persist_pathway_changes(self, pathway_id: str, pathway: Pathway) -> None:
        """Persist pathway changes to storage.

        This is called after any modification to sync to the store.
        """
        if not self._store:
            return

        # Get existing doc_id from meta
        meta = self._meta.get(pathway_id)
        doc_id = meta.doc_id if meta else None

        if not doc_id:
            # No existing document - create new one
            ws_id = self._default_workspace_id
            if ws_id:
                doc_id = self._persist_pathway(
                    pathway,
                    source=meta.source if meta else "user:api",
                    workspace_id=ws_id,
                )
                if meta and doc_id:
                    meta.doc_id = doc_id
            return

        try:
            # Update existing document revision
            content = {
                "id": pathway.id,
                "name": pathway.name,
                "description": pathway.description,
                "source": meta.source if meta else "user:api",
                "version": meta.version if meta else None,
                "nodes": [
                    self._serialize_node(node) for node in pathway.nodes.values()
                ],
                "connections": [
                    {
                        "from": c.from_node,
                        "to": c.to_node,
                        "from_output": c.from_output,
                        "to_input": c.to_input,
                    }
                    for c in pathway.connections
                ],
                "metadata": dict(pathway.metadata),
            }

            rev_id = f"rev_{uuid.uuid4().hex[:12]}"
            self._store.write_revision(doc_id=doc_id, rev_id=rev_id, content=content)
            self._store.upsert_document(
                {
                    "id": doc_id,
                    "head_rev": rev_id,
                    "name": pathway.name or pathway.id,
                }
            )

        except Exception as e:
            logger.error("Failed to persist pathway changes: %s", e)


__all__ = [
    "PathwayService",
    "PathwaySource",
    "PathwayMeta",
]
