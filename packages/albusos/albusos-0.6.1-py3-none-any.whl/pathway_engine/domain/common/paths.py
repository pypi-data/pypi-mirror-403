"""Filesystem path helpers (repo-root aware).

Many parts of Albus load *repo-owned artifacts* (schemas, prompts, packs, etc.).
Historically these were accessed via CWD-relative paths like `Path("schemas/...")`,
which breaks easily when the process isn't started from the repo root.

This module centralizes that logic so callers can resolve stable absolute paths.

Resource locations:
- pathway_engine/resources/       - optional templates / DSL artifacts (if present)
- albus/resources/                - prompts, schemas, model configs (if present)
- config/                   - model_skus.json (runtime config)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Return the repo root directory (src-layout aware).

    Resolution order:
    - Explicit env override: `PATHWAY_REPO_ROOT` or `PATHWAY_ROOT`
    - Heuristic based on this file's location (src-layout)
    - Upward search for `pyproject.toml` and/or `src/`
    """

    env = (os.getenv("PATHWAY_REPO_ROOT") or os.getenv("PATHWAY_ROOT") or "").strip()
    if env:
        return Path(env).expanduser().resolve()

    here = Path(__file__).resolve()

    # Typical src-layout: <root>/src/pathway_engine/paths.py
    # - parents[0] = pathway_engine/
    # - parents[1] = src/
    # - parents[2] = <root>/
    try:
        candidate = here.parents[2]
        if (candidate / "pyproject.toml").exists():
            return candidate
    except Exception:
        candidate = Path.cwd()

    for p in here.parents:
        if (p / "pyproject.toml").exists() and (p / "src").exists():
            return p

    return candidate


def src_dir() -> Path:
    """Return the src/ directory."""
    return repo_root() / "src"


def config_dir() -> Path:
    """Return the config/ directory (runtime configuration)."""
    return repo_root() / "config"


def pathway_engine_resources_dir() -> Path:
    """Return pathway_engine/resources/ directory.

    This directory is optional in this repo; callers should not assume it exists.
    """
    return src_dir() / "pathway_engine" / "resources"


def albus_resources_dir() -> Path:
    """Return albus/resources/ directory.

    This directory is optional in this repo; callers should not assume it exists.
    """
    return src_dir() / "albus" / "resources"


def schemas_dir() -> Path:
    """Return the directory containing system JSON schemas.

    Returns albus/resources/schemas/ which contains:
    - models/ - model configuration schemas
    """
    return albus_resources_dir() / "schemas"


def prompts_dir() -> Path:
    """Return the prompts directory."""
    return albus_resources_dir() / "prompts"


def templates_dir() -> Path:
    """Return the pathway templates directory."""
    return pathway_engine_resources_dir() / "templates"


def data_dir() -> Path:
    """Return the data directory for runtime state."""
    return repo_root() / "data"


__all__ = [
    "repo_root",
    "src_dir",
    "config_dir",
    "pathway_engine_resources_dir",
    "albus_resources_dir",
    "schemas_dir",
    "prompts_dir",
    "templates_dir",
    "data_dir",
]
