"""Runtime Bridge - THE interface between Studio and Runtime.

This module provides the SINGLE bridge through which Studio interacts with Runtime.
Studio is the orchestrator, Runtime is the executor.

Architecture:
- Studio orchestrates. Runtime executes.
- Same VM, different kernels.
- RuntimeBridge hides kernel complexity from callers.

The bridge handles:
- Pathway execution (via PathwayVM with appropriate kernel)
- Kernel selection (PrivilegedKernel vs UserKernel)

This is NOT where execution happens - it's where Studio ASKS Runtime to execute.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from pathway_engine.application.ports.runtime import KernelProtocol

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRequest:
    """A request from Studio to Runtime to execute something."""

    pathway_id: str | None = None
    pathway: Any = None  # Pathway object
    inputs: dict[str, Any] | None = None
    context: dict[str, Any] | None = None

    # Execution options
    timeout_seconds: float | None = None
    priority: int = 0

    # Context
    workspace_id: str | None = None
    run_id: str | None = None

    # Kernel selection (for user pathways)
    kernel: Any | None = None  # KernelProtocol - if provided, uses custom kernel


@dataclass
class ExecutionResult:
    """Result of an execution from Runtime."""

    success: bool
    outputs: dict[str, Any] | None = None
    error: str | None = None

    # Metrics
    duration_ms: int | None = None
    node_count: int | None = None

    # For learning
    pathway_id: str | None = None
    run_id: str | None = None


class RuntimeBridge:
    """THE bridge between Studio and Runtime.

    Studio calls this to execute pathways.
    This is the SINGLE point of contact with pathway_engine.execution.

    Architecture: "Same VM, different kernels"
    - Default execution uses PrivilegedKernel (privileged, for Albus)
    - User pathways can specify a UserKernel via ExecutionRequest.kernel
    - The bridge handles kernel selection transparently
    """

    def __init__(
        self,
        *,
        pathway_vm: Any = None,  # PathwayVM (configured with PrivilegedKernel)
        studio_kernel: Any = None,  # KernelProtocol for Albus
        make_user_pathway_vm: Callable[["KernelProtocol"], Any] | None = None,
    ):
        self._pathway_vm = pathway_vm
        self._studio_kernel = studio_kernel
        self._make_user_pathway_vm = make_user_pathway_vm

    @property
    def pathway_vm(self) -> Any:
        """Get the default PathwayVM (uses PrivilegedKernel)."""
        return self._pathway_vm

    @property
    def studio_kernel(self) -> Any:
        """Get the PrivilegedKernel for Albus."""
        return self._studio_kernel

    async def execute_pathway(
        self,
        request: ExecutionRequest,
    ) -> ExecutionResult:
        """Execute a pathway through Runtime.

        Args:
            request: Execution request with pathway and inputs

        Returns:
            ExecutionResult with outputs or error

        Notes:
            - If request.kernel is provided, uses that kernel (for user pathways)
            - Otherwise uses PrivilegedKernel (for Albus)
        """
        # Select VM based on kernel
        if request.kernel is not None and self._make_user_pathway_vm is not None:
            # User pathway with custom kernel
            vm = self._make_user_pathway_vm(request.kernel)
        elif self._pathway_vm:
            # Default: PrivilegedKernel
            vm = self._pathway_vm
        else:
            return ExecutionResult(
                success=False,
                error="pathway_vm_not_configured",
            )

        pathway = request.pathway
        if not pathway and request.pathway_id:
            # Pathway loading by ID is not supported in RuntimeBridge.
            # The caller (in the `albus` layer) should use PathwayService to load
            # the pathway and pass it via request.pathway, due to layer constraints.
            return ExecutionResult(
                success=False,
                error=f"pathway_not_provided: caller must load pathway '{request.pathway_id}' and pass it via request.pathway",
            )

        if not pathway:
            return ExecutionResult(
                success=False,
                error="no_pathway_provided",
            )

        import time

        start = time.monotonic()

        try:
            # Execute via PathwayVM
            result = await vm.execute(
                pathway,
                inputs=request.inputs or {},
            )

            duration_ms = int((time.monotonic() - start) * 1000)

            return ExecutionResult(
                success=True,
                outputs=result.outputs if hasattr(result, "outputs") else result,
                duration_ms=duration_ms,
                pathway_id=request.pathway_id,
                run_id=request.run_id,
            )

        except Exception as e:
            logger.exception("Pathway execution failed")
            duration_ms = int((time.monotonic() - start) * 1000)
            return ExecutionResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                pathway_id=request.pathway_id,
            )

    @classmethod
    def from_studio_runtime(cls, runtime: Any) -> "RuntimeBridge":
        """Create a RuntimeBridge from a StudioRuntime.

        This is the preferred way to create a RuntimeBridge - it ensures
        all components are properly wired from the bootstrap.

        Args:
            runtime: StudioRuntime from persistence.bootstrap

        Returns:
            Configured RuntimeBridge
        """
        return cls(
            pathway_vm=runtime.pathway_vm,
            studio_kernel=runtime.studio_kernel,
            make_user_pathway_vm=runtime.make_user_pathway_vm,
        )


__all__ = [
    "ExecutionRequest",
    "ExecutionResult",
    "RuntimeBridge",
]
