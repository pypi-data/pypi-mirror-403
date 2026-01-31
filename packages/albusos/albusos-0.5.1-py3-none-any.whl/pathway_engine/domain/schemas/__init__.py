"""pathway_engine.schemas - JSON-serializable schemas.

This module provides schemas for:
- Learning configuration (LearningConfig, RewardConfig)
- Learning models (RewardV1, PolicyWeightsV1, ExperienceRecordV1)
- Expressions (ExpressionV1)
- Signatures (PathwaySignature, PortSpec)
"""

from __future__ import annotations

# Learning configuration
from pathway_engine.domain.schemas.learning import (
    LearningConfig,
    RewardComponent,
    RewardConfig,
    RewardShaping,
)

# Learning runtime models
from pathway_engine.domain.schemas.learning_models import (
    ExperienceRecordV1,
    NodePolicyV1,
    PolicyUpdateResultV1,
    PolicyWeightsV1,
    RewardV1,
)

# Expressions
from shared_types.schemas.expression import (
    ExpressionV1,
    ExpressionValidationResult,
)

# Signatures
from pathway_engine.domain.schemas.signature import (
    PathwaySignature,
    PortSpec,
)

# Context
from pathway_engine.domain.schemas.context import ContextBudgetV1

# Context receipt from models (re-export)
from pathway_engine.domain.models.context import ContextReceiptV1

__all__ = [
    # Learning configuration
    "LearningConfig",
    "RewardConfig",
    "RewardComponent",
    "RewardShaping",
    # Learning models
    "RewardV1",
    "PolicyWeightsV1",
    "ExperienceRecordV1",
    "NodePolicyV1",
    "PolicyUpdateResultV1",
    # Expressions
    "ExpressionV1",
    "ExpressionValidationResult",
    # Signatures
    "PathwaySignature",
    "PortSpec",
    # Context
    "ContextBudgetV1",
    "ContextReceiptV1",
]
