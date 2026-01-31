"""Brain Studio (Terminal) - Canonical terminal-based Studio.

This is the ONLY Studio. No web UI.

Features:
- Live event stream (/ws)
- Pathway streaming control plane (JSON-RPC)
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any
from urllib.parse import quote

import aiohttp
from aiohttp import WSMsgType


def _ws_url(host: str, port: int, thread_id: str) -> str:
    return f"ws://{host}:{port}/api/v1/ws?mode=both&thread_id={quote(thread_id)}"


async def _run_studio(*, host: str, port: int, thread_id: str) -> int:
    """Run the terminal studio."""
    ws_url = _ws_url(host, port, thread_id)
    base_url = f"http://{host}:{port}"

    print(f"\n🧙 ALBUS STUDIO (terminal)")
    print(f"   thread: {thread_id}")
    print(f"   server: {base_url}")
    print(f"   ws:     {ws_url}")
    print()
    print("Commands:")
    print("  /quit, /exit  - Exit studio")
    print("  /thread <id>  - Switch thread")
    print("  /pathways     - List pathways")
    print("  /clear        - Clear screen")
    print("  /run <id>     - Stream a pathway by id (JSON-RPC)")
    print()

    rpc_id = 0
    pending: dict[int, asyncio.Future] = {}
    current_thread = thread_id

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=None)
    ) as session:
        # Health check
        try:
            async with session.get(f"{base_url}/api/v1/health") as resp:
                if resp.status != 200:
                    print(f"❌ Server not healthy at {base_url}")
                    return 1
        except Exception as e:
            print(f"❌ Cannot reach server at {base_url}: {e}")
            print("   Start with: uv run albus server --debug")
            return 1

        print(f"✓ Connected to {base_url}")
        print()

        # Connect WebSocket
        try:
            async with session.ws_connect(ws_url, heartbeat=15.0, autoping=True) as ws:

                async def _receiver():
                    """Receive WebSocket messages."""
                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            try:
                                obj = json.loads(msg.data)
                            except Exception:
                                continue

                            # JSON-RPC response
                            if (
                                isinstance(obj, dict)
                                and obj.get("jsonrpc") == "2.0"
                                and "id" in obj
                            ):
                                rid = obj["id"]
                                if rid in pending:
                                    fut = pending.pop(rid)
                                    if "error" in obj:
                                        fut.set_exception(
                                            RuntimeError(
                                                str(
                                                    obj["error"].get(
                                                        "message", obj["error"]
                                                    )
                                                )
                                            )
                                        )
                                    else:
                                        fut.set_result(obj.get("result", {}))
                                continue

                            # Event
                            if isinstance(obj, dict):
                                et = obj.get("type") or obj.get("event_type") or ""
                                if et in ("turn_started",):
                                    print(f"  [{et}] turn={obj.get('turn_id', '')}")
                                elif et in ("turn_completed",):
                                    # Response will be shown via RPC result
                                    pass
                                elif et in ("turn_failed",):
                                    print(f"  [{et}] error={obj.get('error', '')}")
                                elif et in (
                                    "node_started",
                                    "node_completed",
                                    "node_failed",
                                ):
                                    node = obj.get("node_id", "")
                                    if et == "node_failed":
                                        print(
                                            f"  [{et}] {node} error={obj.get('error', '')}"
                                        )
                                    else:
                                        print(f"  [{et}] {node}")
                                elif et in (
                                    "tool_called",
                                    "tool_completed",
                                    "tool_failed",
                                ):
                                    tool = obj.get("tool_name", "")
                                    print(f"  [{et}] {tool}")

                        elif msg.type in (
                            WSMsgType.CLOSED,
                            WSMsgType.CLOSE,
                            WSMsgType.ERROR,
                        ):
                            break

                recv_task = asyncio.create_task(_receiver())

                try:
                    while True:
                        # Read input
                        try:
                            line = await asyncio.get_event_loop().run_in_executor(
                                None, lambda: input("you> ")
                            )
                        except EOFError:
                            break

                        text = line.strip()
                        if not text:
                            continue

                        # Commands
                        if text in ("/quit", "/exit"):
                            break

                        if text == "/clear":
                            print("\033[2J\033[H", end="")
                            continue

                        if text.startswith("/thread "):
                            current_thread = (
                                text[len("/thread ") :].strip() or current_thread
                            )
                            print(f"✓ Switched to thread: {current_thread}")
                            continue

                        if text == "/pathways":
                            try:
                                async with session.get(
                                    f"{base_url}/api/v1/pathways"
                                ) as resp:
                                    data = await resp.json()
                                    pathways = data.get("pathways", [])
                                    print(f"\nPathways ({len(pathways)}):")
                                    for p in pathways:
                                        print(
                                            f"  • {p.get('id')} ({p.get('source', '')})"
                                        )
                                    print()
                            except Exception as e:
                                print(f"  error: {e}")
                            continue

                        # Minimal control plane: stream a pathway by id
                        if text.startswith("/run "):
                            pathway_id = text[len("/run ") :].strip()
                            if not pathway_id:
                                print("  usage: /run <pathway_id>")
                                continue
                            rpc_id += 1
                            rid = rpc_id
                            fut = asyncio.get_event_loop().create_future()
                            pending[rid] = fut
                            await ws.send_str(
                                json.dumps(
                                    {
                                        "jsonrpc": "2.0",
                                        "id": rid,
                                        "method": "pathway.stream_start",
                                        "params": {
                                            "pathway_id": pathway_id,
                                            "inputs": {},
                                        },
                                    }
                                )
                            )
                            try:
                                result = await asyncio.wait_for(fut, timeout=15.0)
                                print(f"✓ stream started: {result.get('stream_id')}")
                            except Exception as e:
                                print(f"  ❌ error: {e}")
                            continue

                        print("  unknown command. try: /run <pathway_id>")

                finally:
                    recv_task.cancel()
                    await asyncio.gather(recv_task, return_exceptions=True)

        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            return 1

    print("\n👋 Goodbye")
    return 0


def run_studio(*, host: str, port: int, thread_id: str) -> int:
    """Run terminal studio (blocking)."""
    try:
        return asyncio.run(_run_studio(host=host, port=port, thread_id=thread_id))
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
        return 0


__all__ = ["run_studio"]
