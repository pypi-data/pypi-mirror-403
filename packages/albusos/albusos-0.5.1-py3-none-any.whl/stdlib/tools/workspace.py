"""Workspace Tools - File and document operations.

These are callable capabilities for pathways to interact with the workspace.
All operations use StudioDomainPort for proper document management.

Tools receive dependencies via ToolContext - no globals, no service locators.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("workspace.read_file")
async def read_file(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Read a file from the workspace.

    Inputs:
        path: File path relative to workspace root

    Returns:
        content: File content as string
        exists: Whether file exists
    """
    path = str(inputs.get("path", "")).strip()
    if not path:
        return {"success": False, "error": "path is required", "exists": False}

    workspace_id = context.workspace_id

    # Read via studio domain (for documents)
    if context.domain and workspace_id:
        try:
            # Check if this is a document reference
            if path.startswith("doc_"):
                doc = context.domain.get_document(doc_id=path)
                if doc:
                    try:
                        content = context.domain.get_head_content(doc_id=path)
                        return {
                            "success": True,
                            "path": path,
                            "content": str(content),
                            "exists": True,
                            "doc_id": doc.id,
                            "doc_type": doc.type,
                        }
                    except Exception:
                        return {
                            "success": True,
                            "path": path,
                            "content": "",
                            "exists": True,
                            "doc_id": doc.id,
                            "doc_type": doc.type,
                            "note": "Document exists but has no content revision yet",
                        }
        except Exception as e:
            logger.debug("Document lookup failed for %s: %s", path, e)

    # Fall back to file system read
    try:
        root = os.getenv("AGENT_STDLIB_WORKSPACE_ROOT", "data/studio")
        if workspace_id:
            full_path = os.path.join(root, str(workspace_id), path)
        else:
            full_path = os.path.join(root, path)

        # Normalize and check path safety
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(os.path.normpath(root)):
            return {
                "success": False,
                "error": "path outside workspace",
                "exists": False,
            }

        if os.path.isfile(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "success": True,
                "path": path,
                "content": content,
                "exists": True,
                "size_bytes": len(content),
            }
        else:
            return {
                "success": False,
                "path": path,
                "exists": False,
                "error": "file not found",
            }
    except Exception as e:
        logger.warning("File read failed for %s: %s", path, e)
        return {"success": False, "path": path, "exists": False, "error": str(e)}


@register_tool("workspace.write_file")
async def write_file(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Write content to a file in the workspace.

    Inputs:
        path: File path relative to workspace root
        content: Content to write

    Returns:
        success: Whether write succeeded
    """
    path = str(inputs.get("path", "")).strip()
    content = str(inputs.get("content", ""))

    if not path:
        return {"success": False, "error": "path is required"}

    workspace_id = context.workspace_id

    # Write via studio domain (for documents)
    if context.domain and workspace_id:
        try:
            # If path is a doc_id, update document content
            if path.startswith("doc_"):
                doc = context.domain.get_document(doc_id=path)
                if doc:
                    rev = context.domain.save_revision(
                        doc_id=path,
                        content={"text": content, "raw": content},
                    )
                    return {
                        "success": True,
                        "path": path,
                        "doc_id": doc.id,
                        "rev_id": rev.rev_id,
                        "bytes_written": len(content),
                    }
        except Exception as e:
            logger.debug("Document write failed for %s: %s", path, e)

    # Fall back to file system write
    try:
        root = os.getenv("AGENT_STDLIB_WORKSPACE_ROOT", "data/studio")
        if workspace_id:
            full_path = os.path.join(root, str(workspace_id), path)
        else:
            full_path = os.path.join(root, path)

        # Normalize and check path safety
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(os.path.normpath(root)):
            return {"success": False, "error": "path outside workspace"}

        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "path": path,
            "bytes_written": len(content),
        }
    except Exception as e:
        logger.warning("File write failed for %s: %s", path, e)
        return {"success": False, "path": path, "error": str(e)}


@register_tool("workspace.list_files")
async def list_files(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """List files in a workspace directory.

    Inputs:
        path: Directory path (default: root)
        pattern: Glob pattern to filter (optional)

    Returns:
        files: List of file paths
    """
    path = str(inputs.get("path", "")).strip() or ""
    pattern = str(inputs.get("pattern", "*")).strip()
    workspace_id = context.workspace_id

    # List via studio domain (for documents/folders)
    if context.domain and workspace_id:
        try:
            # Get tree for workspace
            tree = context.domain.get_tree(workspace_id=str(workspace_id))

            files = []
            folders = []

            # Extract documents and folders from tree
            def extract_items(node: Any, prefix: str = "") -> None:
                if hasattr(node, "documents"):
                    for doc in node.documents:
                        doc_path = f"{prefix}/{doc.name}" if prefix else doc.name
                        files.append(
                            {
                                "path": doc_path,
                                "type": "document",
                                "doc_type": getattr(doc, "type", "unknown"),
                                "doc_id": getattr(doc, "id", ""),
                            }
                        )
                if hasattr(node, "folders"):
                    for folder in node.folders:
                        folder_path = (
                            f"{prefix}/{folder.name}" if prefix else folder.name
                        )
                        folders.append(
                            {
                                "path": folder_path,
                                "type": "folder",
                                "folder_id": getattr(folder, "id", ""),
                            }
                        )
                        # Recurse into folder
                        extract_items(folder, folder_path)

            extract_items(tree)

            return {
                "success": True,
                "path": path,
                "pattern": pattern,
                "files": files,
                "folders": folders,
                "total_documents": len(files),
                "total_folders": len(folders),
            }
        except Exception as e:
            logger.debug("Studio tree listing failed: %s", e)

    # Fall back to file system listing
    try:
        import glob as glob_module

        root = os.getenv("AGENT_STDLIB_WORKSPACE_ROOT", "data/studio")
        if workspace_id:
            base_path = os.path.join(root, str(workspace_id), path)
        else:
            base_path = os.path.join(root, path)

        base_path = os.path.normpath(base_path)
        if not base_path.startswith(os.path.normpath(root)):
            return {"success": False, "error": "path outside workspace", "files": []}

        if not os.path.isdir(base_path):
            return {
                "success": False,
                "error": "directory not found",
                "files": [],
                "path": path,
            }

        # List files matching pattern
        search_pattern = os.path.join(base_path, pattern)
        matches = glob_module.glob(search_pattern)

        files = []
        folders = []
        for match in matches[:100]:  # Limit results
            rel_path = os.path.relpath(match, base_path)
            if os.path.isfile(match):
                files.append(
                    {
                        "path": rel_path,
                        "type": "file",
                        "size_bytes": os.path.getsize(match),
                    }
                )
            elif os.path.isdir(match):
                folders.append(
                    {
                        "path": rel_path,
                        "type": "folder",
                    }
                )

        return {
            "success": True,
            "path": path,
            "pattern": pattern,
            "files": files,
            "folders": folders,
        }
    except Exception as e:
        logger.warning("File listing failed for %s: %s", path, e)
        return {"success": False, "path": path, "error": str(e), "files": []}


@register_tool("workspace.create_document")
async def create_document(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Create a new document in the workspace.

    Inputs:
        name: Document name
        content: Initial content (optional)
        doc_type: Document type (default: "text")
        parent_id: Parent folder ID (optional)

    Returns:
        document_id: Created document ID
    """
    name = str(inputs.get("name", "")).strip()
    content = inputs.get("content", "")
    doc_type = str(inputs.get("doc_type", "text")).strip()
    parent_id = inputs.get("parent_id")

    if not name:
        return {"success": False, "error": "name is required"}

    workspace_id = context.workspace_id

    if context.domain and workspace_id:
        try:
            # Map common user/tool synonyms to canonical DocType values
            # (see `persistence.domain.contracts.studio.DocType`)
            type_mapping = {
                "markdown": "text",
                "md": "text",
                "text": "text",
                "pathway": "pathway",
                "flow": "pathway",
                "graph": "pathway",
                "agent": "agent",
                "artifact": "artifact",
                "asset": "asset",
            }
            mapped_type = type_mapping.get(doc_type.lower(), "text")

            # Create document
            doc = context.domain.create_document(
                doc_type=mapped_type,
                name=name,
                parent_id=parent_id,
                workspace_id=str(workspace_id),
                metadata={"created_by": "pathway"},
            )

            # Save initial content if provided
            if content:
                rev = context.domain.save_revision(
                    doc_id=doc.id,
                    content={"text": str(content), "raw": str(content)},
                )
                return {
                    "success": True,
                    "document_id": doc.id,
                    "name": name,
                    "doc_type": mapped_type,
                    "rev_id": rev.rev_id,
                }

            return {
                "success": True,
                "document_id": doc.id,
                "name": name,
                "doc_type": mapped_type,
            }
        except Exception as e:
            logger.warning("Document creation failed: %s", e)
            return {"success": False, "error": str(e)}

    # Without domain, we can't create proper documents
    return {"success": False, "error": "workspace not available"}


@register_tool("workspace.delete_file")
async def delete_file(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Delete a file or document from the workspace.

    Inputs:
        path: File path or document ID

    Returns:
        success: Whether deletion succeeded
    """
    path = str(inputs.get("path", "")).strip()
    if not path:
        return {"success": False, "error": "path is required"}

    workspace_id = context.workspace_id

    if context.domain and workspace_id:
        try:
            # If it's a document ID, trash it via studio
            if path.startswith("doc_"):
                context.domain.trash_document(doc_id=path)
                return {"success": True, "path": path, "action": "trashed"}
        except Exception as e:
            logger.debug("Document trash failed for %s: %s", path, e)

    # Fall back to file system delete
    try:
        root = os.getenv("AGENT_STDLIB_WORKSPACE_ROOT", "data/studio")
        if workspace_id:
            full_path = os.path.join(root, str(workspace_id), path)
        else:
            full_path = os.path.join(root, path)

        full_path = os.path.normpath(full_path)
        if not full_path.startswith(os.path.normpath(root)):
            return {"success": False, "error": "path outside workspace"}

        if os.path.isfile(full_path):
            os.remove(full_path)
            return {"success": True, "path": path, "action": "deleted"}
        else:
            return {"success": False, "path": path, "error": "file not found"}
    except Exception as e:
        logger.warning("File deletion failed for %s: %s", path, e)
        return {"success": False, "path": path, "error": str(e)}


@register_tool("workspace.get_info")
async def get_workspace_info(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Get information about the current workspace.

    Returns:
        workspace_id: Current workspace ID
        name: Workspace name
        document_count: Number of documents
        folder_count: Number of folders
    """
    workspace_id = context.workspace_id

    if context.domain and workspace_id:
        try:
            workspace = context.domain.get_workspace(workspace_id=str(workspace_id))
            tree = context.domain.get_tree(workspace_id=str(workspace_id))

            # Count items in tree
            doc_count = 0
            folder_count = 0

            def count_items(node: Any) -> None:
                nonlocal doc_count, folder_count
                if hasattr(node, "documents"):
                    doc_count += len(node.documents)
                if hasattr(node, "folders"):
                    folder_count += len(node.folders)
                    for folder in node.folders:
                        count_items(folder)

            count_items(tree)

            return {
                "success": True,
                "workspace_id": workspace.id,
                "name": workspace.name,
                "document_count": doc_count,
                "folder_count": folder_count,
            }
        except Exception as e:
            logger.warning("Workspace info failed: %s", e)
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "workspace not available"}
