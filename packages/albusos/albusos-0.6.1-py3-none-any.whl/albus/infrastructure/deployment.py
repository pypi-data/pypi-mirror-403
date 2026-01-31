"""Deployment configuration - Customer YAML config for packs and MCP servers.

This module provides the deployment-time configuration layer:
- What packs to deploy (business logic selection)
- What MCP servers to connect (external integrations)
- Event bindings (external sources → internal webhook topics)

IMPORTANT SEPARATION:
- Pack manifests declare triggers: "topic X → pathway Y" (library-time)
- DeploymentConfig declares bindings: "source A → topic X" (deployment-time)

Bindings do NOT redefine pack triggers. They only route external events
into the internal topic namespace that packs already listen to.

Example flow:
    Gmail inbox → binding → topic "maintenance-requests" → pack trigger → pathway

Usage:
    # Load from YAML file
    config = DeploymentConfig.from_yaml("albus.yaml")
    
    # Boot sequence uses this to:
    # 1. Connect MCP servers
    # 2. Deploy selected packs (which register their triggers on topics)
    # 3. Set up bindings (external sources → topics)
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Environment variable substitution pattern: ${VAR} or ${VAR:-default}
_ENV_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::-([^}]*))?\}")


def _substitute_env_vars(value: Any) -> Any:
    """Recursively substitute ${VAR} and ${VAR:-default} in strings.

    Examples:
        ${OPENAI_API_KEY} → value of OPENAI_API_KEY env var
        ${PORT:-8080} → value of PORT, or "8080" if not set
    """
    if isinstance(value, str):

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            env_value = os.getenv(var_name)
            if env_value is not None:
                return env_value
            if default is not None:
                return default
            # Return empty string if not set and no default
            logger.warning("Environment variable %s not set (no default)", var_name)
            return ""

        return _ENV_PATTERN.sub(replacer, value)

    elif isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]

    return value


# Supported MCP transports
_SUPPORTED_MCP_TRANSPORTS = {"stdio", "sse"}


@dataclass
class MCPServerSpec:
    """MCP server connection specification.

    Supported transports:
    - stdio: Launch a subprocess (command + args)
    - sse: Connect to HTTP SSE endpoint (url + headers)

    Environment variables in any string field are substituted at load time.
    """

    id: str  # Unique server identifier
    transport: str = "stdio"  # "stdio" or "sse"

    # For stdio transport
    command: str | None = None  # e.g., "npx", "python"
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)  # Additional env vars

    # For SSE transport
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)

    # Connection settings
    timeout_s: int = 30
    retry_attempts: int = 3

    def validate(self) -> list[str]:
        """Validate the spec, return list of errors."""
        errors = []

        if not self.id:
            errors.append("MCP server id is required")

        # Check transport is known
        if self.transport not in _SUPPORTED_MCP_TRANSPORTS:
            errors.append(
                f"Invalid transport '{self.transport}', must be one of: {sorted(_SUPPORTED_MCP_TRANSPORTS)}"
            )

        # Validate stdio requirements
        if self.transport == "stdio" and not self.command:
            errors.append(f"MCP server '{self.id}': stdio transport requires 'command'")

        # Validate SSE requirements
        if self.transport == "sse" and not self.url:
            errors.append(f"MCP server '{self.id}': sse transport requires 'url'")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict (for API/debugging)."""
        d = {
            "id": self.id,
            "transport": self.transport,
        }
        if self.command:
            d["command"] = self.command
        if self.args:
            d["args"] = self.args
        if self.url:
            d["url"] = self.url
        # Don't expose env/headers (may contain secrets)
        return d


@dataclass
class ModelRoutingConfig:
    """Model routing configuration - which models to use for which capabilities.

    This allows declarative control over model selection:
    - default_profile: Base battery pack ("local", "balanced", "premium", "starter")
    - routing: Fine-grained capability → model overrides

    Example YAML:
        models:
          default_profile: local
          routing:
            tool_calling: qwen2.5:7b
            code: qwen2.5-coder:7b
            reasoning: llama3.1:8b
            vision: gpt-4o  # cloud fallback
    """

    default_profile: str = "balanced"  # Battery pack base
    routing: dict[str, str] = field(default_factory=dict)  # capability → model overrides

    def get_model(self, capability: str) -> str | None:
        """Get model for capability, checking overrides first."""
        # Check explicit override
        if capability in self.routing:
            return self.routing[capability]

        # Check parent capability (e.g., "code.python" → "code")
        if "." in capability:
            parent = capability.rsplit(".", 1)[0]
            if parent in self.routing:
                return self.routing[parent]

        # Return None to fall back to battery pack
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "default_profile": self.default_profile,
            "routing": dict(self.routing),
        }


@dataclass
class WebhookBinding:
    """Maps an external event source to an internal webhook topic.

    IMPORTANT: Bindings only route source → topic.
    The pack trigger defines topic → pathway (that's not our job).

    Example:
        Binding: gmail.inbox → topic "support-requests"
        Pack trigger: topic "support-requests" → pathway "my_agent.support.v1"

    This separation keeps business logic in packs, routing in config.
    """

    source: str  # External source (e.g., "gmail.inbox_watch")
    topic: str  # Internal webhook topic (e.g., "maintenance-requests")
    filter: dict[str, Any] = field(default_factory=dict)  # Source-specific filters
    transform: dict[str, str] = field(default_factory=dict)  # Field mappings


@dataclass
class DeploymentConfig:
    """Customer deployment configuration.

    This is the single source of truth for what gets deployed at startup:
    - Which packs to activate
    - Which agents to deploy
    - Which MCP servers to connect
    - How external events route to internal topics

    Loaded from:
    - YAML file (recommended for all environments)
    """

    # Packs to deploy (by ID)
    packs: list[str] = field(default_factory=list)

    # Agents to deploy (by ID) - use ["*"] for all registered agents
    agents: list[str] = field(default_factory=list)

    # Schema version for this config format
    schema_version: int = 1

    # MCP server connections
    mcp_servers: list[MCPServerSpec] = field(default_factory=list)

    # Event bindings (source → topic routing)
    bindings: list[WebhookBinding] = field(default_factory=list)

    # Model routing configuration
    models: ModelRoutingConfig = field(default_factory=ModelRoutingConfig)

    # Source file (if loaded from YAML)
    _source_file: str | None = None

    @property
    def source(self) -> str:
        """Return where this config was loaded from: file path or 'none'."""
        return self._source_file or "none"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "DeploymentConfig":
        """Load configuration from YAML file.

        Supports environment variable substitution: ${VAR} or ${VAR:-default}

        Args:
            path: Path to albus.yaml file

        Returns:
            DeploymentConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        import yaml

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            raw = yaml.safe_load(f) or {}

        # Substitute environment variables
        data = _substitute_env_vars(raw)

        # Schema version (default v1)
        schema_version = int(data.get("schema_version", 1) or 1)

        # Parse packs - support "*" wildcard for auto-registration
        packs = data.get("packs", [])
        if isinstance(packs, str):
            packs = [p.strip() for p in packs.split(",") if p.strip()]

        # Packs are no longer supported - ignore pack config
        packs = []

        # Parse agents - support "*" wildcard for auto-registration
        agents = data.get("agents", [])
        if isinstance(agents, str):
            agents = [a.strip() for a in agents.split(",") if a.strip()]

        # Handle wildcard: ["*"] means "all available agents"
        # Note: We don't expand here, we let the server do it to avoid import issues
        if agents == "*":
            agents = ["*"]

        # Parse MCP servers
        mcp_servers = []
        for spec in data.get("mcp_servers", []):
            if isinstance(spec, dict):
                mcp_servers.append(
                    MCPServerSpec(
                        id=spec.get("id", ""),
                        transport=spec.get("transport", "stdio"),
                        command=spec.get("command"),
                        args=spec.get("args", []),
                        env=spec.get("env", {}),
                        url=spec.get("url"),
                        headers=spec.get("headers", {}),
                        timeout_s=spec.get("timeout_s", 30),
                        retry_attempts=spec.get("retry_attempts", 3),
                    )
                )

        # Parse model routing config
        models_data = data.get("models", {})
        if models_data is None:
            models_data = {}
        models = ModelRoutingConfig(
            default_profile=str(models_data.get("default_profile", "balanced")).strip(),
            routing=dict(models_data.get("routing", {})),
        )

        # Parse bindings
        bindings = []
        bindings_data = data.get("bindings", {})
        if bindings_data is None:
            bindings_data = {}
        if not isinstance(bindings_data, dict):
            logger.warning(
                "Invalid bindings section (expected mapping), ignoring: %r",
                bindings_data,
            )
            bindings_data = {}

        # Handle nested binding format: bindings.gmail.inbox_watch → topic
        for source_prefix, source_bindings in bindings_data.items():
            if isinstance(source_bindings, dict):
                for event_name, binding_spec in source_bindings.items():
                    if isinstance(binding_spec, str):
                        # Simple format: topic name only
                        bindings.append(
                            WebhookBinding(
                                source=f"{source_prefix}.{event_name}",
                                topic=binding_spec,
                            )
                        )
                    elif isinstance(binding_spec, dict):
                        # Full format with filter/transform
                        bindings.append(
                            WebhookBinding(
                                source=f"{source_prefix}.{event_name}",
                                topic=binding_spec.get("topic", event_name),
                                filter=binding_spec.get("filter", {}),
                                transform=binding_spec.get("transform", {}),
                            )
                        )

        config = cls(
            packs=packs,
            agents=agents,
            schema_version=schema_version,
            mcp_servers=mcp_servers,
            bindings=bindings,
            models=models,
        )
        config._source_file = str(path)

        return config

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "DeploymentConfig":
        """Load deployment config from YAML (recommended).

        Args:
            config_path: Optional path to YAML config. If None, checks:
                1. ALBUS_CONFIG env var
                2. ./albus.yaml
                3. ./config/albus.yaml

        Returns:
            DeploymentConfig instance. If no config file is found, returns an empty config.
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                logger.info("Loading deployment config from: %s", path)
                return cls.from_yaml(path)
            else:
                logger.warning("Config file not found: %s, using empty config", path)
                return cls()

        # Check standard locations
        candidates = [
            os.getenv("ALBUS_CONFIG"),
            "albus.yaml",
            "config/albus.yaml",
        ]

        for candidate in candidates:
            if candidate and Path(candidate).exists():
                logger.info("Loading deployment config from: %s", candidate)
                return cls.from_yaml(candidate)

        logger.info("No deployment config file found, using empty config")
        return cls()

    def validate(self) -> list[str]:
        """Validate the configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.schema_version != 1:
            errors.append(
                f"Unsupported deployment schema_version: {self.schema_version} (expected 1)"
            )

        # Packs are no longer supported - skip validation

        # Validate MCP servers
        for mcp in self.mcp_servers:
            errors.extend(mcp.validate())

        # Check for duplicate MCP IDs
        mcp_ids = [m.id for m in self.mcp_servers]
        if len(mcp_ids) != len(set(mcp_ids)):
            errors.append("Duplicate MCP server IDs detected")

        # Validate bindings (shape + required fields)
        for b in self.bindings:
            if not b.source:
                errors.append("Binding source is required")
            if not b.topic:
                errors.append(f"Binding '{b.source}': topic is required")
            if not isinstance(b.filter, dict):
                errors.append(f"Binding '{b.source}': filter must be an object")
            if not isinstance(b.transform, dict):
                errors.append(f"Binding '{b.source}': transform must be an object")
            else:
                bad = [k for k, v in b.transform.items() if not isinstance(v, str)]
                if bad:
                    errors.append(
                        f"Binding '{b.source}': transform values must be strings (bad keys: {bad})"
                    )

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict (for API/debugging).

        Returns effective config after env substitution + defaults,
        plus 'source' field indicating where it was loaded from.
        """
        return {
            "source": self.source,  # "env" or file path
            "schema_version": self.schema_version,
            "packs": self.packs,
            "agents": self.agents,
            "mcp_servers": [m.to_dict() for m in self.mcp_servers],
            "bindings": [
                {
                    "source": b.source,
                    "topic": b.topic,
                    "filter": b.filter,
                    "transform": b.transform,
                }
                for b in self.bindings
            ],
            "models": self.models.to_dict(),
        }


__all__ = [
    "DeploymentConfig",
    "MCPServerSpec",
    "ModelRoutingConfig",
    "WebhookBinding",
]
