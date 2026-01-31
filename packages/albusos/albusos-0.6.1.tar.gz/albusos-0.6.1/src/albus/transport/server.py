"""AlbusServer - Main server entry point.

Starts HTTP server (and WebSocket in future) for Albus.

Usage:
    # Programmatic
    server = AlbusServer.create(pathway_vm=vm)
    await server.start(host="0.0.0.0", port=8080)
    
    # Or run directly
    python -m albus.transport.server
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiohttp import web

from albus.transport.http import create_http_app

if TYPE_CHECKING:
    from albus.application.runtime import AlbusRuntime
    from pathway_engine.application.kernel import PathwayVM
    from persistence.ports import ThreadStorePort

logger = logging.getLogger(__name__)


class AlbusServer:
    """Albus HTTP/WebSocket server.

    Wraps AlbusRuntime with transport layer.
    """

    def __init__(
        self,
        runtime: "AlbusRuntime",
        app: web.Application,
    ):
        self._runtime = runtime
        self._app = app
        self._runner: web.AppRunner | None = None

    @classmethod
    def create(
        cls,
        *,
        pathway_vm: "PathwayVM",
        thread_store: "ThreadStorePort | None" = None,
        debug: bool = False,
    ) -> "AlbusServer":
        """Create server with runtime.

        Args:
            pathway_vm: PathwayVM for executing pathways
            thread_store: Optional persistent storage
            debug: Enable debug logging

        Returns:
            Configured AlbusServer
        """
        from albus.application.runtime import AlbusRuntime

        # Create runtime
        runtime = AlbusRuntime.create(
            pathway_vm=pathway_vm,
            thread_store=thread_store,
            debug=debug,
        )

        # Create HTTP app
        app = create_http_app(runtime)

        return cls(runtime=runtime, app=app)

    @property
    def runtime(self) -> "AlbusRuntime":
        """Access the underlying runtime."""
        return self._runtime

    async def start(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> None:
        """Start the server.

        This runs until interrupted. Handles graceful shutdown.
        """
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        site = web.TCPSite(self._runner, host, port)
        await site.start()

        logger.info("Albus server started at http://%s:%d", host, port)
        print(f"\n🧙 Albus server running at http://{host}:{port}\n")
        print("API Version: v1 (all endpoints under /api/v1/)")
        print("\nKey Endpoints:")
        print("  GET  /api/v1/health          - Health check")
        print("  GET  /api/v1/tools           - List all tools")
        print("  GET  /api/v1/pathways        - List all pathways")
        print("  GET  /api/v1/ws              - WebSocket: events + JSON-RPC")
        print("  GET  /api/v1/help            - API documentation")
        print()
        print("Studio (terminal):")
        print(f"  albus studio --host {host} --port {port}")
        print("\nPress Ctrl+C to stop\n")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("Server shutdown requested")
            return

    async def stop(self, *, drain_timeout: float = 30.0) -> None:
        """Stop the server with graceful shutdown.

        Args:
            drain_timeout: Maximum time to wait for requests to complete (seconds)
        """
        if not self._runner:
            return

        logger.info(
            "Initiating graceful shutdown (drain_timeout=%.1fs)...", drain_timeout
        )

        # Stop accepting new connections
        try:
            # Give existing requests time to complete
            await asyncio.sleep(1.0)  # Brief pause for in-flight requests

            # Cleanup runner (this will close connections)
            await self._runner.cleanup()
            logger.info("Albus server stopped gracefully")
        except Exception as e:
            logger.warning("Error during shutdown: %s", e)
            # Force cleanup
            try:
                await self._runner.cleanup()
            except Exception:
                pass


async def _async_main(host: str, port: int, debug: bool):
    """Async main logic."""
    # Create PathwayVM with tools
    from pathway_engine.domain.context import Context
    from pathway_engine.application.kernel import PathwayVM
    from pathway_engine.domain.event_bus import AsyncEventBus
    from pathlib import Path

    # Load stdlib tool registrations (explicit, no shims).
    from stdlib.bootstrap import load_stdlib
    from stdlib.registry import TOOL_HANDLERS, TOOL_DEFINITIONS

    load_stdlib()

    # =========================================================================
    # DEPLOYMENT CONFIG - Load early so it can drive MCP wiring
    # =========================================================================
    from albus.infrastructure.deployment import DeploymentConfig

    deploy_config = DeploymentConfig.load()
    # Validate config (hard fail on invalid config)
    errors = deploy_config.validate()
    if errors:
        raise RuntimeError(
            f"Invalid deployment config ({deploy_config.source}): {errors}"
        )
    logger.info("Deployment config loaded from: %s", deploy_config.source)

    # Initialize MCP client and auto-register MCP tools as first-class tools
    mcp_client = None
    try:
        from pathway_engine.infrastructure.mcp import McpClientService
        from pathway_engine.infrastructure.mcp.client import McpServerConfig, McpSseServerConfig
        from stdlib.tools.mcp_autoregister import register_mcp_tools

        # Build MCP configs from DeploymentConfig (stdio + SSE)
        project_root = Path(__file__).resolve().parents[3]
        src_path = str(project_root / "src")

        stdio_servers: list[McpServerConfig] = []
        sse_servers: list[McpSseServerConfig] = []

        for spec in deploy_config.mcp_servers:
            if spec.transport == "stdio":
                if not spec.command:
                    continue

                env = dict(spec.env or {})
                # Helpful default for local python MCP servers living in this repo.
                if spec.command in ("python", "python3") and "PYTHONPATH" not in env:
                    env["PYTHONPATH"] = src_path

                stdio_servers.append(
                    McpServerConfig(
                        id=spec.id,
                        command=[spec.command],
                        args=list(spec.args or []),
                        env=env,
                        timeout_ms=int(getattr(spec, "timeout_s", 30) * 1000),
                    )
                )

            elif spec.transport == "sse":
                if not spec.url:
                    continue

                sse_servers.append(
                    McpSseServerConfig(
                        id=spec.id,
                        url=spec.url,
                        headers=dict(spec.headers or {}),
                        timeout_ms=int(getattr(spec, "timeout_s", 30) * 1000),
                        retry_attempts=int(getattr(spec, "retry_attempts", 3)),
                    )
                )

        if stdio_servers or sse_servers:
            mcp_client = McpClientService(servers=stdio_servers, sse_servers=sse_servers)
            mcp_tools = await register_mcp_tools(mcp_client)
            if mcp_tools:
                stdio_count = len(stdio_servers)
                sse_count = len(sse_servers)
                transport_info = []
                if stdio_count:
                    transport_info.append(f"{stdio_count} stdio")
                if sse_count:
                    transport_info.append(f"{sse_count} sse")
                print(
                    f"✓ Registered {len(mcp_tools)} MCP tools ({', '.join(transport_info)}): {mcp_tools[:5]}{'...' if len(mcp_tools) > 5 else ''}"
                )
    except Exception as e:
        logger.warning("Failed to initialize MCP: %s", e)

    # Build context with registered tools (now includes MCP tools)
    ctx = Context(tools=TOOL_HANDLERS)
    # Expose tool schemas for function-calling nodes (ToolCallingLLMNode).
    ctx.extras["tool_definitions"] = TOOL_DEFINITIONS

    # Expose MCP client to tools that need direct access
    if mcp_client:
        ctx.extras["mcp_client"] = mcp_client

    # Expose deployment config to handlers/tools
    ctx.extras["deployment_config"] = deploy_config

    # Expose executor to tools that need to run pathways recursively (best-effort).
    ctx.extras["pathway_executor"] = None  # placeholder until vm exists

    # Wire persistence domain + thread store (dev-first, file-backed) so builder actions
    # like pathway.create can persist without additional caller-supplied wiring.
    try:
        from persistence.infrastructure.storage.file.store import FileStudioStore
        from persistence.application.services.service import StudioDomainService

        store = FileStudioStore()
        ctx.extras["domain"] = StudioDomainService(store=store)
        ctx.extras["studio_store"] = store
        thread_store = store
    except Exception:
        thread_store = None

    vm = PathwayVM(ctx)
    ctx.extras["pathway_executor"] = vm

    # Wire event buffer for VM observability (used by introspection and streaming)
    ctx.extras.setdefault("event_buffer", [])
    event_bus = AsyncEventBus()
    # NOTE: this is an async pub/sub bus for streaming nodes (PathwayEngine),
    # not Albus's typed EventEmitter (observability).
    ctx.extras["event_bus"] = event_bus

    def on_vm_event(ev):
        try:
            payload = ev.model_dump()
            ts = payload.get("timestamp")
            if ts is not None:
                payload["timestamp"] = (
                    ts.isoformat() if hasattr(ts, "isoformat") else ts
                )
            buf = ctx.extras.get("event_buffer", [])
            buf.append(payload)
            if len(buf) > 2000:
                del buf[: len(buf) - 2000]
            event_bus.publish("pathway.events", payload)
        except Exception:
            logger.debug("Failed to record/publish VM event (non-fatal)", exc_info=True)

    vm.add_listener(on_vm_event)

    # Create server first (this creates PathwayService)
    server = AlbusServer.create(
        pathway_vm=vm,
        thread_store=thread_store,
        debug=debug,
    )
    
    # Schedule Host skills loading AFTER server is created (non-blocking background task)
    # This ensures skills load in background without blocking server startup
    async def load_host_skills_background():
        try:
            await server.runtime.agent_service.ensure_host_external_skills()
        except Exception as e:
            logger.warning(f"Background Host skills loading failed: {e}", exc_info=True)
    
    # Schedule as background task - won't block server startup
    asyncio.create_task(load_host_skills_background())

    # Apply model routing config from deployment config
    if deploy_config.models:
        server.runtime.apply_model_config(
            default_profile=deploy_config.models.default_profile,
            routing=deploy_config.models.routing,
        )

    # Wire up TriggerManager for event-driven pack execution
    from pathway_engine import TriggerManager, WEBHOOK_BUS

    trigger_manager = TriggerManager(
        webhook_bus=WEBHOOK_BUS,
        event_bus=event_bus,
    )

    # Create pathway invoker that TriggerManager calls when triggers fire
    async def invoke_pathway(pathway_id: str, inputs: dict, trigger_ctx):
        """Invoke a pathway when a trigger fires."""
        pathway_service = server.runtime.pathway_service
        pathway = pathway_service.load(pathway_id)
        if not pathway:
            logger.warning("Trigger fired for unknown pathway: %s", pathway_id)
            return {"error": f"pathway_not_found: {pathway_id}"}

        # Add trigger context to inputs
        inputs["_trigger"] = {
            "id": trigger_ctx.trigger_id,
            "pack_id": trigger_ctx.pack_id,
            "source": trigger_ctx.source,
            "event": trigger_ctx.event,
        }

        result = await vm.execute(pathway, inputs)
        return result.outputs

    trigger_manager.set_pathway_invoker(invoke_pathway)
    ctx.extras["trigger_manager"] = trigger_manager

    # Host state machine is registered via register_builtin_state_machines()
    # in runtime.py - use runtime.send_event() to interact with it

    try:
        await server.start(host=host, port=port)
    except OSError as e:
        # Common dev footgun: port already in use.
        # macOS: errno=48, Linux: errno=98
        if getattr(e, "errno", None) in (48, 98):
            print(f"\nPort {port} is already in use on {host}.")
            print("Fix options:")
            print(
                f"  - Use a different port:  uv run albus server --debug --port {port + 1}"
            )
            print(
                "  - Or set env:            ALBUS_PORT=8081 uv run albus server --debug"
            )
            print("  - Or stop the process currently using that port.\n")
            return
        raise
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    finally:
        # Shutdown MCP connections first (stops child processes cleanly)
        try:
            if mcp_client is not None:
                await mcp_client.close_all()
        except Exception:
            logger.warning("Error while closing MCP client", exc_info=True)

        # Shutdown trigger subscriptions first
        await trigger_manager.shutdown()
        await server.stop(drain_timeout=30.0)


def main():
    """CLI entry point."""
    import argparse
    import os
    import sys
    from pathlib import Path

    def _env_bool(name: str, default: bool = False) -> bool:
        v = os.getenv(name)
        if v is None:
            return default
        return v.strip().lower() in ("1", "true", "yes", "y", "on")

    # Add src to path for imports
    src_path = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Load environment files from project root
    from dotenv import load_dotenv

    # server.py is at: src/albus/transport/server.py (4 levels from root)
    project_root = Path(__file__).parent.parent.parent.parent

    # Load .env (base), then .env.local (overrides)
    env_file = project_root / ".env"
    env_local = project_root / ".env.local"

    loaded = []
    if env_file.exists():
        load_dotenv(env_file)
        loaded.append(".env")
    if env_local.exists():
        load_dotenv(env_local, override=True)
        loaded.append(".env.local")

    if loaded:
        print(f"✓ Loaded environment: {', '.join(loaded)}")
    else:
        print("⚠ No .env files found. Copy env.example to .env and configure.")

    parser = argparse.ArgumentParser(description="Run Albus server")
    parser.add_argument(
        "--host",
        default=os.getenv("ALBUS_HOST", "127.0.0.1"),
        help="Host to bind to (env: ALBUS_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("ALBUS_PORT", "8080")),
        help="Port to bind to (env: ALBUS_PORT)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=_env_bool("ALBUS_DEBUG", default=False),
        help="Enable debug event stream (env: ALBUS_DEBUG)",
    )
    parser.add_argument(
        "--log-level",
        default="",
        help="Python log level (e.g. INFO, DEBUG). Default: INFO. (env: ALBUS_LOG_LEVEL)",
    )
    args = parser.parse_args()

    # Configure logging (readable defaults; avoids flooding stdout in --debug).
    from albus.infrastructure.observability.logging_config import configure_logging

    configure_logging(debug=args.debug, log_level=args.log_level)

    asyncio.run(_async_main(args.host, args.port, args.debug))


if __name__ == "__main__":
    main()


__all__ = [
    "AlbusServer",
]
