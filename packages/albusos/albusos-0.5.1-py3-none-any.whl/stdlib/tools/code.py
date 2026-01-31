"""Code Execution Tools - Sandboxed Python code execution.

Provides secure, isolated code execution for pathways and Albus.
Uses subprocess isolation with resource limits.

Tools:
- code.execute: Run Python code in a sandboxed subprocess
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any

from pathway_engine.application.ports.tool_registry import ToolContext
from pathway_engine.infrastructure.sandbox import run_python_sandboxed
from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


def _clamp_int(v: Any, *, default: int, lo: int, hi: int) -> int:
    try:
        x = int(v)
    except Exception:
        x = default
    return max(lo, min(hi, x))


def _coerce_bool(v: Any, *, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "yes", "y", "on"):
            return True
        if s in ("0", "false", "no", "n", "off", ""):
            return False
    return default


@register_tool(
    "code.execute",
    description="Execute Python code in a secure sandbox. Returns result from main(input) or a global 'result' variable.",
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute. Define main(input) or set result = ...",
            },
            "language": {
                "type": "string",
                "description": "Execution language (currently only 'python' is supported).",
                "default": "python",
            },
            "profile": {
                "type": "string",
                "description": (
                    "Optional sandbox profile name (e.g. 'datascience', 'viz'). "
                    "Profiles are allowlisted by ops via env vars: "
                    "ALBUS_CODE_SANDBOX_DOCKER_IMAGE_<PROFILE>. "
                    "If omitted, falls back to AGENT_STDLIB_CODE_SANDBOX_DOCKER_IMAGE / 'python:3.11-slim'."
                ),
            },
            "inputs": {
                "type": "object",
                "description": "Input data available as 'input' variable",
            },
            "timeout_ms": {
                "type": "integer",
                "description": "Execution timeout in milliseconds (default: 10000, max: 60000)",
            },
            "memory_mb": {
                "type": "integer",
                "description": "Memory limit in MB (default: 256, max: 1024)",
            },
            "allow_site_packages": {
                "type": "boolean",
                "description": "Allow access to installed packages like pandas, numpy, etc. (default: false)",
            },
        },
        "required": ["code"],
    },
    requires_privileged=True,  # Code execution requires elevated permissions
)
async def code_execute(inputs: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    """Execute Python code in a sandboxed subprocess.

    The code can:
    - Define `def main(input):` which will be called with the input data
    - Set a global `result = ...` variable
    - Use `input` variable to access input data

    Returns:
        {
            "ok": bool,        # Whether execution succeeded
            "result": any,     # Return value from main() or global result
            "output": any,     # Alias for result
            "stdout": str,     # Captured stdout
            "stderr": str,     # Captured stderr
            "duration_ms": float,
            "error": str|None, # Error message if failed
        }

    Example code:
        ```python
        def main(input):
            return {"sum": input["a"] + input["b"]}
        ```

        Or simply:
        ```python
        result = input["a"] + input["b"]
        ```
    """
    code = str(inputs.get("code", "")).strip()
    if not code:
        return {
            "ok": False,
            "error": "code is required",
            "output": None,
            "stdout": "",
            "stderr": "",
        }

    language = str(inputs.get("language", "python") or "python").strip().lower()
    if language not in ("python", "py"):
        return {
            "ok": False,
            "error": f"unsupported_language:{language}",
            "output": None,
            "stdout": "",
            "stderr": "",
        }

    # Clamp limits for safety (be robust to None / strings)
    timeout_ms = _clamp_int(inputs.get("timeout_ms"), default=10_000, lo=1, hi=60_000)
    memory_mb = _clamp_int(inputs.get("memory_mb"), default=256, lo=16, hi=1024)
    allow_site_packages = _coerce_bool(inputs.get("allow_site_packages"), default=False)

    input_obj = inputs.get("inputs", {})
    if input_obj is None:
        input_obj = {}
    if not isinstance(input_obj, dict):
        return {
            "ok": False,
            "error": "invalid_inputs_type",
            "output": None,
            "stdout": "",
            "stderr": "",
        }

    # Sandbox mode:
    # - For untrusted user code, Docker is the only meaningful security boundary.
    # - Default to docker; developers can opt into local mode explicitly.
    mode = str(os.getenv("AGENT_STDLIB_CODE_SANDBOX_MODE", "docker")).strip().lower()
    if mode not in ("docker", "local"):
        mode = "docker"

    # Docker image is an ops policy decision: configure via env var(s), not per-call.
    # Support profiles via allowlisted env vars (no arbitrary image strings in inputs).
    profile_raw = inputs.get("profile")
    docker_image: str
    if profile_raw:
        profile = str(profile_raw).strip().lower()
        # Restrict profile names to safe identifier chars to avoid env var tricks.
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,31}", profile):
            return {
                "ok": False,
                "error": f"invalid_profile:{profile}",
                "output": None,
                "stdout": "",
                "stderr": "",
            }
        key = f"ALBUS_CODE_SANDBOX_DOCKER_IMAGE_{profile.upper().replace('-', '_')}"
        docker_image = (os.getenv(key) or "").strip()
        if not docker_image:
            return {
                "ok": False,
                "error": f"unknown_profile:{profile}",
                "output": None,
                "stdout": "",
                "stderr": "",
            }
    else:
        docker_image = (
            os.getenv("AGENT_STDLIB_CODE_SANDBOX_DOCKER_IMAGE") or ""
        ).strip() or "python:3.11-slim"

    # In docker mode, do NOT allow site packages unless the operator explicitly enables it.
    # (This is still isolated by container boundaries, but increases surface area.)
    if mode == "docker" and allow_site_packages:
        logger.info(
            "allow_site_packages=True with docker sandbox (image=%s); "
            "ensure the image has required packages pre-installed.",
            docker_image,
        )

    logger.debug(
        "Executing sandboxed code (mode=%s, timeout=%dms, memory=%dMB, image=%s, site_packages=%s)",
        mode,
        timeout_ms,
        memory_mb,
        docker_image if mode == "docker" else "N/A",
        allow_site_packages,
    )

    # Run in sandbox (do NOT block the event loop)
    result = await asyncio.to_thread(
        run_python_sandboxed,
        code=code,
        input_obj=input_obj,
        timeout_ms=timeout_ms,
        memory_mb=memory_mb,
        allow_site_packages=allow_site_packages,
        sandbox="docker" if mode == "docker" else "local",
        docker_image=docker_image,
    )

    # Normalize output
    return {
        "ok": result.get("ok", False),
        "result": result.get("result"),
        "output": result.get("result"),  # Alias
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "duration_ms": result.get("duration_ms", 0),
        "error": result.get("error"),
        "traceback": result.get("traceback"),
    }


__all__ = ["code_execute"]
