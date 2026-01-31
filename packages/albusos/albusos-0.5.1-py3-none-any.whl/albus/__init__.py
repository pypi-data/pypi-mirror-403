"""albus - built-in system agent (server + UI + product scaffolds).

Albus is the default system agent/shell, powered by:
- Runtime kernel: `pathway_engine` (execution + authoring)
- Stdlib tools: `stdlib` (runtime-neutral tools)

Albus is not the runtime kernel; it is the product-layer agent and host.
"""

from __future__ import annotations

# No public re-exports. Import directly from submodules, e.g.:
#   from albus.application.runtime import AlbusRuntime

__all__: list[str] = []
