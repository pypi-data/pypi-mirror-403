"""Tool Calling Nodes - Typed, reliable tool calling infrastructure.

This module provides:
- ToolCall / ToolResult DTOs - canonical types for tool interactions
- ToolCallingLLMNode - LLM with function calling, outputs structured calls
- ToolExecutorNode - Executes tool calls, outputs structured results

Usage:
    from pathway_engine.domain.nodes.tool_calling import ToolCallingLLMNode, ToolExecutorNode
    from pathway_engine.domain.nodes.core import LLMNode
    
    # Plan and execute tools
    plan = ToolCallingLLMNode(
        id="plan",
        prompt="Help the user: {{message}}",
        tools=["pathway.create", "pathway.run", "workspace.read_file"],
    )
    execute = ToolExecutorNode(id="execute")
    respond = LLMNode(id="respond", prompt="Results: {{execute.results}}\nRespond to: {{message}}")
    
    pathway = plan >> execute >> respond
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from pydantic import Field

from pathway_engine.domain.nodes.base import NodeBase
from pathway_engine.domain.context import Context

# Import DTOs from models - single source of truth
from pathway_engine.domain.models.tool import (
    ToolCall,
    ToolResult,
    ToolCallPlan,
    ToolExecutionResult,
)
from pathway_engine.domain.models.tool_calling_llm import ToolCallingLLMOutput

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL SCHEMA REGISTRY
# =============================================================================


def get_tool_schemas_for_names(
    tool_names: list[str],
    ctx: Context,
) -> list[dict[str, Any]]:
    """Get OpenAI-format tool schemas for the given tool names.

    Supports wildcards like "pathway.*" to include all pathway tools.
    """
    # Prefer explicit tool definitions (stdlib, host wiring) when provided.
    tool_definitions = ctx.services.tool_definitions
    if not isinstance(tool_definitions, dict):
        tool_definitions = {}

    # Get available tools from context (fallback)
    available = list(ctx.tools.keys())
    if tool_definitions:
        available = sorted(
            {*available, *[k for k in tool_definitions.keys() if isinstance(k, str)]}
        )

    # Expand wildcards
    expanded_names = []
    for name in tool_names:
        if name.endswith(".*"):
            prefix = name[:-2]
            expanded_names.extend(t for t in available if t.startswith(prefix + "."))
        elif name == "*":
            expanded_names.extend(available)
        else:
            if name in available:
                expanded_names.append(name)

    # Build schemas
    schemas = []
    for name in expanded_names:
        schema = None
        if (
            tool_definitions
            and name in tool_definitions
            and isinstance(tool_definitions[name], dict)
        ):
            defn = tool_definitions[name]
            # Sanitize name for OpenAI compatibility (no dots allowed)
            safe_name = name.replace(".", "_")
            schema = {
                "type": "function",
                "function": {
                    "name": safe_name,
                    "description": str(defn.get("description", "") or ""),
                    "parameters": defn.get("parameters")
                    or {"type": "object", "properties": {}, "required": []},
                },
            }
        else:
            # Fallback to built-in minimal schemas (dev/test-friendly).
            schema = _get_tool_schema(name)
        if schema:
            schemas.append(schema)

    return schemas


def _get_tool_schema(name: str) -> dict[str, Any] | None:
    """Get schema for a single tool."""
    # Built-in tool schemas
    TOOL_SCHEMAS = {
        "pathway.create": {
            "type": "function",
            "function": {
                "name": "pathway_create",
                "description": "Create an automation pathway with nodes and connections",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Pathway name"},
                        "description": {
                            "type": "string",
                            "description": "What the pathway does",
                        },
                        "nodes": {
                            "type": "array",
                            "description": "List of nodes",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "type": {
                                        "type": "string",
                                        "enum": ["llm", "tool", "transform", "router"],
                                    },
                                    "config": {"type": "object"},
                                },
                                "required": ["id", "type"],
                            },
                        },
                        "connections": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Connections like 'node_a → node_b'",
                        },
                    },
                    "required": ["name"],
                },
            },
        },
        "pathway.run": {
            "type": "function",
            "function": {
                "name": "pathway_run",
                "description": "Execute a pathway with inputs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "Pathway document ID to run (doc_...)",
                        },
                        "inputs": {
                            "type": "object",
                            "description": "Input data for the pathway",
                        },
                    },
                    "required": ["doc_id"],
                },
            },
        },
        "workspace.read_file": {
            "type": "function",
            "function": {
                "name": "workspace_read_file",
                "description": "Read a file from the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                    },
                    "required": ["path"],
                },
            },
        },
        "workspace.write_file": {
            "type": "function",
            "function": {
                "name": "workspace_write_file",
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {
                            "type": "string",
                            "description": "Content to write",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        },
        "workspace.list_files": {
            "type": "function",
            "function": {
                "name": "workspace_list_files",
                "description": "List files in a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                    },
                },
            },
        },
        "search.semantic": {
            "type": "function",
            "function": {
                "name": "search_semantic",
                "description": "Semantic search using AI embeddings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {
                            "type": "integer",
                            "description": "Max results",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    }

    return TOOL_SCHEMAS.get(name)


def _openai_name_to_tool_name(openai_name: str) -> str:
    """Convert OpenAI function name back to tool name."""
    # pathway_create -> pathway.create
    parts = openai_name.split("_", 1)
    if len(parts) == 2:
        return f"{parts[0]}.{parts[1]}"
    return openai_name


# =============================================================================
# TOOL CALLING LLM NODE
# =============================================================================


class ToolCallingLLMNode(NodeBase):
    """LLM node with function calling support.

    Sends tool schemas to the LLM, receives structured tool calls back.
    Outputs typed ToolCall objects, not just JSON strings.

    Attributes:
        prompt: User prompt template
        tools: List of tool names to expose (supports wildcards like "pathway.*")
        model: Model to use (must support function calling)
        system: Optional system prompt
        tool_choice: "auto", "required", or specific tool name
        images: Optional list of base64 images for vision (gpt-4o, claude-3, etc.)
    """

    type: Literal["tool_calling_llm"] = "tool_calling_llm"
    prompt: str
    tools: list[str] = Field(default_factory=list)
    model: str = "auto"  # "auto" uses capability routing for tool_calling
    system: str | None = None
    tool_choice: str = "auto"  # "auto", "required", "none", or tool name
    images: str | list[str] | None = None  # Vision: base64 images or template

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Call LLM with function calling, return typed tool calls."""
        # Format prompt
        formatted_prompt = self._format_template(self.prompt, inputs)
        formatted_system = (
            self._format_template(self.system, inputs) if self.system else None
        )

        # Resolve images for vision
        resolved_images: list[str] | None = None
        if self.images is not None:
            if isinstance(self.images, str) and "{{" in self.images:
                raw = self._resolve_path(inputs, self.images.strip("{}"))
                if isinstance(raw, list):
                    resolved_images = [str(img) for img in raw if img]
                elif isinstance(raw, str) and raw:
                    resolved_images = [raw]
            elif isinstance(self.images, list):
                resolved_images = [str(img) for img in self.images if img]
            elif isinstance(self.images, str) and self.images:
                resolved_images = [self.images]

        # Get tool schemas
        tool_schemas = get_tool_schemas_for_names(self.tools, ctx)

        # Get LLM handler
        llm_generate = ctx.tools.get("llm.generate")
        if not llm_generate:
            raise RuntimeError("llm.generate tool not available")

        # Build tool_choice parameter
        tool_choice_param = self.tool_choice
        if self.tool_choice not in ("auto", "required", "none"):
            # Specific tool name - format for OpenAI
            tool_choice_param = {
                "type": "function",
                "function": {"name": self.tool_choice},
            }

        # Build request
        request: dict[str, Any] = {
            "prompt": formatted_prompt,
            "model": self.model,
            "system": formatted_system,
            "tools": tool_schemas if tool_schemas else None,
            "tool_choice": tool_choice_param if tool_schemas else None,
        }

        # Add images for vision models
        if resolved_images:
            request["images"] = resolved_images

        # Call LLM with tools
        result = await llm_generate(request, ctx)

        # Parse tool calls from response.
        # Providers may explicitly return `tool_calls: null`. Normalize to [] so enumerate() is safe.
        raw_tool_calls = result.get("tool_calls") or []
        tool_calls: list[ToolCall] = []

        for i, tc in enumerate(raw_tool_calls):
            try:
                # Handle OpenAI format
                if isinstance(tc, dict):
                    func = tc.get("function", tc)
                    tool_name = _openai_name_to_tool_name(func.get("name", ""))

                    # Parse arguments
                    args = func.get("arguments", {})
                    if isinstance(args, str):
                        args = json.loads(args)

                    tool_calls.append(
                        ToolCall(
                            id=tc.get("id", f"call_{i}"),
                            tool=tool_name,
                            args=args,
                        )
                    )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Specific parsing errors
                logger.warning(
                    "Failed to parse tool call: error_type=%s, error=%s, tool_call=%s",
                    type(e).__name__,
                    e,
                    tc,
                )
            except Exception as e:
                # Unexpected parsing errors
                logger.error(
                    "Unexpected error parsing tool call: error_type=%s, error=%s, tool_call=%s",
                    type(e).__name__,
                    e,
                    tc,
                    exc_info=True,
                )

        # Build plan
        plan = ToolCallPlan(
            calls=tool_calls,
            reasoning=result.get("content"),  # LLM might explain its reasoning
        )

        logger.info(
            "[ToolCallingLLM] Generated %d tool calls: %s",
            len(tool_calls),
            [tc.tool for tc in tool_calls],
        )

        # Return typed plan and tool calls for downstream executor
        return {
            "tool_calls": [tc.model_dump() for tc in tool_calls],
            "plan": plan.model_dump(),
            "reasoning": plan.reasoning,
            "response": result.get("content", ""),
            "model": result.get("model"),
        }


# =============================================================================
# TOOL EXECUTOR NODE
# =============================================================================


class ToolExecutorNode(NodeBase):
    """Executes tool calls and returns structured results.

    Takes tool calls from any source (ToolCallingLLMNode, plan_tools, etc.)
    and actually executes them via ctx.tools.

    Attributes:
        input_key: Key in inputs containing tool calls (default: "tool_calls")
        continue_on_error: Whether to continue if a tool fails
    """

    type: Literal["tool_executor"] = "tool_executor"
    input_key: str = "tool_calls"
    continue_on_error: bool = True

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute tool calls and return results."""
        # Get tool calls from inputs - try multiple locations
        raw_calls = []

        # 1. Direct key (e.g., "tool_calls")
        if self.input_key in inputs:
            raw_calls = inputs[self.input_key]

        # 2. Check upstream node outputs (e.g., "agent.tool_calls")
        if not raw_calls:
            for key, value in inputs.items():
                if isinstance(value, dict):
                    if self.input_key in value:
                        raw_calls = value[self.input_key]
                        logger.debug(
                            f"[ToolExecutor] Found tool_calls in {key}.{self.input_key}"
                        )
                        break
                    if "plan" in value and isinstance(value["plan"], dict):
                        raw_calls = value["plan"].get("calls", [])
                        if raw_calls:
                            logger.debug(
                                f"[ToolExecutor] Found tool_calls in {key}.plan.calls"
                            )
                            break

        # 3. Direct plan.calls format
        if not raw_calls and "plan" in inputs:
            plan = inputs["plan"]
            if isinstance(plan, dict):
                raw_calls = plan.get("calls", [])

        # Parse into ToolCall objects
        tool_calls: list[ToolCall] = []
        for tc in raw_calls:
            if isinstance(tc, ToolCall):
                tool_calls.append(tc)
            elif isinstance(tc, dict):
                tool_calls.append(ToolCall(**tc))

        if not tool_calls:
            logger.debug("[ToolExecutor] No tool calls to execute")
            return {
                "results": [],
                "all_succeeded": True,
                "summary": "No tools were called",
            }

        # Execute each tool call
        results: list[ToolResult] = []
        all_succeeded = True

        for call in tool_calls:
            logger.info("[ToolExecutor] Executing: %s(%s)", call.tool, call.args)

            handler = ctx.tools.get(call.tool)
            if not handler:
                result = ToolResult(
                    call_id=call.id,
                    tool=call.tool,
                    success=False,
                    error=f"Tool not found: {call.tool}",
                )
                all_succeeded = False
            else:
                try:
                    output = await handler(call.args, ctx)
                    result = ToolResult(
                        call_id=call.id,
                        tool=call.tool,
                        success=True,
                        output=output,
                    )
                    logger.info("[ToolExecutor] %s succeeded", call.tool)
                except Exception as e:
                    error_type = type(e).__name__
                    error_msg = str(e)
                    logger.error(
                        "[ToolExecutor] Tool execution failed: tool=%s, call_id=%s, error_type=%s, error=%s",
                        call.tool,
                        call.id,
                        error_type,
                        error_msg,
                        exc_info=True,
                    )
                    result = ToolResult(
                        call_id=call.id,
                        tool=call.tool,
                        success=False,
                        error=error_msg,
                    )
                    all_succeeded = False

                    if not self.continue_on_error:
                        results.append(result)
                        break

            results.append(result)

        # Build typed execution result
        execution = ToolExecutionResult(
            results=results,
            all_succeeded=all_succeeded,
            summary=f"Executed {len(results)} tools, {sum(1 for r in results if r.success)} succeeded",
        )

        logger.info("[ToolExecutor] %s", execution.summary)

        # Return as dict for VM compatibility
        # Include upstream passthrough for multi-node data flow
        output = execution.model_dump()

        # Passthrough upstream data so downstream nodes can access it
        for key, value in inputs.items():
            if key not in output and isinstance(value, dict):
                output[f"upstream_{key}"] = value

        return output


__all__ = [
    # DTOs
    "ToolCall",
    "ToolResult",
    "ToolCallPlan",
    "ToolExecutionResult",
    # Nodes
    "ToolCallingLLMNode",
    "ToolExecutorNode",
    # Utilities
    "get_tool_schemas_for_names",
]
