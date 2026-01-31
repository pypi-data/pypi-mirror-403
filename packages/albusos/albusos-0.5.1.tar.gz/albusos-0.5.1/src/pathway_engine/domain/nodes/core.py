"""Typed Node Classes - Nodes that know how to execute themselves.

Each node type:
1. Is a Pydantic model (serializable)
2. Has typed fields (IDE autocomplete, validation)
3. Implements compute() (executable)

No resolvers needed - the node class defines its own execution.

Usage:
    node = LLMNode(prompt="Analyze: {{input}}")  # Uses auto model routing
    node = LLMNode(prompt="Analyze: {{input}}", model="qwen2.5:7b")  # Explicit model
    result = await node.compute({"input": "hello"}, ctx)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from pathway_engine.domain.nodes.base import NodeBase
from pathway_engine.domain.context import Context
from pathway_engine.domain.models.llm import LLMOutput


# =============================================================================
# COMPUTE NODES
# =============================================================================


class LLMNode(NodeBase):
    """LLM completion node.

    Calls ctx.tools["llm.generate"] to generate text.

    Attributes:
        prompt: Template with {{var}} placeholders
        model: "auto" (uses capability routing) or explicit model name (e.g., "qwen2.5:7b")
        temperature: Sampling temperature
        max_tokens: Maximum output tokens
        system: System prompt (optional)
        response_format: "text" or "json"
        json_schema: JSON schema if response_format="json"
        images: Optional list of base64 images or template (for vision models)
                Can be: "{{var}}" template, list of base64 strings, or list of URLs

    Vision example:
        LLMNode(
            id="ocr",
            prompt="Extract text from these images",
            model="gpt-4o",
            images="{{uploaded_images}}",  # Template resolves to list of base64
        )
    """

    type: Literal["llm"] = "llm"
    prompt: str
    model: str = "auto"  # "auto" uses capability routing; explicit names used directly
    temperature: float = 0.7
    max_tokens: int | None = None
    system: str | None = None
    response_format: Literal["text", "json"] = "text"
    json_schema: dict[str, Any] | None = None
    images: str | list[str] | None = None  # Vision: base64 images or template

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute LLM call. Returns LLMOutput as dict for VM compatibility."""
        # Format prompt with inputs (templates only for prompts!)
        formatted_prompt = self._format_template(self.prompt, inputs)
        formatted_system = (
            self._format_template(self.system, inputs) if self.system else None
        )

        # Resolve images for vision (can be template or literal list)
        resolved_images: list[str] | None = None
        if self.images is not None:
            if isinstance(self.images, str) and "{{" in self.images:
                # Template - resolve it
                raw = self._resolve_path(inputs, self.images.strip("{}"))
                if isinstance(raw, list):
                    resolved_images = [str(img) for img in raw if img]
                elif isinstance(raw, str) and raw:
                    resolved_images = [raw]
            elif isinstance(self.images, list):
                resolved_images = [str(img) for img in self.images if img]
            elif isinstance(self.images, str) and self.images:
                resolved_images = [self.images]

        # Prefer llm.json for structured output so schemas are actually enforced and parsed.
        # Fall back to llm.generate when llm.json isn't available (e.g., minimal test contexts).
        # Note: llm.json doesn't support images yet, so we skip it when images are present.
        if (
            self.response_format == "json"
            and self.json_schema is not None
            and "llm.json" in ctx.tools
            and not resolved_images  # Skip llm.json for vision requests
        ):
            llm_json = ctx.tools.get("llm.json")
            if not llm_json:
                raise RuntimeError("llm.json tool not available in context")

            req: dict[str, Any] = {
                "prompt": formatted_prompt,
                "schema": self.json_schema,
                "model": self.model,
                "temperature": self.temperature,
            }
            if self.max_tokens is not None:
                req["max_tokens"] = self.max_tokens
            # NOTE: llm.json doesn't currently accept `system`; if we need it, we can
            # extend llm.json to forward system → llm.generate.

            result = await llm_json(req, ctx)
            if not result.get("success", True):
                raise RuntimeError(result.get("error") or "llm.json call failed")

            response = result.get("content", "")
            model_used = result.get("model", self.model)
            usage = result.get("usage")  # may be absent
            parsed = result.get("data")
        else:
            # Get LLM tool
            llm_generate = ctx.tools.get("llm.generate")
            if not llm_generate:
                raise RuntimeError("llm.generate tool not available in context")

            # Build request
            prompt_to_send = formatted_prompt
            if self.response_format == "json" and self.json_schema is not None:
                # Best-effort schema injection when llm.json isn't available.
                # (This mirrors llm.json behavior but keeps node-level independence.)
                import json as _json

                prompt_to_send = (
                    f"{formatted_prompt}\n\n"
                    "Respond with JSON matching this schema. Return JSON only.\n"
                    f"```json\n{_json.dumps(self.json_schema, indent=2)}\n```"
                )

            request: dict[str, Any] = {
                "prompt": prompt_to_send,
                "model": self.model,
                "temperature": self.temperature,
            }
            if self.max_tokens is not None:
                request["max_tokens"] = self.max_tokens
            if formatted_system:
                request["system"] = formatted_system
            if self.response_format != "text":
                request["response_format"] = self.response_format

            # Add images for vision models
            if resolved_images:
                request["images"] = resolved_images

            # Call LLM
            result = await llm_generate(request, ctx)
            if not result.get("success", True):
                raise RuntimeError(result.get("error") or "llm.generate call failed")

            response = result.get(
                "content", result.get("text", result.get("response", ""))
            )
            model_used = result.get("model", self.model)
            usage = result.get("usage")
            parsed = None

        # Build typed output
        output = LLMOutput(
            response=response,
            model=model_used,
            usage=usage,
            metadata={"parsed": parsed},
        )

        # Parse JSON if requested (best-effort when llm.json isn't used)
        if (
            output.metadata.get("parsed") is None
            and self.response_format == "json"
            and isinstance(response, str)
        ):
            import json

            try:
                parsed = json.loads(response)
                output.metadata["parsed"] = parsed
            except json.JSONDecodeError:
                # Best-effort: some providers still wrap JSON in prose/markdown.
                # Try to salvage the first JSON object we can find.
                try:
                    s = response.strip()
                    # Prefer fenced ```json blocks if present
                    if "```" in s:
                        import re

                        m = re.search(
                            r"```(?:json)?\s*([\s\S]*?)\s*```", s, re.IGNORECASE
                        )
                        if m:
                            candidate = m.group(1).strip()
                            output.metadata["parsed"] = json.loads(candidate)
                            return output.model_dump()
                    # Otherwise, try from first '{' to last '}'.
                    i = s.find("{")
                    j = s.rfind("}")
                    if i != -1 and j != -1 and j > i:
                        candidate = s[i : j + 1]
                        output.metadata["parsed"] = json.loads(candidate)
                except Exception:
                    pass

            # Final fallback: if parsing still failed but a schema exists and llm.json is available,
            # ask llm.json to re-emit strictly-valid JSON matching the schema.
            if (
                output.metadata.get("parsed") is None
                and self.json_schema is not None
                and "llm.json" in ctx.tools
            ):
                llm_json = ctx.tools.get("llm.json")
                if llm_json:
                    repair_prompt = (
                        "Fix the following draft so it is valid JSON and matches the schema exactly. "
                        "Return JSON only.\n\nDRAFT:\n"
                        + response
                    )
                    try:
                        repaired = await llm_json(
                            {
                                "prompt": repair_prompt,
                                "schema": self.json_schema,
                                "model": self.model,
                                "temperature": 0.0,
                            },
                            ctx,
                        )
                        if repaired.get("success", True) and repaired.get("data") is not None:
                            output.metadata["parsed"] = repaired.get("data")
                            # Prefer the repaired canonical JSON text, if available.
                            if isinstance(repaired.get("content"), str) and repaired.get("content"):
                                output.response = repaired["content"]
                    except Exception:
                        # Keep best-effort behavior; don't fail the node just because repair failed.
                        pass

        # Return as dict for VM compatibility - the VM expects dict outputs for interpolation
        return output.model_dump()


class ToolNode(NodeBase):
    """Tool invocation node.

    Calls a tool from ctx.tools by name.

    Attributes:
        tool: Tool name (e.g., "workspace.read_file")
        args: Static arguments (can contain {{var}} templates)
    """

    type: Literal["tool"] = "tool"
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute tool call."""
        # Get tool handler
        handler = ctx.tools.get(self.tool)
        if not handler:
            raise RuntimeError(f"Tool not found: {self.tool}")

        # Build arguments: merge static args with dynamic inputs
        call_args: dict[str, Any] = {}

        for key, value in self.args.items():
            if isinstance(value, str) and "{{" in value:
                # Template substitution
                call_args[key] = self._format_template(value, inputs)
            else:
                call_args[key] = value

        # Also pass through any inputs not in static args
        for key, value in inputs.items():
            if key not in call_args:
                call_args[key] = value

        # Execute
        result = await handler(call_args, ctx)

        return {"output": result}


class CodeNode(NodeBase):
    """Code execution node.

    Executes Python code in a Docker sandbox via the tool boundary (`code.execute`).

    Security: By default, code runs in an isolated Docker container with:
    - No network access (--network=none)
    - Read-only root filesystem
    - Dropped capabilities (--cap-drop=ALL)
    - Memory and CPU limits
    - No access to host filesystem (except temp workdir)

    Attributes:
        code: Python code to execute. Can use {{var}} templates.
        language: Currently only "python" supported.
        profile: Sandbox profile name for pre-configured environments.
            Profiles are allowlisted by ops via env vars:
            ALBUS_CODE_SANDBOX_DOCKER_IMAGE_<PROFILE>
            Built-in profiles (when configured):
            - "datascience": pandas, numpy, scipy, scikit-learn
            - "viz": matplotlib, seaborn, plotly
            - "web": requests, beautifulsoup4, httpx
        allow_site_packages: Enable access to installed packages.
            Only effective if the Docker image has them pre-installed.
        timeout_ms: Execution timeout in milliseconds (default: 10000, max: 60000)
        memory_mb: Memory limit in MB (default: 256, max: 1024)

    Example with data science profile:
        CodeNode(
            code='''
import pandas as pd
import numpy as np

def main(input):
    df = pd.DataFrame(input["data"])
    return {
        "mean": df["value"].mean(),
        "std": df["value"].std(),
        "count": len(df)
    }
''',
            profile="datascience",
            allow_site_packages=True,
            timeout_ms=30000,
            memory_mb=512,
        )

    Example with visualization:
        CodeNode(
            code='''
import matplotlib.pyplot as plt
import io
import base64

def main(input):
    plt.figure(figsize=(10, 6))
    plt.plot(input["x"], input["y"])
    plt.title(input.get("title", "Chart"))
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return {"image_base64": base64.b64encode(buf.read()).decode()}
''',
            profile="viz",
            allow_site_packages=True,
        )
    """

    type: Literal["code"] = "code"
    code: str
    language: Literal["python"] = "python"

    # Sandbox configuration
    profile: str | None = None  # Sandbox profile (e.g., "datascience", "viz")
    allow_site_packages: bool = False
    timeout_ms: int = 10_000
    memory_mb: int = 256

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Execute code in Docker sandbox."""
        code_runner = ctx.tools.get("code.execute")
        if not code_runner:
            raise RuntimeError("code.execute tool not available")

        # Format code template if needed
        formatted_code = (
            self._format_template(self.code, inputs) if "{{" in self.code else self.code
        )

        # Build execution request
        request: dict[str, Any] = {
            "code": formatted_code,
            "language": self.language,
            "inputs": inputs,
            "allow_site_packages": self.allow_site_packages,
            "timeout_ms": self.timeout_ms,
            "memory_mb": self.memory_mb,
        }

        # Add profile if specified
        if self.profile:
            request["profile"] = self.profile

        result = await code_runner(request, ctx)

        return {
            "output": result.get("output") or result.get("result"),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "error": result.get("error"),
            "ok": result.get("ok", False),
            "duration_ms": result.get("duration_ms", 0),
            "sandbox": result.get("sandbox", "unknown"),
        }


class CodeGeneratorNode(NodeBase):
    """LLM-powered code generation node.

    Uses an LLM to generate code from a natural language description.
    Can be chained with CodeNode for generate-then-execute patterns.

    Attributes:
        description: What the code should do (supports {{var}} templates)
        language: Target language (python, javascript, etc.)
        model: LLM model to use for generation
    """

    type: Literal["code_generator"] = "code_generator"
    description: str
    language: str = "python"
    model: str = "auto"  # "auto" routes to code-specialized model
    temperature: float = 0.2  # Low for code accuracy
    include_tests: bool = False
    include_docstring: bool = True

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Generate code using LLM."""
        llm_generate = ctx.tools.get("llm.generate")
        if not llm_generate:
            raise RuntimeError("llm.generate tool not available")

        # Format description with inputs
        formatted_desc = self._format_template(self.description, inputs)
        # Allow language to be dynamic (e.g. language="{{language}}").
        formatted_lang = self._format_template(self.language, inputs)

        # Build generation prompt
        system = f"""You are a code generator. Generate clean, correct {formatted_lang} code.

Rules:
- Output ONLY the code, no explanations
- Include type hints (for Python)
- Handle edge cases
- Keep it simple and readable
{"- Include docstrings" if self.include_docstring else ""}
{"- Include unit tests" if self.include_tests else ""}"""

        prompt = f"""Generate {formatted_lang} code for:

{formatted_desc}

Output the code only, wrapped in ```{formatted_lang}``` fences."""

        result = await llm_generate(
            {
                "prompt": prompt,
                "system": system,
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": 2000,
            },
            ctx,
        )

        if not result.get("success"):
            return {
                "code": "",
                "language": self.language,
                "error": result.get("error"),
            }

        # Extract code from response
        content = result.get("content", "")
        code = self._extract_code(content, formatted_lang)

        return {
            "code": code,
            "language": formatted_lang,
            "description": formatted_desc,
            "model": result.get("model"),
            "tokens_used": result.get("tokens_used", 0),
        }

    def _extract_code(self, content: str, language: str) -> str:
        """Extract code from markdown code blocks."""
        import re

        # Try to find fenced code block
        pattern = rf"```{language}?\s*\n?(.*?)\n?```"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Fall back to full content (might be raw code)
        return content.strip()


class DebugNode(NodeBase):
    """LLM-powered code debugging node.

    Analyzes code errors and suggests fixes.

    Attributes:
        model: LLM model to use for debugging
    """

    type: Literal["debug"] = "debug"
    model: str = "auto"  # "auto" routes to code_repair capability
    temperature: float = 0.3
    max_iterations: int = 3

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Debug code using LLM."""
        llm_generate = ctx.tools.get("llm.generate")
        if not llm_generate:
            raise RuntimeError("llm.generate tool not available")

        code = inputs.get("code", "")
        error = inputs.get("error", "")
        traceback = inputs.get("traceback", "")
        language = inputs.get("language", "python")
        description = inputs.get("description", "")

        if not code:
            return {"fixed_code": "", "error": "No code provided to debug"}

        if not error and not traceback:
            return {
                "fixed_code": code,
                "analysis": "No error provided, returning original code",
                "changes": [],
            }

        system = f"""You are a code debugger. Analyze errors and fix code.

Rules:
- Explain the bug briefly
- Provide the fixed code
- List specific changes made
- Keep fixes minimal and targeted"""

        # Build prompt parts
        purpose_str = f"Purpose: {description}" if description else ""
        traceback_str = f"Traceback:\n{traceback}" if traceback else ""

        prompt = f"""Debug this {language} code:

```{language}
{code}
```

{purpose_str}

Error:
{error}

{traceback_str}

Provide:
1. Brief analysis of the bug
2. Fixed code in ```{language}``` block
3. List of changes made"""

        result = await llm_generate(
            {
                "prompt": prompt,
                "system": system,
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": 2500,
            },
            ctx,
        )

        if not result.get("success"):
            return {
                "fixed_code": code,
                "error": result.get("error"),
                "analysis": "Failed to analyze",
            }

        content = result.get("content", "")

        # Extract fixed code
        import re

        pattern = rf"```{language}?\s*\n?(.*?)\n?```"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        fixed_code = match.group(1).strip() if match else code

        return {
            "fixed_code": fixed_code,
            "original_code": code,
            "analysis": content,
            "model": result.get("model"),
            "tokens_used": result.get("tokens_used", 0),
        }


class TransformNode(NodeBase):
    """Data transformation node.

    Transforms input data using an expression.

    Attributes:
        expr: Expression to evaluate (supports simple paths and basic ops)
    """

    type: Literal["transform"] = "transform"
    expr: str

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Transform data."""
        from pathway_engine.domain.expressions import safe_eval

        result = safe_eval(self.expr, inputs)
        return {"output": result}


# =============================================================================
# CONTROL FLOW NODES
# =============================================================================


class RouterNode(NodeBase):
    """Conditional routing node.

    Evaluates a condition and outputs which route to take.
    The VM uses this to skip nodes not on the selected route.

    Attributes:
        condition: Expression to evaluate (supports {{var}} templates or dict syntax)
        routes: Mapping of condition values to node IDs
        default: Default node ID if no route matches

    Examples:
        # Template syntax (interpolated first, then result is evaluated)
        RouterNode(condition="{{intent.mode}}", routes={"builder": "...", "thinker": "..."})

        # Dict indexing syntax (evaluated directly)
        RouterNode(condition='intent["mode"]', routes={"builder": "...", "thinker": "..."})
    """

    type: Literal["router"] = "router"
    condition: str
    routes: dict[str, str]  # value -> node_id
    default: str | None = None

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Evaluate condition and select route."""
        from pathway_engine.domain.expressions import safe_eval

        # Support both {{var}} templates and direct expressions
        condition = self.condition
        if "{{" in condition:
            # Interpolate templates first, then evaluate the result
            interpolated = self._format_template(condition, inputs)
            # The interpolated value might be "True", "false", "builder", etc.
            # Try to evaluate it, or use it directly as a string
            try:
                value = safe_eval(interpolated, {})
            except Exception:
                value = interpolated
        else:
            # Direct expression (dict indexing syntax)
            value = safe_eval(condition, inputs)

        str_value = str(value).lower() if isinstance(value, bool) else str(value)

        selected = self.routes.get(str_value, self.default)

        return {
            "selected_route": selected,
            "condition_value": value,
            "routes_available": list(self.routes.keys()),
        }


class GateNode(NodeBase):
    """Binary gate node (if/else).

    Simpler than RouterNode - just true/false branching.

    Attributes:
        condition: Expression that evaluates to truthy/falsy (supports {{var}} templates)
        true_path: Node ID to execute if true
        false_path: Node ID to execute if false

    Examples:
        # Template syntax
        GateNode(condition="{{intent.needs_tools}}", true_path="builder", false_path="thinker")

        # Dict indexing syntax
        GateNode(condition='intent["needs_tools"]', true_path="builder", false_path="thinker")
    """

    type: Literal["gate"] = "gate"
    condition: str
    true_path: str
    false_path: str

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Evaluate gate condition."""
        from pathway_engine.domain.expressions import safe_eval

        # Support both {{var}} templates and direct expressions
        condition = self.condition
        if "{{" in condition:
            # Interpolate templates first
            interpolated = self._format_template(condition, inputs)
            # Handle common truthy/falsy string values
            lowered = interpolated.strip().lower()
            if lowered in ("true", "yes", "1"):
                value = True
            elif lowered in ("false", "no", "0", "", "none", "null"):
                value = False
            else:
                # Try to evaluate as Python literal
                try:
                    value = safe_eval(interpolated, {})
                except Exception:
                    # Non-empty string is truthy
                    value = bool(interpolated.strip())
        else:
            # Direct expression (dict indexing syntax)
            value = safe_eval(condition, inputs)

        is_true = bool(value)

        return {
            "selected_route": self.true_path if is_true else self.false_path,
            "condition_value": is_true,
        }


# =============================================================================
# MEMORY NODES
# =============================================================================


class MemoryReadNode(NodeBase):
    """Read from memory store.

    Attributes:
        key: Specific key to read (optional)
        query: Semantic search query (optional)
        namespace: Memory namespace
        limit: Max results for search
    """

    type: Literal["memory_read"] = "memory_read"
    key: str | None = None
    query: str | None = None
    namespace: str = "default"
    limit: int = 5

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Read from memory."""
        if self.query:
            # Semantic search
            formatted_query = self._format_template(self.query, inputs)
            search_tool = ctx.tools.get("memory.search")
            if search_tool:
                result = await search_tool(
                    {
                        "query": formatted_query,
                        "namespace": self.namespace,
                        "limit": self.limit,
                    },
                    ctx,
                )
                return {"results": result.get("results", []), "query": formatted_query}

        if self.key:
            # Direct key lookup
            formatted_key = self._format_template(self.key, inputs)
            get_tool = ctx.tools.get("memory.get")
            if get_tool:
                result = await get_tool(
                    {
                        "key": formatted_key,
                        "namespace": self.namespace,
                    },
                    ctx,
                )
                return {"value": result.get("value"), "key": formatted_key}

        return {"results": [], "error": "No key or query specified"}


class MemoryWriteNode(NodeBase):
    """Write to memory store.

    Attributes:
        key: Key to write to
        value_expr: Expression to extract value from inputs
        namespace: Memory namespace
    """

    type: Literal["memory_write"] = "memory_write"
    key: str
    value_expr: str = "{{input}}"
    namespace: str = "default"

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Write to memory."""
        formatted_key = self._format_template(self.key, inputs)
        value = (
            self._resolve_path(inputs, self.value_expr.strip("{}"))
            if "{{" in self.value_expr
            else self.value_expr
        )

        write_tool = ctx.tools.get("memory.set")
        if write_tool:
            await write_tool(
                {
                    "key": formatted_key,
                    "value": value,
                    "namespace": self.namespace,
                },
                ctx,
            )

        return {"key": formatted_key, "written": True}


# =============================================================================
# TYPE UNION (for discriminated union parsing)
# =============================================================================

from typing import Annotated, Union

Node = Annotated[
    Union[
        LLMNode,
        ToolNode,
        CodeNode,
        TransformNode,
        RouterNode,
        GateNode,
        MemoryReadNode,
        MemoryWriteNode,
    ],
    Field(discriminator="type"),
]


__all__ = [
    # Base
    "NodeBase",
    # Compute
    "LLMNode",
    "ToolNode",
    "CodeNode",
    "TransformNode",
    # Control
    "RouterNode",
    "GateNode",
    # Memory
    "MemoryReadNode",
    "MemoryWriteNode",
    # Union type
    "Node",
]
