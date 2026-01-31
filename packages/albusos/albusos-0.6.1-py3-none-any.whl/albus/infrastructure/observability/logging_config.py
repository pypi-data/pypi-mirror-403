"""Central logging configuration for Albus.

Goal: keep Albus debug signal readable while preventing extremely noisy
third-party DEBUG logs (httpx/httpcore/openai) from flooding the terminal.

Usage:
    from albus.infrastructure.observability.logging_config import configure_logging
    configure_logging(debug=args.debug, log_level=args.log_level)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Iterable


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _parse_level(level: str) -> int:
    lvl = (level or "").strip().upper()
    if not lvl:
        return logging.INFO
    return getattr(logging, lvl, logging.INFO)


def _set_levels(names: Iterable[str], level: int) -> None:
    for n in names:
        try:
            logging.getLogger(n).setLevel(level)
        except Exception:
            # Best-effort: never fail boot because a logger name is invalid.
            continue


def configure_logging(*, debug: bool = False, log_level: str | None = None) -> None:
    """Configure Python logging for Albus.

    Environment overrides:
      - ALBUS_LOG_LEVEL: Root log level (e.g. INFO, DEBUG)
      - ALBUS_HTTP_TRACE: If true, allow verbose HTTP/OpenAI logs in debug mode
      - ALBUS_ACCESS_LOG: If false, suppress aiohttp access logs
      - ALBUS_LOG_STYLE: "plain" (canonical)
    """
    # NOTE: `--debug` is about the event stream (DebugHandler), not about turning
    # the *entire* Python logging system to DEBUG (too noisy). Use --log-level
    # or ALBUS_LOG_LEVEL for that.
    env_level = os.getenv("ALBUS_LOG_LEVEL")
    root_level = _parse_level(env_level or (log_level or ""))
    if env_level is None and not (log_level or "").strip():
        root_level = logging.INFO

    # Canonical: plain logging (no extra deps).
    logging.basicConfig(
        level=root_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
        force=True,
    )

    # Make *our* logs useful in --debug, but keep third-party noise down.
    # Without this, openai/httpx/httpcore will emit giant request/response dumps.
    http_trace = _env_bool("ALBUS_HTTP_TRACE", default=False)
    # Local dev: access logs are noisy; default off unless explicitly enabled.
    access_log = _env_bool("ALBUS_ACCESS_LOG", default=bool(debug))

    # Prefer readable defaults: clamp the noisy stack unless explicitly tracing.
    if not http_trace:
        _set_levels(
            [
                "openai",
                "openai._base_client",
                "httpx",
                "httpcore",
                "httpcore.http11",
            ],
            logging.WARNING,
        )

    # aiohttp access logs can overwhelm local dev runs; keep on by default.
    if not access_log:
        _set_levels(["aiohttp.access"], logging.WARNING)

    # Asyncio can be surprisingly chatty in some environments.
    if debug:
        _set_levels(["asyncio"], logging.INFO)


__all__ = ["configure_logging"]
