"""Learning models - runtime data structures for policy learning.

This module contains RUNTIME models for learning:
- RewardV1: Computed reward output
- PolicyWeightsV1: Mutable policy state (weights + overrides)
- ExperienceRecordV1: Recorded experience for learning
- PolicyUpdateResultV1: Result of a policy update

## Architecture

Configuration schemas (LearningConfig, RewardConfig) are PRIMITIVES in pathway_engine.config.
They define fundamental learning behavior, not just validation.

Runtime models (state, computed outputs) live here in pathway_engine.learning:
- RewardV1, PolicyWeightsV1, ExperienceRecordV1, PolicyUpdateResultV1

Philosophy:
- Keep it simple: we're doing contextual bandits, not deep RL
- Keep it auditable: every weight change is traceable
- Keep it bounded: weights are normalized, updates are clamped
- **Plasticity:** Supports "Bias Correction" via prompt overrides

The learning loop:
1. Observe state (context)
2. Select action (weighted by policy + overrides)
3. Receive reward (from supervision)
4. Update weights (gradient-free, exponential moving average)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# RE-EXPORT CONFIG SCHEMAS FROM pathway_engine.config (canonical source)
# =============================================================================
from pathway_engine.domain.schemas.learning import LearningConfig, RewardConfig

# =============================================================================
# RUNTIME: COMPUTED REWARD OUTPUT
# =============================================================================


class RewardV1(BaseModel):
    """A computed reward for a pathway execution.

    This is a RUNTIME OUTPUT - the result of evaluating a RewardConfig
    against actual execution outcomes.
    """

    model_config = ConfigDict(extra="allow")

    version: Literal["v1"] = "v1"

    reward_id: str
    pathway_id: str
    run_id: str

    score: float = Field(ge=-1.0, le=1.0)
    breakdown: dict[str, float] = Field(default_factory=dict)

    failed_node_id: str | None = None
    error_signature_id: str | None = None


# =============================================================================
# RUNTIME: POLICY WEIGHTS STATE
# =============================================================================


class NodePolicyV1(BaseModel):
    """Policy for a specific node in a pathway.

    This allows the agent to learn specific behaviors for specific nodes,
    rather than just global tool weights.
    """

    model_config = ConfigDict(extra="allow")

    node_id: str

    # Prompt injection (Bias Correction)
    prompt_override: str | None = None
    prompt_injection: str | None = None  # Appended to system prompt

    # Tool preferences for this node
    preferred_tools: dict[str, float] = Field(default_factory=dict)

    # Action preferences for this node
    preferred_actions: dict[str, float] = Field(default_factory=dict)

    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PolicyWeightsV1(BaseModel):
    """Learned weights for action/tool selection.

    This is RUNTIME STATE - mutable weights that change during learning.

    These weights influence which tools get selected by the planner.
    They're updated based on reward signals from execution.

    Structure:
    - tool_weights: {tool_name: weight} - higher = more likely to select
    - action_weights: {action: weight} - respond/use_tools/call_tools
    - context_weights: {context_key: weight} - situational adjustments
    - node_policies: {node_id: NodePolicyV1} - node-specific overrides

    All weights are in [0, 1] and normalized when used.
    """

    model_config = ConfigDict(extra="allow")

    version: Literal["v1"] = "v1"

    # Global weights
    tool_weights: dict[str, float] = Field(default_factory=dict)
    action_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "respond": 0.5,
            "use_tools": 0.5,
            "call_tools": 0.5,
        }
    )
    context_weights: dict[str, float] = Field(default_factory=dict)

    # Node-specific policies (Plasticity)
    node_policies: dict[str, NodePolicyV1] = Field(default_factory=dict)

    total_updates: int = 0
    last_updated: datetime | None = None

    def get_tool_weight(
        self, tool_name: str, node_id: str | None = None, default: float = 0.5
    ) -> float:
        """Get weight for a tool, checking node override first."""
        if node_id and node_id in self.node_policies:
            node_policy = self.node_policies[node_id]
            if tool_name in node_policy.preferred_tools:
                return float(node_policy.preferred_tools[tool_name])
        return float(self.tool_weights.get(tool_name, default))

    def get_action_weight(
        self, action: str, node_id: str | None = None, default: float = 0.5
    ) -> float:
        """Get weight for an action, checking node override first."""
        if node_id and node_id in self.node_policies:
            node_policy = self.node_policies[node_id]
            if action in node_policy.preferred_actions:
                return float(node_policy.preferred_actions[action])
        return float(self.action_weights.get(action, default))

    def get_prompt_injection(self, node_id: str) -> str | None:
        """Get prompt injection for a specific node."""
        if node_id in self.node_policies:
            return self.node_policies[node_id].prompt_injection
        return None

    def normalize_tool_weights(
        self, tool_names: list[str], node_id: str | None = None
    ) -> dict[str, float]:
        """Normalize weights for a set of tools to sum to 1."""
        weights = {t: self.get_tool_weight(t, node_id) for t in tool_names}
        total = sum(weights.values())
        if total <= 0:
            return {t: 1.0 / len(tool_names) for t in tool_names}
        return {t: w / total for t, w in weights.items()}


# =============================================================================
# RUNTIME: EXPERIENCE RECORD STATE
# =============================================================================


class ExperienceRecordV1(BaseModel):
    """A single learning example: what happened and how it went.

    This is RUNTIME STATE - recorded experience for replay-based learning.

    This captures:
    - The context (what was the situation)
    - The action (what did we do)
    - The reward (how well did it go)
    - Metadata for debugging/auditing
    """

    model_config = ConfigDict(extra="allow")

    version: Literal["v1"] = "v1"

    experience_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    context_hash: str
    context_summary: str = ""

    node_id: str | None = None  # Which node generated this experience

    action: str  # "respond" | "use_tools" | "call_tools"
    tool_names: list[str] = Field(default_factory=list)

    reward: float = Field(ge=-1.0, le=1.0)
    reward_breakdown: dict[str, float] = Field(default_factory=dict)

    success: bool = True
    error_type: str | None = None

    run_id: str | None = None
    pathway_id: str | None = None
    session_id: str | None = None


# =============================================================================
# RUNTIME: POLICY UPDATE RESULT OUTPUT
# =============================================================================


class PolicyUpdateResultV1(BaseModel):
    """Result of a policy weight update.

    This is a RUNTIME OUTPUT - captures what changed and why, for auditability.
    """

    model_config = ConfigDict(extra="allow")

    version: Literal["v1"] = "v1"

    updated_tools: dict[str, tuple[float, float]] = Field(
        default_factory=dict
    )  # {tool: (old, new)}
    updated_actions: dict[str, tuple[float, float]] = Field(default_factory=dict)

    # Tracks if a prompt injection was created/updated
    prompt_injection_update: dict[str, str] | None = None  # {node_id: "new_prompt"}

    experience_id: str
    reward: float
    learning_rate_used: float

    total_updates: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    # Runtime models (defined here)
    "RewardV1",
    "NodePolicyV1",
    "PolicyWeightsV1",
    "ExperienceRecordV1",
    "PolicyUpdateResultV1",
    # Config schemas from pathway_engine.config (canonical source)
    "RewardConfig",
    "LearningConfig",
]
