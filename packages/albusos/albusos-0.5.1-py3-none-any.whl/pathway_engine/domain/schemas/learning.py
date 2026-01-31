"""Learning Configuration - Fundamental learning behavior specification.

These types define HOW pathways and state machines learn.
They are PRIMITIVES, not just validation schemas.

## Why This Is In pathway_engine

A StateMachine with `learning: LearningConfig` can:
- Update transition weights based on rewards
- Explore vs exploit via epsilon-greedy
- Decay learning rate over time

Without LearningConfig, a StateMachine exists but cannot learn.
LearningConfig is FUNDAMENTAL to learning behavior.

## Usage

```python
from pathway_engine.domain.schemas.learning import LearningConfig, RewardConfig

# In a StateMachine
sm = StateMachine(
    id="my_agent",
    learning=LearningConfig(
        enabled=True,
        rate=0.1,
        exploration=0.1,
        reward=RewardConfig(on_success=1.0, on_failure=-0.5)
    )
)

# In a Pathway
pathway = Pathway(
    id="my_pathway",
    learning=LearningConfig(enabled=True, rate=0.05)
)
```

## Naming Convention

We use SHORT, INTUITIVE names:
- `rate` (not `learning_rate` or `plasticity`)
- `exploration` (not `exploration_rate`)
- `min_delta` (not `require_min_reward_delta`)
- `on_success` (not `w_completed`)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# DECLARATIVE REWARD COMPONENTS
# =============================================================================


class RewardComponent(BaseModel):
    """A single signal contribution to the reward.

    Example:
    ```json
    { "signal": "evaluate.score", "weight": 0.3, "default": 0.5 }
    ```

    Signals can be:
    - Built-in: "success", "failure", "tool_failures", "verify_failures"
    - Node outputs: "node_id.field" (e.g., "evaluate.score")
    - Context: "context.field" (e.g., "context.user_rating")
    """

    model_config = ConfigDict(extra="forbid")

    signal: str = Field(
        description="Signal path (e.g., 'success', 'evaluate.score', 'tool_failures')"
    )
    weight: float = Field(
        default=1.0, description="Contribution weight (negative for penalties)"
    )
    default: float = Field(
        default=0.0, description="Default value if signal unavailable"
    )
    cap: float | None = Field(
        default=None, description="Max absolute value before weighting"
    )
    transform: Literal["identity", "abs", "neg", "bool", "inv"] = Field(
        default="identity",
        description="Transform to apply: identity, abs, neg, bool (0/1), inv (1-x)",
    )


class RewardShaping(BaseModel):
    """Interim reward bonus triggered by specific events.

    Reward shaping helps guide learning by providing intermediate signals.

    Example:
    ```json
    { "on": "tool_success", "bonus": 0.05 }
    ```

    Events can be:
    - "tool_success": A tool call succeeded
    - "tool_failure": A tool call failed
    - "verify_pass": A verifier passed
    - "verify_fail": A verifier failed
    - "step_complete": Any step completed
    - Custom: "custom.event_name"
    """

    model_config = ConfigDict(extra="forbid")

    on: str = Field(description="Event that triggers this bonus")
    bonus: float = Field(description="Reward bonus to add when event occurs")
    when: str | None = Field(default=None, description="Optional condition expression")


# =============================================================================
# REWARD CONFIGURATION
# =============================================================================


class RewardConfig(BaseModel):
    """Configuration for computing rewards from execution.

    Rewards drive learning - they tell the system what "good" looks like.

    ## Simple Mode
    ```json
    {
      "reward": {
        "on_success": 1.0,
        "on_failure": -1.0,
        "on_tool_error": -0.2
      }
    }
    ```

    ## Declarative Mode
    ```json
    {
      "reward": {
        "components": [
          { "signal": "success", "weight": 0.5 },
          { "signal": "evaluate.score", "weight": 0.3, "default": 0.5 },
          { "signal": "tool_failures", "weight": -0.1, "cap": 3 }
        ],
        "shaping": [
          { "on": "tool_success", "bonus": 0.05 }
        ]
      }
    }
    ```

    When `components` is provided, declarative mode is used.
    Otherwise, falls back to simple mode with fixed weights.
    """

    model_config = ConfigDict(extra="allow")

    # -------------------------------------------------------------------------
    # DECLARATIVE MODE
    # -------------------------------------------------------------------------

    components: list[RewardComponent] | None = Field(
        default=None,
        description="Declarative reward components (if set, uses expression mode)",
    )
    shaping: list[RewardShaping] | None = Field(
        default=None,
        description="Interim reward bonuses triggered by events",
    )

    # -------------------------------------------------------------------------
    # SIMPLE MODE
    # -------------------------------------------------------------------------

    on_success: float = Field(
        default=1.0, description="Reward for successful completion"
    )
    on_failure: float = Field(default=-1.0, description="Penalty for failure")
    on_tool_error: float = Field(default=-0.2, description="Penalty per tool error")
    on_verify_fail: float = Field(
        default=-0.3, description="Penalty per verification failure"
    )

    max_tool_errors: int = Field(default=5, description="Max tool errors to count")
    max_verify_fails: int = Field(default=5, description="Max verify fails to count")

    min_score: float = Field(default=-1.0, description="Minimum reward score")
    max_score: float = Field(default=1.0, description="Maximum reward score")

    discount: float = Field(default=0.99, description="Discount for delayed rewards")

    success_signals: list[str] = Field(
        default_factory=lambda: ["success", "completed"],
        description="Signal names indicating success",
    )
    failure_signals: list[str] = Field(
        default_factory=lambda: ["error", "failed"],
        description="Signal names indicating failure",
    )

    @property
    def is_declarative(self) -> bool:
        """Check if using declarative mode (components defined)."""
        return self.components is not None and len(self.components) > 0


# =============================================================================
# LEARNING CONFIGURATION
# =============================================================================


class LearningConfig(BaseModel):
    """Configuration for learning behavior.

    Controls whether and how a pathway/state machine learns from execution.

    Example:
    ```json
    {
      "learning": {
        "enabled": true,
        "rate": 0.1,
        "exploration": 0.1,
        "min_delta": 0.05,
        "reward": { "on_success": 1.0, "on_failure": -0.5 }
      }
    }
    ```

    ## Parameters
    - `rate`: How fast weights change (0.01=slow, 0.1=fast)
    - `exploration`: Probability of random exploration (epsilon-greedy)
    - `min_delta`: Minimum reward change to trigger update
    - `decay`: Learning rate decay over time
    """

    model_config = ConfigDict(extra="allow")

    enabled: bool = Field(default=True, description="Whether learning is active")

    rate: float = Field(default=0.1, ge=0.001, le=0.5, description="Learning rate")
    exploration: float = Field(
        default=0.1, ge=0.0, le=0.5, description="Exploration probability"
    )
    decay: float = Field(
        default=0.01, ge=0.0, le=0.1, description="Learning rate decay"
    )
    min_delta: float = Field(
        default=0.1, ge=0.0, description="Minimum reward change to trigger update"
    )

    min_weight: float = Field(default=0.01, ge=0.0, description="Minimum weight value")
    max_weight: float = Field(default=0.99, le=1.0, description="Maximum weight value")

    update_on_success: bool = Field(
        default=True, description="Update weights on successful execution"
    )
    update_on_failure: bool = Field(
        default=True, description="Update weights on failed execution"
    )

    reward: RewardConfig = Field(
        default_factory=RewardConfig, description="Reward computation config"
    )

    persist_every: int = Field(
        default=5, ge=1, description="Persist weights every N updates"
    )

    strategy: str = Field(
        default="hebbian",
        description="Learning strategy: 'hebbian', 'reward_modulated', 'none'",
    )


__all__ = [
    "RewardComponent",
    "RewardShaping",
    "RewardConfig",
    "LearningConfig",
]
