"""persistence.workspace - Workspace models and environment.

This package contains workspace-related models:
- Environment configuration
- Manifest parsing
- Workspace models
"""

from __future__ import annotations

from persistence.domain.workspace.environment import (
    BaseEnvironment,
    EnvironmentCapability,
    EnvironmentConfig,
    EnvironmentProtocol,
    ObservationSpaceProtocol,
    ActionSpaceProtocol,
    EventStreamProtocol,
    FeedbackChannelProtocol,
)
from persistence.domain.workspace.manifest import (
    ProjectManifestDocV1,
    ProjectManifestSpecV1,
    ProjectPointersV1,
    WorkspaceReality,
    safe_parse_project_manifest_doc,
)

__all__ = [
    # Environment
    "BaseEnvironment",
    "EnvironmentCapability",
    "EnvironmentConfig",
    "EnvironmentProtocol",
    "ObservationSpaceProtocol",
    "ActionSpaceProtocol",
    "EventStreamProtocol",
    "FeedbackChannelProtocol",
    # Manifest
    "ProjectManifestDocV1",
    "ProjectManifestSpecV1",
    "ProjectPointersV1",
    "WorkspaceReality",
    "safe_parse_project_manifest_doc",
]
