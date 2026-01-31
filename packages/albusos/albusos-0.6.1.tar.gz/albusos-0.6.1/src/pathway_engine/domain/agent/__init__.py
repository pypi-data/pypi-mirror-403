"""Agent package - Persistent AI entities with identity, memory, and capabilities.

Core abstractions:
- Agent: Persistent AI entity with persona, goals, and cognitive style
- Skill: A pathway exposed as a tool
"""

from .cognitive import (
    ReasoningMode,
    OrationMode,
    SupervisionMode,
    CognitiveStyle,
    CognitivePresets,
)
from .memory import MemoryScope, AgentMemoryConfig
from .capabilities import AgentCapabilities, ProactiveTrigger
from .state import AgentState
from .core import Agent
from .builder import AgentBuilder, agent_builder
from .skill import Skill, skill

__all__ = [
    # Agent
    "Agent",
    "AgentBuilder",
    "agent_builder",
    # Skills
    "Skill",
    "skill",
    # Cognitive
    "ReasoningMode",
    "OrationMode",
    "SupervisionMode",
    "CognitiveStyle",
    "CognitivePresets",
    # Memory
    "MemoryScope",
    "AgentMemoryConfig",
    # Capabilities
    "AgentCapabilities",
    "ProactiveTrigger",
    # State
    "AgentState",
]
