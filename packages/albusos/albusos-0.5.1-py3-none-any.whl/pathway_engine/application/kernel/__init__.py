"""VM - The graph execution engine.

PathwayVM executes graphs by calling node.compute() directly.
No resolvers, no type lookups - nodes know how to execute themselves.
"""

from pathway_engine.application.kernel.vm import PathwayVM, PathwayPriority

__all__ = [
    # Core VM
    "PathwayVM",
    "PathwayPriority",
]
