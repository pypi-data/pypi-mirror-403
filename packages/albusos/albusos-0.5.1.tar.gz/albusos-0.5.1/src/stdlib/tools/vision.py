"""Vision Tools - Image analysis and reasoning capabilities.

These are callable capabilities for pathways to understand and reason about images.
Uses the pathway_engine infrastructure for vision processing.

Tools receive dependencies via ToolContext - no globals, no service locators.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


# Vision-capable models by capability
VISION_MODELS = {
    "general": ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-2.0-flash-exp"],
    "fast": ["gpt-4o-mini", "gemini-1.5-flash"],
    "ocr": ["gpt-4o", "claude-3-5-sonnet-20241022"],
    "diagram": ["claude-3-5-sonnet-20241022", "gpt-4o"],
    "reasoning": ["claude-3-5-sonnet-20241022", "gpt-4o"],
}


def _select_model(capability: str, preference: str | None = None) -> str:
    """Select the best vision model for a capability."""
    if preference and preference in [
        m for models in VISION_MODELS.values() for m in models
    ]:
        return preference
    models = VISION_MODELS.get(capability, VISION_MODELS["general"])
    return models[0]


def _detect_mime_type(image_base64: str) -> str:
    """Detect MIME type from base64 prefix."""
    if image_base64.startswith("/9j/"):
        return "image/jpeg"
    elif image_base64.startswith("iVBORw"):
        return "image/png"
    elif image_base64.startswith("R0lGOD"):
        return "image/gif"
    return "image/png"


@register_tool("vision.analyze_smart")
async def analyze_smart(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Analyze an image using intelligent routing and multiple models.

    This is the PRIMARY vision tool. It:
    1. Classifies the image type (diagram, screenshot, photo, etc.)
    2. Routes to specialized analysis based on type
    3. Uses multiple models for reliability
    4. Returns structured, actionable results

    Inputs:
        image_base64: Base64-encoded image data
        image_url: URL to image (alternative to base64)
        hint: Optional hint about image type (diagram, screenshot, whiteboard, etc.)
        question: Specific question about the image
        use_pathway: Whether to use full pathway-based analysis (default: True)

    Returns:
        image_type: Detected image type
        analysis: Structured analysis results
        can_convert_to_pathway: Whether this could become a pathway
        success: Whether analysis succeeded
    """
    image_base64 = inputs.get("image_base64")
    image_url = inputs.get("image_url")
    hint = inputs.get("hint")
    question = inputs.get("question")
    use_pathway = inputs.get("use_pathway", True)

    if not image_base64 and not image_url:
        return {"success": False, "error": "image_base64 or image_url is required"}

    if not context.pathway_executor:
        return {"success": False, "error": "pathway executor not available"}

    # URL without base64 falls back to simple analysis
    if image_url and not image_base64:
        return await analyze_image(inputs, context)

    # NOTE: stdlib must not depend on `albus`. Advanced multi-step vision
    # routing can be implemented later within stdlib itself. For now, this tool
    # always falls back to simple single-model analysis.
    if use_pathway:
        logger.debug(
            "vision.analyze_smart: pathway routing not configured in stdlib; using simple mode"
        )

    return await analyze_image(inputs, context)


@register_tool("vision.analyze")
async def analyze_image(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Analyze an image and describe its contents.

    This is a SIMPLE single-model analysis. For intelligent routing,
    use vision.analyze_smart instead.

    Inputs:
        image_base64: Base64-encoded image data
        image_url: URL to image (alternative to base64)
        prompt: Question or instruction about the image (default: "Describe this image")
        model: Vision model to use (default: auto-selected based on task)
        detail: Image detail level ("auto", "low", "high")

    Returns:
        description: Text description of the image
        model: Which model was used
        success: Whether analysis succeeded
    """
    image_base64 = inputs.get("image_base64")
    image_url = inputs.get("image_url")
    prompt = str(inputs.get("prompt", "Describe this image in detail.")).strip()
    model = inputs.get("model") or _select_model("general")
    detail = inputs.get("detail", "auto")

    if not image_base64 and not image_url:
        return {"success": False, "error": "image_base64 or image_url is required"}

    # Get tool_registry for LLM calls
    from pathway_engine.application.ports.tool_registry import ToolRegistryPort

    tool_registry: ToolRegistryPort | None = (
        context.extras.get("tool_registry") if context.extras else None
    )
    if tool_registry is None and context.pathway_executor:
        tool_registry = getattr(context.pathway_executor, "tool_registry", None)

    if tool_registry is None:
        return {"success": False, "error": "tool_registry not available"}

    try:
        # Build attachments list for vision
        attachments = []
        if image_base64:
            mime_type = _detect_mime_type(image_base64)
            attachments.append(
                {
                    "type": "image",
                    "mime_type": mime_type,
                    "data_base64": image_base64,
                    "detail": detail,
                }
            )
        elif image_url:
            attachments.append(
                {
                    "type": "image_url",
                    "url": image_url,
                    "detail": detail,
                }
            )

        tool_inputs = {
            "prompt": prompt,
            "model": model,
            "temperature": 0.3,
            "max_tokens": 1500,
            "attachments": attachments,
        }

        result = await tool_registry.invoke(
            "llm.generate", tool_inputs, context=context
        )

        if not result.get("success", True):
            raise RuntimeError(f"LLM tool failed: {result.get('error')}")

        return {
            "success": True,
            "description": result.get("content", ""),
            "model": result.get("model", model),
            "tokens_used": result.get("tokens_used", 0),
        }
    except Exception as e:
        logger.warning("Image analysis failed: %s", e)
        return {"success": False, "error": str(e)}


@register_tool("vision.extract_workflow")
async def extract_workflow_from_sketch(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Analyze a workflow sketch/diagram and extract a structured pathway.

    This is the "sketch-to-pathway" capability - take a hand-drawn or digital
    diagram of a workflow and convert it into a pathway specification.

    Uses Claude by default (best at diagram reasoning), falls back to GPT-4o.

    Inputs:
        image_base64: Base64-encoded image of the workflow sketch
        image_url: URL to image (alternative)
        context: Additional context about what the workflow should do
        model: Vision model to use (default: claude-3-5-sonnet for diagrams)
        use_pathway: Use pathway-based multi-step analysis (default: True)

    Returns:
        pathway_spec: Proposed pathway structure with nodes and connections
        reasoning: Explanation of the interpreted workflow
    """
    image_base64 = inputs.get("image_base64")
    image_url = inputs.get("image_url")
    additional_context = str(inputs.get("context", "")).strip()
    model = inputs.get("model") or _select_model("diagram")
    use_pathway = inputs.get("use_pathway", True)

    if not image_base64 and not image_url:
        return {"success": False, "error": "image_base64 or image_url is required"}

    if not context.pathway_executor:
        return {"success": False, "error": "pathway executor not available"}

    # Try pathway-based analysis first
    # NOTE: stdlib must not depend on `albus`. Pathway-based diagram extraction
    # can be implemented later inside stdlib. For now, we use the single-model fallback.

    # Fallback to single-model analysis via tool_registry
    from pathway_engine.application.ports.tool_registry import ToolRegistryPort

    tool_registry: ToolRegistryPort | None = (
        context.extras.get("tool_registry") if context.extras else None
    )
    if tool_registry is None and context.pathway_executor:
        tool_registry = getattr(context.pathway_executor, "tool_registry", None)

    if tool_registry is None:
        return {"success": False, "error": "tool_registry not available"}

    try:
        prompt = f"""Analyze this workflow diagram/sketch and extract a structured automation pathway.

{f"Additional context: {additional_context}" if additional_context else ""}

Identify:
1. Each step/node in the workflow (boxes, circles, or labeled elements)
2. The connections/edges between them (arrows, lines)
3. The type of each node (LLM call, data transformation, decision point, etc.)
4. Any conditions or branching logic

Return a JSON object with this structure:
{{
    "interpretation": "Brief description of what this workflow does",
    "nodes": [
        {{"id": "node_1", "type": "llm|tool|transform|router|input|output", "name": "Node Name", "description": "What this node does", "config": {{}}}}
    ],
    "connections": [
        {{"from": "node_1", "to": "node_2", "label": "optional edge label"}}
    ],
    "entry_point": "node_id of the first node",
    "reasoning": "Explanation of how you interpreted the diagram"
}}

Node types:
- input: Entry point / user input
- output: Final result / exit
- llm: AI/LLM processing step
- tool: External action (API call, file operation)
- transform: Data manipulation
- router: Decision/branching point
- parallel: Multiple paths executing simultaneously

Be specific about what each node should do based on any labels or context in the diagram."""

        attachments = []
        if image_base64:
            mime_type = _detect_mime_type(image_base64)
            attachments.append(
                {
                    "type": "image",
                    "mime_type": mime_type,
                    "data_base64": image_base64,
                }
            )
        elif image_url:
            attachments.append(
                {
                    "type": "image_url",
                    "url": image_url,
                }
            )

        tool_inputs = {
            "prompt": prompt,
            "model": model,
            "temperature": 0.2,
            "max_tokens": 2000,
            "response_format": "json",
            "attachments": attachments,
        }

        result = await tool_registry.invoke(
            "llm.generate", tool_inputs, context=context
        )

        if not result.get("success", True):
            raise RuntimeError(f"LLM tool failed: {result.get('error')}")

        response_content = result.get("content", "")
        try:
            parsed = json.loads(response_content) if response_content else {}
        except json.JSONDecodeError:
            parsed = {}

        if isinstance(parsed, dict) and parsed.get("nodes"):
            return {
                "success": True,
                "interpretation": parsed.get("interpretation", ""),
                "pathway_spec": {
                    "name": "Extracted Workflow",
                    "description": parsed.get("interpretation", ""),
                    "nodes": parsed.get("nodes", []),
                    "connections": parsed.get("connections", []),
                },
                "entry_point": parsed.get("entry_point"),
                "reasoning": parsed.get("reasoning", ""),
                "model": result.get("model", model),
                "method": "single_model",
            }
        else:
            return {
                "success": False,
                "error": "Could not extract structured workflow",
                "raw_response": response_content,
            }
    except Exception as e:
        logger.warning("Workflow extraction failed: %s", e)
        return {"success": False, "error": str(e)}


@register_tool("vision.extract_epistemology")
async def extract_epistemology_graph(
    inputs: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    """Analyze a diagram of reasoning/epistemology and extract an LLM chain structure.

    This interprets conceptual diagrams showing how knowledge flows, how reasoning
    should proceed, or how different perspectives relate - and converts them into
    executable LLM node chains.

    Uses Claude for best reasoning about abstract diagrams.

    Inputs:
        image_base64: Base64-encoded image
        image_url: URL to image
        domain: The knowledge domain (e.g., "philosophy", "science", "business")
        model: Vision model (default: claude for reasoning diagrams)

    Returns:
        llm_chain: Proposed chain of LLM nodes with prompts
        reasoning: How the diagram was interpreted
    """
    image_base64 = inputs.get("image_base64")
    image_url = inputs.get("image_url")
    domain = str(inputs.get("domain", "general")).strip()
    model = inputs.get("model") or _select_model("reasoning")

    if not image_base64 and not image_url:
        return {"success": False, "error": "image_base64 or image_url is required"}

    # Get tool_registry for LLM calls
    from pathway_engine.application.ports.tool_registry import ToolRegistryPort

    tool_registry: ToolRegistryPort | None = (
        context.extras.get("tool_registry") if context.extras else None
    )
    if tool_registry is None and context.pathway_executor:
        tool_registry = getattr(context.pathway_executor, "tool_registry", None)

    if tool_registry is None:
        return {"success": False, "error": "tool_registry not available"}

    try:
        prompt = f"""Analyze this epistemology/reasoning diagram and design an LLM chain that implements it.

Domain: {domain}

This diagram represents how knowledge, reasoning, or different perspectives should flow.
Convert it into a concrete chain of LLM nodes where each node:
- Has a specific reasoning role (e.g., "Devil's Advocate", "Synthesizer", "Fact Checker")
- Has a prompt that captures its perspective/function
- Connects to other nodes in the reasoning flow

Return JSON:
{{
    "interpretation": "What reasoning pattern this diagram represents",
    "llm_chain": [
        {{
            "id": "node_id",
            "role": "The reasoning role (e.g., 'Analyst', 'Critic', 'Synthesizer')",
            "prompt_template": "The system prompt for this node's perspective",
            "input_from": ["list of node IDs this receives input from"],
            "output_to": ["list of node IDs this sends output to"],
            "temperature": 0.7
        }}
    ],
    "entry_point": "First node ID",
    "final_output": "Node ID that produces final result",
    "reasoning_pattern": "Name for this pattern (e.g., 'Dialectic', 'Parallel Analysis', 'Chain of Thought')",
    "explanation": "How this chain implements the reasoning in the diagram"
}}

Consider patterns like:
- Sequential reasoning (A → B → C)
- Parallel perspectives (A₁, A₂, A₃ → Synthesis)
- Dialectic (Thesis → Antithesis → Synthesis)
- Iterative refinement (Draft → Critique → Revise → ...)
- Multi-agent debate"""

        attachments = []
        if image_base64:
            mime_type = _detect_mime_type(image_base64)
            attachments.append(
                {
                    "type": "image",
                    "mime_type": mime_type,
                    "data_base64": image_base64,
                }
            )
        elif image_url:
            attachments.append(
                {
                    "type": "image_url",
                    "url": image_url,
                }
            )

        tool_inputs = {
            "prompt": prompt,
            "model": model,
            "temperature": 0.3,
            "max_tokens": 2500,
            "response_format": "json",
            "attachments": attachments,
        }

        result = await tool_registry.invoke(
            "llm.generate", tool_inputs, context=context
        )

        if not result.get("success", True):
            raise RuntimeError(f"LLM tool failed: {result.get('error')}")

        response_content = result.get("content", "")
        try:
            parsed = json.loads(response_content) if response_content else {}
        except json.JSONDecodeError:
            parsed = {}

        if isinstance(parsed, dict) and parsed.get("llm_chain"):
            llm_chain = parsed.get("llm_chain", [])
            nodes = []
            connections = []

            for node in llm_chain:
                nodes.append(
                    {
                        "id": node.get("id"),
                        "type": "llm",
                        "name": node.get("role", node.get("id")),
                        "description": f"LLM node: {node.get('role', '')}",
                        "config": {
                            "prompt": node.get("prompt_template", ""),
                            "temperature": node.get("temperature", 0.7),
                            "max_output_tokens": 1000,
                        },
                    }
                )

                for target in node.get("output_to", []):
                    connections.append(f"{node.get('id')} → {target}")

            return {
                "success": True,
                "interpretation": parsed.get("interpretation", ""),
                "reasoning_pattern": parsed.get("reasoning_pattern", ""),
                "pathway_spec": {
                    "name": f"{parsed.get('reasoning_pattern', 'Reasoning')} Chain",
                    "description": parsed.get("interpretation", ""),
                    "nodes": nodes,
                    "connections": connections,
                },
                "entry_point": parsed.get("entry_point"),
                "final_output": parsed.get("final_output"),
                "explanation": parsed.get("explanation", ""),
            }
        else:
            return {
                "success": False,
                "error": "Could not extract LLM chain structure",
                "raw_response": response.content,
            }
    except Exception as e:
        logger.warning("Epistemology extraction failed: %s", e)
        return {"success": False, "error": str(e)}


@register_tool("vision.ocr")
async def extract_text(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Extract text from an image (OCR).

    Uses models optimized for text extraction.

    Inputs:
        image_base64: Base64-encoded image
        image_url: URL to image
        language: Expected language (default: auto-detect)
        model: Vision model (default: best OCR model)
        detail: Image detail level ("high" recommended for OCR)

    Returns:
        text: Extracted text content
        model: Model used
        success: Whether extraction succeeded
    """
    image_base64 = inputs.get("image_base64")
    image_url = inputs.get("image_url")
    model = inputs.get("model") or _select_model("ocr")
    detail = inputs.get("detail", "high")

    if not image_base64 and not image_url:
        return {"success": False, "error": "image_base64 or image_url is required"}

    # Get tool_registry for LLM calls
    from pathway_engine.application.ports.tool_registry import ToolRegistryPort

    tool_registry: ToolRegistryPort | None = (
        context.extras.get("tool_registry") if context.extras else None
    )
    if tool_registry is None and context.pathway_executor:
        tool_registry = getattr(context.pathway_executor, "tool_registry", None)

    if tool_registry is None:
        return {"success": False, "error": "tool_registry not available"}

    try:
        prompt = """Extract ALL text visible in this image.
Maintain the structure and layout as much as possible.
Include any labels, captions, handwritten text, or typed text.
Return the text exactly as it appears, preserving line breaks where logical."""

        attachments = []
        if image_base64:
            mime_type = _detect_mime_type(image_base64)
            attachments.append(
                {
                    "type": "image",
                    "mime_type": mime_type,
                    "data_base64": image_base64,
                    "detail": detail,
                }
            )
        elif image_url:
            attachments.append(
                {
                    "type": "image_url",
                    "url": image_url,
                    "detail": detail,
                }
            )

        tool_inputs = {
            "prompt": prompt,
            "model": model,
            "temperature": 0.1,
            "max_tokens": 2000,
            "attachments": attachments,
        }

        result = await tool_registry.invoke(
            "llm.generate", tool_inputs, context=context
        )

        if not result.get("success", True):
            raise RuntimeError(f"LLM tool failed: {result.get('error')}")

        return {
            "success": True,
            "text": result.get("content", ""),
            "model": result.get("model", model),
        }
    except Exception as e:
        logger.warning("OCR failed: %s", e)
        return {"success": False, "error": str(e)}
