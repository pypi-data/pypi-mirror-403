"""Pack registry for AlbusOS.

Packs are registered via the @deployable decorator at import time.

Usage:
    # In your pack module (e.g., src/packs/my_pack/pack.py)
    from packs.registry import deployable

    @deployable
    def MY_PACK():
        return (
            pack_builder()
            .id("my_pack")
            .name("My Pack")
            .pathway("my_pack.main.v1", build_main)
            .build()
        )

    # Or for simple packs:
    @deployable
    def MY_PACK():
        return Pack(id="my_pack", name="My Pack", ...)

The pack is automatically registered when its module is imported.
albus.yaml controls which registered packs actually get deployed at startup.
"""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import TYPE_CHECKING, Callable, Iterable, TypeVar

if TYPE_CHECKING:
    from pathway_engine.domain.pack import Pack

logger = logging.getLogger(__name__)

# Registry of available packs
_PACK_REGISTRY: dict[str, "Pack"] = {}

# Flag to track if packs have been bootstrapped
_BOOTSTRAPPED = False

T = TypeVar("T")


def deployable(
    func: Callable[[], "Pack"] | None = None,
    *,
    enabled: bool = True,
    env_gate: str | None = None,
) -> Callable[[], "Pack"] | Callable[[Callable[[], "Pack"]], Callable[[], "Pack"]]:
    """Decorator that registers a pack builder at import time.

    The decorated function should return a Pack. The pack is registered
    immediately when the module is imported.

    Args:
        func: Pack builder function (when used without arguments)
        enabled: Whether to register the pack (default True)
        env_gate: Optional env var that must be truthy to enable (e.g., "ALBUS_ENABLE_SEP")

    Examples:
        # Simple usage
        @deployable
        def MY_PACK():
            return Pack(id="my_pack", name="My Pack", ...)

        # With env gate
        @deployable(env_gate="ALBUS_ENABLE_EXPERIMENTAL")
        def EXPERIMENTAL_PACK():
            return Pack(id="experimental", ...)

        # Disabled (for development)
        @deployable(enabled=False)
        def WIP_PACK():
            return Pack(id="wip", ...)
    """

    def decorator(fn: Callable[[], "Pack"]) -> Callable[[], "Pack"]:
        @wraps(fn)
        def wrapper() -> "Pack":
            return fn()

        # Check if enabled
        should_register = enabled
        if env_gate:
            gate_val = os.getenv(env_gate, "").strip().lower()
            should_register = should_register and gate_val in ("1", "true", "yes", "on")

        if should_register:
            try:
                pack = fn()
                register_pack(pack)
                logger.debug("Registered pack: %s", pack.id)
            except Exception as e:
                logger.warning("Failed to register pack from %s: %s", fn.__name__, e)

        return wrapper

    if func is not None:
        # Called without arguments: @deployable
        return decorator(func)
    else:
        # Called with arguments: @deployable(env_gate="...")
        return decorator


def register_pack(pack: "Pack") -> None:
    """Register a pack in the registry."""
    _PACK_REGISTRY[pack.id] = pack


def _bootstrap_packs() -> None:
    """Import pack modules to trigger @deployable registration."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    _BOOTSTRAPPED = True

    # Add new packs here
    try:
        import packs.competitor_intel.pack  # noqa: F401
    except ImportError:
        pass

    try:
        import packs.image_narrator.pack  # noqa: F401
    except ImportError:
        pass

    try:
        import packs.voice_assistant.pack  # noqa: F401
    except ImportError:
        pass


def list_available_packs() -> list["Pack"]:
    """Return all registered packs."""
    _bootstrap_packs()
    return list(_PACK_REGISTRY.values())


def get_pack_by_id(pack_id: str) -> "Pack | None":
    """Get a pack by ID."""
    _bootstrap_packs()
    return _PACK_REGISTRY.get(pack_id)


def resolve_pack_ids(ids: Iterable[str]) -> tuple[list["Pack"], list[str]]:
    """Resolve pack IDs to Pack objects.

    Returns (packs, missing_ids).
    """
    packs: list["Pack"] = []
    missing: list[str] = []
    for pid in ids:
        p = get_pack_by_id(pid)
        if p is None:
            missing.append(pid)
        else:
            packs.append(p)
    return packs, missing


def clear_registry() -> None:
    """Clear all registered packs (for testing)."""
    global _BOOTSTRAPPED
    _PACK_REGISTRY.clear()
    _BOOTSTRAPPED = False


__all__ = [
    "deployable",
    "register_pack",
    "list_available_packs",
    "get_pack_by_id",
    "resolve_pack_ids",
    "clear_registry",
]
