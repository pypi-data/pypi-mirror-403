"""Cognitive modes - How agents think, communicate, and coordinate.

This module defines the cognitive primitives that shape agent behavior:
- ReasoningMode: How the agent approaches problems
- OrationMode: How the agent communicates
- SupervisionMode: How the agent coordinates work
- CognitiveStyle: Combined style configuration
- CognitivePresets: Pre-built styles for common patterns
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReasoningMode(str, Enum):
    """How the agent approaches problem-solving.

    REACTIVE: Quick, instinctive responses. Best for simple queries.
    DELIBERATIVE: Step-by-step reasoning, shows work. Best for complex tasks.
    REFLECTIVE: Reviews and critiques own outputs. Best for high-stakes decisions.
    """

    REACTIVE = "reactive"
    DELIBERATIVE = "deliberative"
    REFLECTIVE = "reflective"


class OrationMode(str, Enum):
    """How the agent communicates.

    CONCISE: Brief, to the point. Minimal explanation.
    CONVERSATIONAL: Natural, friendly dialogue.
    ELABORATE: Detailed explanations, thorough coverage.
    SOCRATIC: Questions to understand, guides discovery.
    FORMAL: Professional, structured communication.
    """

    CONCISE = "concise"
    CONVERSATIONAL = "conversational"
    ELABORATE = "elaborate"
    SOCRATIC = "socratic"
    FORMAL = "formal"


class SupervisionMode(str, Enum):
    """How the agent coordinates work.

    AUTONOMOUS: Works alone, makes all decisions.
    COLLABORATIVE: Works with user, seeks input.
    DELEGATING: Assigns work to skills/sub-agents.
    ORCHESTRATING: Full supervisor - plans, delegates, monitors, aggregates.
    """

    AUTONOMOUS = "autonomous"
    COLLABORATIVE = "collaborative"
    DELEGATING = "delegating"
    ORCHESTRATING = "orchestrating"


@dataclass
class CognitiveStyle:
    """Defines HOW an agent thinks and communicates.

    This is separate from WHAT the agent knows (persona/goals) and
    WHAT it can do (capabilities). Cognitive style shapes the agent's
    approach to any task.
    """

    reasoning: ReasoningMode = ReasoningMode.DELIBERATIVE
    oration: OrationMode = OrationMode.CONVERSATIONAL
    supervision: SupervisionMode = SupervisionMode.AUTONOMOUS

    # Style modifier (the only one actually used in prompt generation)
    caution: float = 0.5  # 0=bold, 1=cautious

    def to_system_prompt_section(self) -> str:
        """Generate system prompt instructions for this cognitive style."""
        parts = []

        # Reasoning instructions
        if self.reasoning == ReasoningMode.REACTIVE:
            parts.append(
                "Respond quickly and directly. Don't over-explain or show lengthy reasoning."
            )
        elif self.reasoning == ReasoningMode.DELIBERATIVE:
            parts.append(
                "Think step-by-step. Break down complex problems. Show your reasoning process."
            )
        elif self.reasoning == ReasoningMode.REFLECTIVE:
            parts.append(
                "Before finalizing your response, review it critically. "
                "Consider: Is this accurate? Complete? Could it be misunderstood?"
            )

        # Oration instructions
        if self.oration == OrationMode.CONCISE:
            parts.append("Be brief. Use short sentences. Omit unnecessary details.")
        elif self.oration == OrationMode.CONVERSATIONAL:
            parts.append("Be natural and friendly. Use a conversational tone.")
        elif self.oration == OrationMode.ELABORATE:
            parts.append(
                "Provide thorough explanations. Cover edge cases. Be comprehensive."
            )
        elif self.oration == OrationMode.SOCRATIC:
            parts.append(
                "Ask clarifying questions. Guide the user to understanding rather than just giving answers."
            )
        elif self.oration == OrationMode.FORMAL:
            parts.append(
                "Maintain a professional tone. Use structured formatting. Be precise."
            )

        # Supervision instructions
        if self.supervision == SupervisionMode.AUTONOMOUS:
            parts.append("Work independently. Make decisions without seeking approval.")
        elif self.supervision == SupervisionMode.COLLABORATIVE:
            parts.append(
                "Check in with the user before major decisions. Seek clarification when uncertain."
            )
        elif self.supervision == SupervisionMode.DELEGATING:
            parts.append(
                "Use available skills/tools to accomplish tasks. Delegate specialized work."
            )
        elif self.supervision == SupervisionMode.ORCHESTRATING:
            parts.append(
                "Plan the work, delegate to appropriate skills, monitor progress, "
                "and synthesize results. You are the coordinator."
            )

        # Modifiers
        if self.caution > 0.7:
            parts.append(
                "Be cautious. Double-check facts. Acknowledge uncertainty explicitly."
            )
        elif self.caution < 0.3:
            parts.append("Be confident and decisive. Don't hedge unnecessarily.")

        return "\n".join(f"- {p}" for p in parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoning": self.reasoning.value,
            "oration": self.oration.value,
            "supervision": self.supervision.value,
            "caution": self.caution,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CognitiveStyle":
        return cls(
            reasoning=ReasoningMode(data.get("reasoning", "deliberative")),
            oration=OrationMode(data.get("oration", "conversational")),
            supervision=SupervisionMode(data.get("supervision", "autonomous")),
            caution=data.get("caution", 0.5),
        )


class CognitivePresets:
    """Pre-built cognitive styles for common agent patterns."""

    @staticmethod
    def reasoning_agent() -> CognitiveStyle:
        """Deep thinker - deliberate, thorough, self-critical."""
        return CognitiveStyle(
            reasoning=ReasoningMode.REFLECTIVE,
            oration=OrationMode.ELABORATE,
            supervision=SupervisionMode.AUTONOMOUS,
            caution=0.7,
        )

    @staticmethod
    def orator() -> CognitiveStyle:
        """Eloquent communicator - articulate, engaging, polished."""
        return CognitiveStyle(
            reasoning=ReasoningMode.DELIBERATIVE,
            oration=OrationMode.ELABORATE,
            supervision=SupervisionMode.AUTONOMOUS,
            caution=0.4,
        )

    @staticmethod
    def supervisor() -> CognitiveStyle:
        """Team coordinator - plans, delegates, synthesizes."""
        return CognitiveStyle(
            reasoning=ReasoningMode.REFLECTIVE,
            oration=OrationMode.FORMAL,
            supervision=SupervisionMode.ORCHESTRATING,
            caution=0.6,
        )

    @staticmethod
    def assistant() -> CognitiveStyle:
        """Helpful assistant - quick, friendly, collaborative."""
        return CognitiveStyle(
            reasoning=ReasoningMode.REACTIVE,
            oration=OrationMode.CONVERSATIONAL,
            supervision=SupervisionMode.COLLABORATIVE,
        )

    @staticmethod
    def analyst() -> CognitiveStyle:
        """Data analyst - precise, structured, cautious."""
        return CognitiveStyle(
            reasoning=ReasoningMode.DELIBERATIVE,
            oration=OrationMode.FORMAL,
            supervision=SupervisionMode.AUTONOMOUS,
            caution=0.8,
        )

    @staticmethod
    def creative() -> CognitiveStyle:
        """Creative agent - imaginative, exploratory, bold."""
        return CognitiveStyle(
            reasoning=ReasoningMode.REACTIVE,
            oration=OrationMode.ELABORATE,
            supervision=SupervisionMode.AUTONOMOUS,
            caution=0.2,
        )


__all__ = [
    "ReasoningMode",
    "OrationMode",
    "SupervisionMode",
    "CognitiveStyle",
    "CognitivePresets",
]
