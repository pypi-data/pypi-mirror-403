from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Literal


def _truthy_env(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "y", "on")


def _clamp_int(v: Any, *, default: int, lo: int, hi: int) -> int:
    try:
        x = int(v)
    except Exception:
        return default
    return max(lo, min(hi, x))


_RUNNER_SOURCE = r"""
from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any


def _jsonable(x: Any) -> Any:
    try:
        json.dumps(x)
        return x
    except Exception:
        return {"__repr__": repr(x)}


def _load_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def main() -> int:
    payload = _load_stdin_json()
    code = payload.get("code")
    inp = payload.get("input")

    out: dict[str, Any] = {"ok": False}
    try:
        if not isinstance(code, str) or not code.strip():
            raise ValueError("missing_code")

        g: dict[str, Any] = {"__name__": "__main__", "input": inp}
        exec(compile(code, "<python.run>", "exec"), g, g)  # noqa: S102 - intentional tool boundary

        res: Any = None
        fn = g.get("main")
        if callable(fn):
            res = fn(inp)
        elif "result" in g:
            res = g.get("result")
        else:
            res = None

        out = {"ok": True, "result": _jsonable(res)}
    except Exception as e:  # noqa: BLE001 - tool boundary
        out = {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    try:
        with open("__albus_result.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
    except Exception:
        # If we can't write results, there's nothing else we can do.
        pass
    return 0 if out.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _docker_available() -> tuple[bool, str]:
    """Return (available, note)."""
    if shutil.which("docker") is None:
        return False, "docker_not_found"
    try:
        # Quick, low-noise check that the daemon is reachable.
        p = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2.5,
            check=False,
        )
        if p.returncode != 0:
            err = (p.stderr or b"").decode("utf-8", errors="replace").strip()
            return False, f"docker_unavailable:{err[:200]}"
        return True, "ok"
    except Exception as e:  # noqa: BLE001 - sandbox boundary
        return False, f"docker_unavailable:{e}"


def _docker_image_present(image: str) -> bool:
    try:
        p = subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.5,
            check=False,
        )
        return p.returncode == 0
    except Exception:
        return False


def _run_python_sandboxed_docker(
    *,
    code: str,
    input_obj: Any = None,
    timeout_ms: int = 10_000,
    memory_mb: int = 256,
    cpu_seconds: int = 5,
    max_output_kb: int = 256,
    allow_site_packages: bool = False,
    docker_image: str = "python:3.11-slim",
) -> dict[str, Any]:
    """Execute code inside a hardened Docker sandbox.

    Security properties (best-effort, depends on host Docker daemon):
    - No network: --network=none
    - No host filesystem access: only mounts a temp workdir to /work
    - Read-only root filesystem: --read-only (workdir remains writable)
    - Drops Linux capabilities: --cap-drop=ALL + no-new-privileges
    """
    t0 = time.time()
    ok, note = _docker_available()
    if not ok:
        return {
            "ok": False,
            "error": f"docker_required:{note}",
            "stdout": "",
            "stderr": "",
            "duration_ms": (time.time() - t0) * 1000.0,
        }

    # Do not attempt to pull images automatically; in secure deployments, images
    # should be pre-pulled / pinned by ops.
    if not _docker_image_present(docker_image):
        return {
            "ok": False,
            "error": f"docker_image_missing:{docker_image}",
            "stdout": "",
            "stderr": "",
            "duration_ms": (time.time() - t0) * 1000.0,
        }

    timeout_ms_i = _clamp_int(timeout_ms, default=10_000, lo=1, hi=600_000)
    memory_mb_i = _clamp_int(memory_mb, default=256, lo=16, hi=16_384)
    cpu_seconds_i = _clamp_int(cpu_seconds, default=5, lo=1, hi=600)
    max_output_kb_i = _clamp_int(max_output_kb, default=256, lo=1, hi=8192)

    with tempfile.TemporaryDirectory(prefix="albus_py_docker_") as td:
        # Ensure an unprivileged container user can write results.
        try:
            os.chmod(td, 0o777)
        except Exception:
            pass

        wd = Path(td)
        runner_path = wd / "_runner.py"
        runner_path.write_text(_RUNNER_SOURCE, encoding="utf-8")

        payload = {"code": code, "input": input_obj}
        stdin = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

        stdout_limit = max_output_kb_i * 1024
        stderr_limit = max_output_kb_i * 1024

        # Hardened container flags:
        # - No network
        # - Read-only root
        # - Drop caps + no-new-privileges
        # - Limit pids, memory, cpu
        # - Limit file sizes and open files via ulimit where supported
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            # Keep stdin open so we can pass the JSON payload via communicate().
            # Without this, sys.stdin.read() inside the container is empty and user code never runs.
            "-i",
            "--network=none",
            "--read-only",
            "--security-opt",
            "no-new-privileges",
            "--cap-drop=ALL",
            "--pids-limit=64",
            "--memory",
            f"{int(memory_mb_i)}m",
            "--cpus",
            "1",
            "--ulimit",
            "nofile=64:64",
            "--ulimit",
            "fsize=5242880:5242880",
            "--user",
            "65534:65534",
            "-v",
            f"{str(wd)}:/work:rw",
            "-w",
            "/work",
            docker_image,
            "python",
            "-u",
        ]

        if not allow_site_packages:
            docker_cmd += ["-I", "-S"]

        docker_cmd += ["/work/_runner.py"]

        proc = subprocess.Popen(
            docker_cmd,
            cwd=str(wd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            out_b, err_b = proc.communicate(stdin, timeout=timeout_ms_i / 1000.0)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "ok": False,
                "error": "timeout",
                "stdout": "",
                "stderr": "",
                "duration_ms": (time.time() - t0) * 1000.0,
            }

        stdout = (out_b or b"")[:stdout_limit].decode("utf-8", errors="replace")
        stderr = (err_b or b"")[:stderr_limit].decode("utf-8", errors="replace")

        result_path = wd / "__albus_result.json"
        result_obj: dict[str, Any] | None = None
        if result_path.exists():
            try:
                result_obj = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception:
                result_obj = None

        if not isinstance(result_obj, dict):
            return {
                "ok": False,
                "error": f"docker_runner_failed:exit_code={proc.returncode}",
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": (time.time() - t0) * 1000.0,
            }

        result_obj["stdout"] = stdout
        result_obj["stderr"] = stderr
        result_obj["duration_ms"] = (time.time() - t0) * 1000.0
        # Helpful for debugging but not required.
        result_obj.setdefault("sandbox", "docker")
        result_obj.setdefault("cpu_seconds", cpu_seconds_i)
        return result_obj


def run_python_sandboxed(
    *,
    code: str,
    input_obj: Any = None,
    timeout_ms: int = 10_000,
    memory_mb: int = 256,
    cpu_seconds: int = 5,
    max_output_kb: int = 256,
    allow_site_packages: bool = False,
    python_executable: str | None = None,
    sandbox: Literal["local", "docker"] = "local",
    docker_image: str = "python:3.11-slim",
) -> dict[str, Any]:
    """Execute Python code in a separate process with best-effort local sandboxing.

    Contract:
    - Input: JSON object with `code` (required) and `input` (optional)
    - User code may define:
        - `def main(input): ...` (preferred), or
        - set a global `result = ...`
    - Output: JSON object:
        {"ok": bool, "result": any?, "stdout": str, "stderr": str, "error": str?}
    """
    if sandbox == "docker":
        return _run_python_sandboxed_docker(
            code=code,
            input_obj=input_obj,
            timeout_ms=timeout_ms,
            memory_mb=memory_mb,
            cpu_seconds=cpu_seconds,
            max_output_kb=max_output_kb,
            allow_site_packages=allow_site_packages,
            docker_image=docker_image,
        )

    t0 = time.time()
    timeout_ms_i = _clamp_int(timeout_ms, default=10_000, lo=1, hi=600_000)
    memory_mb_i = _clamp_int(memory_mb, default=256, lo=16, hi=16_384)
    cpu_seconds_i = _clamp_int(cpu_seconds, default=5, lo=1, hi=600)
    max_output_kb_i = _clamp_int(max_output_kb, default=256, lo=1, hi=8192)

    py = str(python_executable).strip() if python_executable else sys.executable
    if not py:
        py = sys.executable

    with tempfile.TemporaryDirectory(prefix="albus_py_") as td:
        wd = Path(td)
        runner_path = wd / "_runner.py"
        runner_path.write_text(_RUNNER_SOURCE, encoding="utf-8")

        env = {
            # Minimal env: keep it deterministic.
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONHASHSEED": "0",
            # Explicitly strip user-site imports even if user tries.
            "PYTHONNOUSERSITE": "1",
        }

        # Allow opt-in passthrough (debug only).
        if _truthy_env("PATHWAY_PYTHON_TOOL_PASSTHROUGH_ENV"):
            for k, v in os.environ.items():
                if isinstance(k, str) and isinstance(v, str):
                    env.setdefault(k, v)

        args = [py, "-u"]
        if not allow_site_packages:
            # -I: isolate environment, -S: don't import site
            args += ["-I", "-S"]
        args.append(str(runner_path))

        payload = {"code": code, "input": input_obj}
        stdin = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

        stdout_limit = max_output_kb_i * 1024
        stderr_limit = max_output_kb_i * 1024

        def _limit_child() -> None:
            # Best-effort POSIX resource limits (macOS/Linux).
            try:
                os.setsid()
            except Exception:
                pass
            try:
                import resource  # noqa: PLC0415

                # CPU time (seconds).
                resource.setrlimit(
                    resource.RLIMIT_CPU, (cpu_seconds_i, cpu_seconds_i + 1)
                )
                # Address space (bytes).
                mem_bytes = int(memory_mb_i) * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                # File size (bytes).
                resource.setrlimit(
                    resource.RLIMIT_FSIZE, (5 * 1024 * 1024, 5 * 1024 * 1024)
                )
                # Open files.
                resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
            except Exception:
                # Non-fatal; we still have wall-clock timeout and process isolation.
                pass

        proc = subprocess.Popen(
            args,
            cwd=str(wd),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=_limit_child if os.name == "posix" else None,
        )

        try:
            out_b, err_b = proc.communicate(stdin, timeout=timeout_ms_i / 1000.0)
        except subprocess.TimeoutExpired:
            try:
                # Kill process group if possible.
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            except Exception:
                pass
            return {
                "ok": False,
                "error": "timeout",
                "stdout": "",
                "stderr": "",
                "duration_ms": (time.time() - t0) * 1000.0,
            }

        stdout = (out_b or b"")[:stdout_limit].decode("utf-8", errors="replace")
        stderr = (err_b or b"")[:stderr_limit].decode("utf-8", errors="replace")

        result_path = wd / "__albus_result.json"
        result_obj: dict[str, Any] | None = None
        if result_path.exists():
            try:
                result_obj = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception:
                result_obj = None

        if not isinstance(result_obj, dict):
            # Fall back to exit-code based failure.
            return {
                "ok": False,
                "error": f"python_runner_failed:exit_code={proc.returncode}",
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": (time.time() - t0) * 1000.0,
            }

        # Attach captured streams + timing.
        result_obj["stdout"] = stdout
        result_obj["stderr"] = stderr
        result_obj["duration_ms"] = (time.time() - t0) * 1000.0
        return result_obj


__all__ = ["run_python_sandboxed"]
