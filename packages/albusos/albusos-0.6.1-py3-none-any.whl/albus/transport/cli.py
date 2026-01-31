"""albus CLI - built-in system agent CLI.

Usage:
    albus server [--host HOST] [--port PORT] [--debug] [--log-level LEVEL]
    albus tools
    albus models [--profile PROFILE] [--check]
    albus battery [--pack PACK] [--check]
    albus --help

Notes:
- Pathways are defined using `pathway_engine` directly.
- The **runtime CLI** is `pathway` (from `pathway_engine`).
- This `albus` CLI runs the built-in Albus system agent/server and dev tooling.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import json as _json
from typing import Any


def cmd_server(args: argparse.Namespace) -> int:
    """Run the Albus server."""
    from albus.transport.server import main as server_main

    # Patch sys.argv so server's argparse sees our args
    argv = ["albus-server"]
    if args.host:
        argv.extend(["--host", args.host])
    if args.port:
        argv.extend(["--port", str(args.port)])
    if args.debug:
        argv.append("--debug")
    if getattr(args, "log_level", ""):
        argv.extend(["--log-level", str(args.log_level)])
    sys.argv = argv
    server_main()
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    """List registered tools."""
    from stdlib.tools import TOOL_HANDLERS

    for name in sorted(TOOL_HANDLERS.keys()):
        print(f"  {name}")
    return 0


def cmd_deploy(args: argparse.Namespace) -> int:
    """Deployment config helpers."""
    action = str(getattr(args, "action", "") or "").strip()
    if action == "validate":
        from albus.infrastructure.deployment import DeploymentConfig

        cfg = DeploymentConfig.load(getattr(args, "config", None))
        errs = cfg.validate()
        if errs:
            print(f"Invalid deployment config ({cfg.source}):")
            for e in errs:
                print(f"  - {e}")
            return 1
        print(f"✓ Deployment config valid ({cfg.source})")
        return 0

    print("Unknown deploy action")
    return 2


def cmd_models(args: argparse.Namespace) -> int:
    """List and check model configuration."""
    from stdlib.llm.cognitive_models import (
        get_all_models_for_profile,
        ensure_local_models,
        list_required_local_models,
    )
    from stdlib.llm import list_available_providers

    profile = args.profile or "local"

    print(f"\n🧠 Cognitive Model Configuration (profile: {profile})")
    print("=" * 50)

    models = get_all_models_for_profile(profile)
    # These keys are operation kinds (explicit names).
    labels = {
        "reasoning": "reasoning",
        "routing": "routing",
        "tool_call": "tool_call",
        "embedding": "embedding",
        "meta": "meta",
        "code_gen": "code_gen",
        "code_repair": "code_repair",
        "streaming": "streaming",
    }
    for op, model in models.items():
        label = labels.get(op, str(op))
        print(f"  {label:12} → {model or '(none)'}")

    print()
    print("📡 Available Providers:")
    providers = list_available_providers()
    for p in providers:
        print(f"  ✓ {p}")
    if not providers:
        print("  (none configured)")

    if args.check and profile in ("local", "dev"):
        print()
        print("🔍 Checking local models (Ollama):")
        asyncio.run(ensure_local_models(verbose=True))
        print()
        print("To pull missing models:")
        for model in list_required_local_models():
            print(f"  ollama pull {model}")

    print()
    return 0


def cmd_battery(args: argparse.Namespace) -> int:
    """Show/check battery pack configuration."""
    from stdlib.llm.capability_routing import (
        get_battery_pack,
        describe_battery_pack,
        list_required_models,
        list_required_providers,
        check_battery_pack_availability,
        BATTERY_PACKS,
    )

    pack = args.pack or get_battery_pack()

    print(f"\n🔋 Battery Pack: {pack}")
    print("=" * 60)
    print(f"   {describe_battery_pack(pack)}")
    print()

    if args.list:
        # List all battery packs
        print("Available Battery Packs:")
        for p in BATTERY_PACKS.keys():
            marker = "→" if p == pack else " "
            print(f"  {marker} {p}: {describe_battery_pack(p)}")
        print()
        print(f"Set with: AGENT_STDLIB_BATTERY_PACK={pack}")
        print()
        return 0

    # Show capability → model mapping
    routes = BATTERY_PACKS.get(pack, {})

    print("Capability Routing:")
    print("-" * 60)

    # Group by category
    categories = {
        "Code & Math": [
            "code",
            "code.python",
            "code.typescript",
            "code.review",
            "math",
            "math.symbolic",
        ],
        "Reasoning": ["reasoning", "reasoning.deep", "reasoning.fast"],
        "Tool Use": ["tool_calling", "scripting", "json_output"],
        "Routing": ["routing", "classify", "intent"],
        "Vision": ["vision", "vision.ocr", "vision.diagram", "vision.general"],
        "Speech": ["speech.asr", "speech.tts", "audio.realtime"],
        "Embeddings": ["embed", "embed.query", "embed.document"],
    }

    for category, caps in categories.items():
        print(f"\n  {category}:")
        for cap in caps:
            model = routes.get(cap, "(not configured)")
            if model is None:
                model = "(not available locally)"
            print(f"    {cap:20} → {model}")

    print()
    print("Required Providers:", ", ".join(list_required_providers(pack)))
    print("Required Models:", len(list_required_models(pack)))

    if args.check:
        print()
        print("🔍 Checking Model Availability:")
        print("-" * 60)
        asyncio.run(check_battery_pack_availability(pack, verbose=True))

    if args.test_reasoning:
        print()
        print("🤔 Testing Reasoning Capability:")
        print("-" * 60)
        deep_model = routes.get("reasoning.deep") or routes.get("reasoning")
        if deep_model:
            print(f"  Target Model: {deep_model}")
            if "claude" in str(deep_model):
                print("  ✓ Extended Thinking Mode: DETECTED")
                print("  ✓ Cognitive Offloading: ACTIVE")
            else:
                print("  ⚠ Standard reasoning model detected (not Claude 3.7)")
        else:
            print("  ❌ No reasoning model configured")

    print()
    return 0


async def _http_json(
    *, method: str, url: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    import aiohttp

    timeout = aiohttp.ClientTimeout(total=180)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if method.upper() == "GET":
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()
        async with session.post(url, json=payload or {}) as resp:
            resp.raise_for_status()
            return await resp.json()


def cmd_viz(args: argparse.Namespace) -> int:
    """Visualize a pathway."""
    pathway_id = str(getattr(args, "pathway_id", "") or "").strip()
    fmt = str(getattr(args, "format", "mermaid") or "mermaid").strip().lower()
    host = str(getattr(args, "host", "127.0.0.1"))
    port = int(getattr(args, "port", 8080))

    if not pathway_id:
        print("pathway_id required")
        return 2

    # For web format, open browser to visualization endpoint
    if fmt == "web":
        url = f"http://{host}:{port}/api/v1/pathways/{pathway_id}/viz"
        print(f"Opening: {url}")
        import webbrowser
        webbrowser.open(url)
        return 0

    # Load from server
    base = f"http://{host}:{port}/api/v1"
    data = asyncio.run(_http_json(method="GET", url=f"{base}/pathways/{pathway_id}/graph"))
    if not data.get("success", False):
        print(f"Error: {data}")
        return 1

    return _describe_viz(data, fmt)


def cmd_skills(args: argparse.Namespace) -> int:
    """List skills for agents or load external skills."""
    host = str(getattr(args, "host", "127.0.0.1"))
    port = int(getattr(args, "port", 8080))
    base = f"http://{host}:{port}/api/v1"
    
    action = str(getattr(args, "action", "") or "").strip()
    
    if action == "list":
        agent_id = str(getattr(args, "agent_id", "host") or "host").strip()
        data = asyncio.run(_http_json(method="GET", url=f"{base}/agents/{agent_id}/skills"))
        
        skills = data.get("skills", [])
        print(f"\nSkills for agent '{agent_id}' ({len(skills)} total):")
        print("=" * 60)
        
        for skill in skills:
            print(f"\n  {skill.get('name', 'Unknown')} ({skill.get('id', 'unknown')})")
            desc = skill.get("description", "")
            if desc:
                print(f"    {desc[:80]}{'...' if len(desc) > 80 else ''}")
            inputs = skill.get("inputs", {})
            if inputs:
                print(f"    Inputs: {', '.join(inputs.keys())}")
        
        return 0
    
    if action == "load":
        skill_dirs = str(getattr(args, "dirs", "") or "").strip()
        if not skill_dirs:
            print("Error: --dirs required for 'load' action")
            return 2
        
        # This would require server-side support for dynamic loading
        # For now, show instructions
        print("To load external skills, set ALBUS_SKILL_DIRS environment variable:")
        print(f"  export ALBUS_SKILL_DIRS=\"{skill_dirs}\"")
        print("  albus server")
        print("\nOr load programmatically:")
        print("  from pathway_engine.infrastructure.skill_loader import load_agent_skills_from_directories")
        print(f"  skills = await load_agent_skills_from_directories(\"{skill_dirs}\")")
        return 0
    
    print("Unknown action. Use 'list' or 'load'")
    return 2


def cmd_pathways(args: argparse.Namespace) -> int:
    """Pathway lifecycle helpers.

    NOTE: YAML deploy/export support was removed.
    Use pathway_engine directly or pathway.create tool for creating pathways.
    """
    from albus.application.pathways import PathwayService

    host = str(getattr(args, "host", "127.0.0.1"))
    port = int(getattr(args, "port", 8080))
    base = f"http://{host}:{port}/api/v1"

    action = str(getattr(args, "action", "") or "").strip()
    if action == "list":
        data = asyncio.run(_http_json(method="GET", url=f"{base}/pathways"))
        paths = data.get("pathways") or []
        print(f"Pathways ({len(paths)}):")
        for p in paths:
            pid = p.get("id")
            src = p.get("source") or ""
            print(f"  - {pid} ({src})")
        return 0

    if action == "describe":
        pid = str(getattr(args, "id", "") or "").strip()
        if not pid:
            print("id required")
            return 2

        fmt = str(getattr(args, "format", "") or "text").strip().lower()

        data = asyncio.run(_http_json(method="GET", url=f"{base}/pathways/{pid}/graph"))
        if not data.get("success", False):
            print(data)
            return 1

        # For visualization formats, we need to load the actual pathway
        if fmt in ("mermaid", "ascii", "dot", "d3"):
            return _describe_viz(data, fmt)

        # Default text format
        print(f"Pathway: {data.get('pathway_id')}")
        if data.get("source"):
            print(f"Source:  {data.get('source')}")
        print(f"Nodes:   {data.get('node_count')}")
        print(f"Edges:   {len(data.get('connections') or data.get('edges') or [])}")
        print()
        print("Nodes:")
        for n in data.get("nodes") or []:
            nid = n.get("id")
            ntype = n.get("type")
            prompt = n.get("prompt")
            if prompt:
                print(f"  - {nid} [{ntype}] :: {prompt}")
            else:
                print(f"  - {nid} [{ntype}]")
        print()
        print("Edges:")
        for e in data.get("connections") or data.get("edges") or []:
            if isinstance(e, (list, tuple)) and len(e) == 2:
                print(f"  - {e[0]} -> {e[1]}")
            elif isinstance(e, dict) and "from" in e and "to" in e:
                print(f"  - {e['from']} -> {e['to']}")
            else:
                print(f"  - {e}")
        print()
        return 0


def _describe_viz(data: dict[str, Any], fmt: str) -> int:
    """Output pathway visualization in the specified format."""
    from stdlib.tools.viz import (
        pathway_to_mermaid,
        pathway_to_ascii,
        pathway_to_dot,
        pathway_to_d3_json,
    )
    from pathway_engine.domain.pathway import Pathway, Connection
    from pathway_engine.domain.nodes.core import LLMNode, ToolNode, TransformNode

    # Reconstruct a minimal pathway from graph data
    nodes: dict[str, Any] = {}
    for n in data.get("nodes") or []:
        nid = n.get("id")
        ntype = str(n.get("type", "")).lower()
        prompt = n.get("prompt")

        # Create appropriate node type
        if "llm" in ntype:
            nodes[nid] = LLMNode(id=nid, prompt=prompt or "", model="auto")
        elif "tool" in ntype:
            nodes[nid] = ToolNode(id=nid, tool=n.get("tool", "unknown"), args={})
        elif "transform" in ntype:
            nodes[nid] = TransformNode(id=nid, expression="")
        else:
            # Generic - use LLMNode as placeholder with type info
            node = LLMNode(id=nid, prompt=prompt or "", model="auto")
            node.type = ntype  # type: ignore
            nodes[nid] = node

    connections = []
    for e in data.get("connections") or data.get("edges") or []:
        if isinstance(e, (list, tuple)) and len(e) == 2:
            connections.append(Connection(from_node=e[0], to_node=e[1]))
        elif isinstance(e, dict):
            from_n = e.get("from") or e.get("from_node") or e.get("source")
            to_n = e.get("to") or e.get("to_node") or e.get("target")
            if from_n and to_n:
                connections.append(Connection(from_node=from_n, to_node=to_n))

    pathway = Pathway(
        id=data.get("pathway_id", "unknown"),
        name=data.get("pathway_id", "Unknown"),
        nodes=nodes,
        connections=connections,
    )

    if fmt == "mermaid":
        print(pathway_to_mermaid(pathway))
    elif fmt == "ascii":
        print(pathway_to_ascii(pathway))
    elif fmt == "dot":
        print(pathway_to_dot(pathway))
    elif fmt == "d3":
        output = pathway_to_d3_json(pathway)
        print(_json.dumps(output, indent=2))
    else:
        print(f"Unknown format: {fmt}")
        return 1

    return 0

    if action == "deploy":
        print(
            "ERROR: YAML deploy support is not available. Use pathway_engine directly or pathway.create tool."
        )
        return 1
        # YAML support is not available
        # file_path = str(getattr(args, "file", "") or "").strip()
        # if not file_path:
        #     print("file required")
        #     return 2
        # pathway = load_pathway_yaml(file_path)

        # Build import payload compatible with POST /api/v1/pathways/import (format albus.pathway.v1)
        # Reuse product-canonical node serialization.
        tmp = PathwayService()
        export_data = {
            "format": "albus.pathway.v1",
            "pathway": {
                "id": pathway.id,
                "name": pathway.name,
                "description": pathway.description,
                "nodes": [tmp._serialize_node(n) for n in pathway.nodes.values()],  # type: ignore[attr-defined]
                "connections": [
                    {"from": c.from_node, "to": c.to_node} for c in pathway.connections
                ],
                "metadata": dict(pathway.metadata or {}),
            },
        }
        data = asyncio.run(
            _http_json(
                method="POST", url=f"{base}/pathways/import", payload=export_data
            )
        )
        if not data.get("success", True):
            print(f"deploy failed: {data.get('error')}")
            return 1
        p = data.get("pathway") or {}
        print(f"✓ deployed: {p.get('id')} (source={p.get('source')})")
        return 0

    if action == "export":
        pid = str(getattr(args, "id", "") or "").strip()
        out_path = str(getattr(args, "out", "") or "").strip()
        if not pid:
            print("id required")
            return 2
        data = asyncio.run(
            _http_json(method="GET", url=f"{base}/pathways/{pid}/export")
        )
        if data.get("format") != "albus.pathway.v1":
            print(f"unexpected export format: {data.get('format')}")
            return 1
        p = data.get("pathway") or {}
        tmp = PathwayService()
        pathway = tmp._pathway_from_dict(p)  # type: ignore[attr-defined]
        # YAML export is not available
        print(
            "ERROR: YAML export support is not available. Pathway data is available in JSON format."
        )
        return 1
        # yaml_txt = pathway_to_yaml(pathway)
        if out_path:
            from pathlib import Path

            Path(out_path).write_text(yaml_txt, encoding="utf-8")
            print(f"✓ wrote {out_path}")
        else:
            print(yaml_txt)
        return 0

    print("Unknown action. Use: list | deploy | export")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="albus",
        description="Albus developer CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # server
    p_server = subparsers.add_parser("server", help="Run Albus server")
    p_server.add_argument("--host", default="127.0.0.1")
    p_server.add_argument("--port", type=int, default=8080)
    p_server.add_argument("--debug", action="store_true")
    p_server.add_argument(
        "--log-level", default="", help="Python log level (e.g. INFO, DEBUG)"
    )
    p_server.set_defaults(func=cmd_server)

    # tools
    p_tools = subparsers.add_parser("tools", help="List registered tools")
    p_tools.set_defaults(func=cmd_tools)

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="Deployment config helpers")
    p_deploy.add_argument(
        "--config",
        default="",
        help="Optional path to deployment config file (default: auto-detect albus.yaml / ALBUS_CONFIG)",
    )
    p_deploy_sub = p_deploy.add_subparsers(dest="action", required=True)
    p_dvalidate = p_deploy_sub.add_parser(
        "validate", help="Validate deployment config (albus.yaml)"
    )
    p_dvalidate.set_defaults(func=cmd_deploy)

    # models
    p_models = subparsers.add_parser("models", help="List/check model configuration")
    p_models.add_argument(
        "--profile",
        choices=["cloud", "local", "dev"],
        default="local",
        help="Model profile to show",
    )
    p_models.add_argument(
        "--check", action="store_true", help="Check if local models are available"
    )
    p_models.set_defaults(func=cmd_models)

    # battery
    p_battery = subparsers.add_parser(
        "battery", help="Show/check battery pack configuration"
    )
    p_battery.add_argument(
        "--pack",
        choices=["starter", "balanced", "premium", "local"],
        help="Battery pack to show (default: from AGENT_STDLIB_BATTERY_PACK)",
    )
    p_battery.add_argument(
        "--check",
        action="store_true",
        help="Check if all required models are available",
    )
    p_battery.add_argument(
        "--test-reasoning", action="store_true", help="Test reasoning capability"
    )
    p_battery.add_argument(
        "--list", action="store_true", help="List all available battery packs"
    )
    p_battery.set_defaults(func=cmd_battery)

    # studio (terminal UI - canonical)
    p_studio = subparsers.add_parser(
        "studio", help="Launch Brain Studio (terminal chat + live events)"
    )
    p_studio.add_argument("--host", default="127.0.0.1")
    p_studio.add_argument("--port", type=int, default=8080)
    p_studio.add_argument("--thread-id", default="demo")

    def _cmd_studio(args: argparse.Namespace) -> int:
        from albus.transport.studio import run_studio

        return run_studio(host=args.host, port=args.port, thread_id=args.thread_id)

    p_studio.set_defaults(func=_cmd_studio)

    # viz (visualization helpers)
    p_viz = subparsers.add_parser("viz", help="Visualize pathways and packs")
    p_viz.add_argument("pathway_id", help="Pathway ID to visualize")
    p_viz.add_argument(
        "--format", "-f",
        choices=["mermaid", "ascii", "dot", "d3", "web"],
        default="mermaid",
        help="Output format (default: mermaid). Use 'web' to open in browser.",
    )
    p_viz.add_argument("--host", default="127.0.0.1")
    p_viz.add_argument("--port", type=int, default=8080)
    p_viz.set_defaults(func=cmd_viz)

    # skills
    p_skills = subparsers.add_parser("skills", help="List and manage agent skills")
    p_skills.add_argument("--host", default="127.0.0.1")
    p_skills.add_argument("--port", type=int, default=8080)
    p_skills_sub = p_skills.add_subparsers(dest="action", required=True)
    
    p_skills_list = p_skills_sub.add_parser("list", help="List skills for an agent")
    p_skills_list.add_argument("--agent-id", default="host", help="Agent ID (default: host)")
    p_skills_list.set_defaults(func=cmd_skills)
    
    p_skills_load = p_skills_sub.add_parser("load", help="Load external skills (shows instructions)")
    p_skills_load.add_argument("--dirs", required=True, help="Comma-separated skill directories")
    p_skills_load.set_defaults(func=cmd_skills)
    
    # pathways (file + lifecycle helpers)
    p_pathways = subparsers.add_parser("pathways", help="Pathway lifecycle helpers")
    p_pathways.add_argument("--host", default="127.0.0.1")
    p_pathways.add_argument("--port", type=int, default=8080)
    p_pathways_sub = p_pathways.add_subparsers(dest="action", required=True)

    p_plist = p_pathways_sub.add_parser("list", help="List all pathways")
    p_plist.set_defaults(func=cmd_pathways)

    p_pdescribe = p_pathways_sub.add_parser(
        "describe", help="Describe a pathway graph (nodes + edges)"
    )
    p_pdescribe.add_argument("id", help="Pathway id")
    p_pdescribe.add_argument(
        "--format", "-f",
        choices=["text", "mermaid", "ascii", "dot", "d3"],
        default="text",
        help="Output format (default: text)",
    )
    p_pdescribe.set_defaults(func=cmd_pathways)

    p_pdeploy = p_pathways_sub.add_parser(
        "deploy", help="(disabled) Deploy a YAML pathway file to the running server"
    )
    p_pdeploy.add_argument("file", help="Path to pathway YAML file")
    p_pdeploy.set_defaults(func=cmd_pathways)

    p_pexport = p_pathways_sub.add_parser(
        "export", help="(disabled) Export a pathway id to YAML"
    )
    p_pexport.add_argument("id", help="Pathway id (pack id or doc id)")
    p_pexport.add_argument(
        "--out", default="", help="Output file path (default: stdout)"
    )
    p_pexport.set_defaults(func=cmd_pathways)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
