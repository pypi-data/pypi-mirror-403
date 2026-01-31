"""Centralized configuration management for Albus.

Loads and validates all environment variables with clear error messages.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse boolean environment variable."""
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int | None = None) -> int | None:
    """Parse integer environment variable."""
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v.strip())
    except ValueError:
        return default


@dataclass
class ServerConfig:
    """Server configuration."""

    host: str = "127.0.0.1"
    port: int = 8080
    debug: bool = False
    log_level: str = "INFO"
    log_style: str = "plain"
    http_trace: bool = False
    access_log: bool = False


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    ollama_host: str | None = None
    battery_pack: str = "balanced"
    model_profile: str = "cloud"
    prefer_local: bool = False
    model_logging: bool = False
    openai_timeout_s: int = 60
    anthropic_timeout_s: int = 60


@dataclass
class WorkspaceConfig:
    """Workspace and tool configuration."""

    workspace_root: str = "data/studio"
    code_sandbox_mode: str = "docker"
    code_sandbox_docker_image: str = "python:3.11-slim"


@dataclass
class PersistenceConfig:
    """Persistence configuration."""

    database_url: str | None = None


@dataclass
class MCPConfig:
    """MCP (Model Context Protocol) configuration."""

    servers: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AlbusConfig:
    """Complete Albus configuration.

    Loads from environment variables with validation.
    """

    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)

    env: str = "development"

    @classmethod
    def from_env(cls, *, validate_required: bool = True) -> AlbusConfig:
        """Load configuration from environment variables.

        Args:
            validate_required: If True, validate that required API keys are present

        Returns:
            Configured AlbusConfig instance

        Raises:
            ValueError: If validation fails and validate_required is True
        """
        # Load .env files
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent.parent.parent
        env_file = project_root / ".env"
        env_local = project_root / ".env.local"

        if env_file.exists():
            load_dotenv(env_file)
        if env_local.exists():
            load_dotenv(env_local, override=True)

        # Server config
        server = ServerConfig(
            host=os.getenv("ALBUS_HOST", "127.0.0.1"),
            port=_env_int("ALBUS_PORT", 8080) or 8080,
            debug=_env_bool("ALBUS_DEBUG", False),
            log_level=os.getenv("ALBUS_LOG_LEVEL", "INFO"),
            log_style=os.getenv("ALBUS_LOG_STYLE", "plain"),
            http_trace=_env_bool("ALBUS_HTTP_TRACE", False),
            access_log=_env_bool("ALBUS_ACCESS_LOG", False),
        )

        # LLM config
        llm = LLMConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            ollama_host=os.getenv("OLLAMA_HOST"),
            battery_pack=os.getenv("AGENT_STDLIB_BATTERY_PACK", "balanced"),
            model_profile=os.getenv("AGENT_STDLIB_MODEL_PROFILE", "cloud"),
            prefer_local=_env_bool("AGENT_STDLIB_PREFER_LOCAL", False),
            model_logging=_env_bool("AGENT_STDLIB_MODEL_LOGGING", False),
            openai_timeout_s=_env_int("AGENT_STDLIB_OPENAI_TIMEOUT_S", 60) or 60,
            anthropic_timeout_s=_env_int("AGENT_STDLIB_ANTHROPIC_TIMEOUT_S", 60) or 60,
        )

        # Workspace config
        workspace = WorkspaceConfig(
            workspace_root=os.getenv("AGENT_STDLIB_WORKSPACE_ROOT", "data/studio"),
            code_sandbox_mode=os.getenv("AGENT_STDLIB_CODE_SANDBOX_MODE", "docker"),
            code_sandbox_docker_image=os.getenv(
                "AGENT_STDLIB_CODE_SANDBOX_DOCKER_IMAGE", "python:3.11-slim"
            ),
        )

        # Persistence config
        persistence = PersistenceConfig(
            database_url=os.getenv("DATABASE_URL"),
        )

        # MCP config
        #
        # MCP server configuration is owned by DeploymentConfig (albus.yaml).
        # This config object keeps an explicit MCP section for clarity, but does not
        # read MCP server specs from environment variables.
        mcp = MCPConfig(servers=[])

        # Environment
        env = os.getenv("ALBUS_ENV", "development").lower()

        config = cls(
            server=server,
            llm=llm,
            workspace=workspace,
            persistence=persistence,
            mcp=mcp,
            env=env,
        )

        if validate_required:
            config.validate()

        return config

    def validate(self) -> None:
        """Validate configuration.

        Checks that at least one LLM provider is configured.

        Raises:
            ValueError: If validation fails
        """
        errors: list[str] = []

        # Check for at least one LLM provider
        has_llm = bool(
            self.llm.openai_api_key
            or self.llm.anthropic_api_key
            or self.llm.google_api_key
            or self.llm.ollama_host
        )

        if not has_llm:
            errors.append(
                "No LLM provider configured. Set at least one of: "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OLLAMA_HOST"
            )

        if errors:
            raise ValueError(
                "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dict (for API responses, excluding secrets)."""
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "debug": self.server.debug,
                "log_level": self.server.log_level,
            },
            "llm": {
                "battery_pack": self.llm.battery_pack,
                "model_profile": self.llm.model_profile,
                "prefer_local": self.llm.prefer_local,
                "providers_configured": {
                    "openai": bool(self.llm.openai_api_key),
                    "anthropic": bool(self.llm.anthropic_api_key),
                    "google": bool(self.llm.google_api_key),
                    "ollama": bool(self.llm.ollama_host),
                },
            },
            "workspace": {
                "workspace_root": self.workspace.workspace_root,
                "code_sandbox_mode": self.workspace.code_sandbox_mode,
            },
            "persistence": {
                "database_configured": bool(self.persistence.database_url),
            },
            "mcp": {
                "servers_configured": len(self.mcp.servers),
            },
            "env": self.env,
        }


# Global config instance (lazy-loaded)
_config: AlbusConfig | None = None


def get_config() -> AlbusConfig:
    """Get global config instance (lazy-loaded)."""
    global _config
    if _config is None:
        _config = AlbusConfig.from_env(validate_required=False)
    return _config


__all__ = [
    "AlbusConfig",
    "ServerConfig",
    "LLMConfig",
    "WorkspaceConfig",
    "PersistenceConfig",
    "MCPConfig",
    "get_config",
]
