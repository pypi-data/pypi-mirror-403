from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from pathway_engine.application.kernel import PathwayVM
from pathway_engine.domain.context import Context
from pathway_engine.domain.pathway import Pathway


def _load_dotenv() -> None:
    """Auto-load .env file if present (so users don't need export $(grep...))."""
    try:
        from dotenv import load_dotenv

        # Search current dir and up to 3 parents for .env
        for p in [Path.cwd()] + list(Path.cwd().parents)[:3]:
            env_file = p / ".env"
            if env_file.is_file():
                load_dotenv(env_file, override=False)
                break
    except ImportError:
        pass  # python-dotenv not installed; skip


def _load_target(spec: str) -> Any:
    """Load a python target of the form module:attr (attr can be nested via dots)."""
    if ":" not in spec:
        raise ValueError("Target must be in the form module:attr")
    mod_name, attr_path = spec.split(":", 1)
    mod = importlib.import_module(mod_name)
    obj: Any = mod
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def _coerce_pathway(obj: Any) -> Pathway:
    """Coerce target to Pathway.

    Accepts:
    - Pathway objects directly
    - Functions that return Pathway objects
    """
    if callable(obj):
        obj = obj()
    if isinstance(obj, Pathway):
        return obj
    raise TypeError(f"Target did not resolve to a Pathway: {type(obj).__name__}")


def _parse_inputs(inputs_arg: str | None) -> dict[str, Any]:
    if not inputs_arg:
        return {}
    s = inputs_arg.strip()
    # @file.json
    if s.startswith("@"):
        path = Path(s[1:])
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(s)


def _coerce_tools(obj: Any) -> dict[str, Any]:
    """Coerce a tool registry object into {name -> handler}.

    Accepted forms:
    - dict[str, Any]
    - module/object with TOOL_HANDLERS attribute
    - callable returning either of the above
    """
    if callable(obj):
        obj = obj()
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "TOOL_HANDLERS"):
        handlers = getattr(obj, "TOOL_HANDLERS")
        if isinstance(handlers, dict):
            return handlers
    raise TypeError("Tools target must be dict[str, handler] or expose TOOL_HANDLERS")


def _coerce_tool_definitions(obj: Any) -> Any:
    """Coerce tool definitions payload (optional, for UX/introspection)."""
    if callable(obj):
        obj = obj()
    if hasattr(obj, "TOOL_DEFINITIONS"):
        return getattr(obj, "TOOL_DEFINITIONS")
    return obj


def _build_vm(
    *, tools_target: str | None, tool_definitions_target: str | None
) -> PathwayVM:
    tools: dict[str, Any] = {}
    tool_definitions: Any | None = None

    if tools_target:
        tools_obj = _load_target(tools_target)
        tools = _coerce_tools(tools_obj)

    if tool_definitions_target:
        defs_obj = _load_target(tool_definitions_target)
        tool_definitions = _coerce_tool_definitions(defs_obj)

    ctx = Context(tools=tools)
    if tool_definitions is not None:
        ctx.extras["tool_definitions"] = tool_definitions

    vm = PathwayVM(ctx)
    # Tools often expect this for subpathway execution or utility.
    vm.ctx.extras["pathway_executor"] = vm
    return vm


async def _run_once(args: argparse.Namespace) -> int:
    target_obj = _load_target(args.target)
    if callable(target_obj):
        target_obj = target_obj()
    pathway = _coerce_pathway(target_obj)

    vm = _build_vm(
        tools_target=args.tools, tool_definitions_target=args.tool_definitions
    )
    inputs = _parse_inputs(args.inputs)
    if args.stop_on_error:
        inputs["_stop_on_error"] = True

    record = await vm.execute(pathway, inputs)
    ok = bool(
        record.status.value == "completed"
        and not record.error
        and record.metrics.nodes_failed == 0
    )
    out = {
        "success": ok,
        "pathway_id": record.pathway_id,
        "execution_id": record.id,
        "status": record.status.value,
        "error": record.error,
        "metrics": record.metrics.model_dump(),
        "outputs": record.outputs,
    }
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0 if ok else 2


async def _run_stream(args: argparse.Namespace) -> int:
    target_obj = _load_target(args.target)
    if callable(target_obj):
        target_obj = target_obj()
    pathway = _coerce_pathway(target_obj)

    vm = _build_vm(
        tools_target=args.tools, tool_definitions_target=args.tool_definitions
    )
    inputs = _parse_inputs(args.inputs)

    produced = 0
    async for item in vm.stream_execute(
        pathway, inputs=inputs, max_events=args.max_events
    ):
        print(json.dumps(item, sort_keys=True, default=str))
        produced += 1
        if args.max_events is not None and produced >= args.max_events:
            break
    return 0


def main() -> int:
    _load_dotenv()  # Auto-load .env for API keys etc.
    p = argparse.ArgumentParser(
        prog="pathway", description="Pathway runtime CLI (run Pathways)"
    )
    sp = p.add_subparsers(dest="cmd", required=True)

    p_run = sp.add_parser("run", help="Run a Pathway once")
    p_run.add_argument(
        "--target",
        required=True,
        help="Target (module:attr) yielding a Pathway or compilable program",
    )
    p_run.add_argument("--inputs", default="", help="JSON inputs or @file.json")
    p_run.add_argument(
        "--tools",
        default="stdlib.tools_export:TOOL_HANDLERS",
        help="Tools target (default: stdlib.tools_export:TOOL_HANDLERS)",
    )
    p_run.add_argument(
        "--tool-definitions",
        default="",
        help="Optional python target module:attr yielding tool definitions payload (or exposing TOOL_DEFINITIONS)",
    )
    p_run.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop execution at first node failure",
    )
    p_run.set_defaults(func=lambda a: int(asyncio.run(_run_once(a))))

    p_stream = sp.add_parser("stream", help="Stream-execute a Pathway with live events")
    p_stream.add_argument(
        "--target",
        required=True,
        help="Target (module:attr) yielding a Pathway or compilable program",
    )
    p_stream.add_argument("--inputs", default="", help="JSON inputs or @file.json")
    p_stream.add_argument(
        "--max-events", type=int, default=None, help="Stop after N events"
    )
    p_stream.add_argument(
        "--tools",
        default="stdlib.tools_export:TOOL_HANDLERS",
        help="Tools target (default: stdlib.tools_export:TOOL_HANDLERS)",
    )
    p_stream.add_argument(
        "--tool-definitions",
        default="",
        help="Optional python target module:attr yielding tool definitions payload (or exposing TOOL_DEFINITIONS)",
    )
    p_stream.set_defaults(func=lambda a: int(asyncio.run(_run_stream(a))))

    args = p.parse_args()
    # Normalize empty strings → None for optional targets
    if getattr(args, "tool_definitions", "") == "":
        args.tool_definitions = None
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
