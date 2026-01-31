"""albus.sdk - Product-layer SDK surface.

Albus is the product/host layer (server + runtime wiring). This SDK provides a
small, stable "front door" for programmatic usage.

Typical usage (dev):
    from albus.sdk import create_dev_vm, create_runtime
    vm = await create_dev_vm()
    runtime = create_runtime(pathway_vm=vm, debug=True)
    # execute pathways directly via `Flow` / PathwayVM
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from typing import Any, AsyncIterator, Protocol, TypeVar

logger = logging.getLogger(__name__)

TPathway = TypeVar("TPathway")


class _CompilableToPathway(Protocol):
    def compile(self) -> Any: ...


def _coerce_pathway(obj: Any) -> Any:
    """Accept a runtime Pathway OR a callable that returns a Pathway.

    This allows pathways to be defined as functions that return Pathway objects.
    """

    compile_fn = getattr(obj, "compile", None)
    if callable(compile_fn):
        return compile_fn()
    return obj


@dataclass(frozen=True)
class Flow:
    """Unified author+run facade: pass a PathwayProgram OR a runtime Pathway."""

    vm: Any  # PathwayVM

    async def run(
        self,
        pathway_or_program: Any,
        inputs: dict[str, Any] | None = None,
        *,
        execution_id: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        pathway = _coerce_pathway(pathway_or_program)
        return await self.vm.execute(
            pathway,
            inputs or {},
            execution_id=execution_id,
            timeout=timeout,
        )

    async def stream(
        self,
        pathway_or_program: Any,
        inputs: dict[str, Any] | None = None,
        *,
        max_events: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        pathway = _coerce_pathway(pathway_or_program)
        async for item in self.vm.stream_execute(
            pathway,
            inputs or {},
            max_events=max_events,
        ):
            yield item


async def create_dev_vm(
    *,
    enable_mcp: bool = True,
    enable_file_backed_persistence: bool = True,
) -> "PathwayVM":
    """Create a dev-friendly PathwayVM wired similarly to `albus.transport.server`.

    - Loads stdlib tool registrations.
    - Builds a `Context` with tool handlers.
    - Exposes tool definitions for ToolCallingLLMNode via `ctx.services.tool_definitions`.
    - Best-effort wires file-backed persistence + MCP auto-registration if available.
    """

    from pathway_engine.domain.context import Context
    from pathway_engine.application.kernel import PathwayVM

    # Load stdlib tool registrations (explicit, no shims).
    from stdlib.bootstrap import load_stdlib
    from stdlib.registry import TOOL_HANDLERS, TOOL_DEFINITIONS

    load_stdlib()

    mcp_client: Any | None = None
    if enable_mcp:
        try:
            from albus.infrastructure.deployment import DeploymentConfig
            from pathway_engine.infrastructure.mcp import McpClientService
            from pathway_engine.infrastructure.mcp.client import McpServerConfig
            from stdlib.tools.mcp_autoregister import register_mcp_tools

            cfg = DeploymentConfig.load()
            servers: list[McpServerConfig] = []
            for spec in cfg.mcp_servers:
                if spec.transport != "stdio" or not spec.command:
                    continue
                env = dict(spec.env or {})
                if spec.command in ("python", "python3") and "PYTHONPATH" not in env:
                    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
                servers.append(
                    McpServerConfig(
                        id=spec.id,
                        command=[spec.command],
                        args=list(spec.args or []),
                        env=env,
                        timeout_ms=int(getattr(spec, "timeout_s", 30) * 1000),
                    )
                )
            if servers:
                mcp_client = McpClientService(servers=servers)
                await register_mcp_tools(mcp_client)
        except Exception:
            logger.debug("MCP initialization failed (non-fatal)", exc_info=True)

    ctx = Context(tools=TOOL_HANDLERS)
    ctx.services.tool_definitions = TOOL_DEFINITIONS

    if mcp_client is not None:
        ctx.services.mcp_client = mcp_client

    # Expose executor for tools that need to run pathways recursively.
    ctx.services.pathway_executor = None  # placeholder until vm exists

    if enable_file_backed_persistence:
        try:
            from persistence.infrastructure.storage.file.store import FileStudioStore
            from persistence.application.services.service import StudioDomainService

            store = FileStudioStore()
            ctx.services.domain = StudioDomainService(store=store)
            ctx.extras["studio_store"] = store
        except Exception:
            logger.debug(
                "File-backed persistence wiring failed (non-fatal)", exc_info=True
            )

    vm = PathwayVM(ctx)
    ctx.services.pathway_executor = vm
    return vm


async def create_dev_flow(
    *,
    enable_mcp: bool = True,
    enable_file_backed_persistence: bool = True,
) -> Flow:
    """Create a dev Flow facade (VM + stdlib wiring)."""

    vm = await create_dev_vm(
        enable_mcp=enable_mcp,
        enable_file_backed_persistence=enable_file_backed_persistence,
    )
    return Flow(vm=vm)


def create_runtime(
    *,
    pathway_vm: "PathwayVM",
    thread_store: "ThreadStorePort | None" = None,
    studio_store: "StudioStore | None" = None,
    pathway_service: "PathwayService | None" = None,
    debug: bool = False,
) -> "AlbusRuntime":
    """Create an `AlbusRuntime` with standard wiring (recommended)."""

    from albus.application.runtime import AlbusRuntime

    return AlbusRuntime.create(
        pathway_vm=pathway_vm,
        thread_store=thread_store,
        studio_store=studio_store,
        pathway_service=pathway_service,
        debug=debug,
    )


def create_server(
    *,
    pathway_vm: "PathwayVM",
    thread_store: "ThreadStorePort | None" = None,
    debug: bool = False,
) -> "AlbusServer":
    """Create an `AlbusServer` (HTTP transport wrapper)."""

    from albus.transport.server import AlbusServer

    return AlbusServer.create(
        pathway_vm=pathway_vm, thread_store=thread_store, debug=debug
    )


__all__ = [
    "Flow",
    "create_dev_vm",
    "create_dev_flow",
    "create_runtime",
    "create_server",
]
