"""Tools export for pathway CLI.

This module bootstraps the stdlib and exposes TOOL_HANDLERS for the CLI.

Usage:
    uv run pathway run --target my_flow:build --tools stdlib.tools_export:TOOL_HANDLERS
"""

from stdlib.bootstrap import load_stdlib
from stdlib.registry import TOOL_HANDLERS, TOOL_DEFINITIONS

# Bootstrap at import time (this is what CLI expects)
load_stdlib()

__all__ = ["TOOL_HANDLERS", "TOOL_DEFINITIONS"]
