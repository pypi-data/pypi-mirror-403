"""Default configuration values for optix-mcp-server."""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    """Logging verbosity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    WARN = "WARNING"
    ERROR = "ERROR"

    @classmethod
    def _missing_(cls, value):
        """Handle WARN as alias for WARNING."""
        if isinstance(value, str) and value.upper() == "WARN":
            return cls.WARNING
        return None


class Transport(Enum):
    """MCP transport types."""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


class HealthStatus(Enum):
    """Server health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class APIKeyConfig:
    """API key configuration for AI providers.

    Attributes:
        openrouter_api_key: OpenRouter API key
        openai_api_key: OpenAI API key
        azure_openai_endpoint: Azure OpenAI endpoint URL
        azure_openai_api_key: Azure OpenAI API key
    """
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    llm_provider: Optional[str] = None

    @classmethod
    def from_env(cls) -> "APIKeyConfig":
        """Create API key configuration from environment variables."""
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            llm_provider=os.getenv("OPTIX_LLM_PROVIDER"),
        )

    def validate_key(self, provider: str) -> bool:
        """Validate that an API key is set and not empty.

        Args:
            provider: Provider name (openrouter, openai, azure)

        Returns:
            True if the key is set and valid format
        """
        key_map = {
            "openrouter": self.openrouter_api_key,
            "openai": self.openai_api_key,
            "azure": self.azure_openai_api_key,
        }
        key = key_map.get(provider.lower())
        return key is not None and len(key) > 0

    def get_configured_providers(self) -> list[str]:
        """Get list of providers with configured API keys."""
        providers = []
        if self.openrouter_api_key:
            providers.append("openrouter")
        if self.openai_api_key:
            providers.append("openai")
        if self.azure_openai_api_key and self.azure_openai_endpoint:
            providers.append("azure")
        return providers

    def get_llm_provider_config(self) -> Optional["LLMProviderConfig"]:
        """Get LLM provider configuration if available.

        Returns:
            LLMProviderConfig if provider and key are configured, None otherwise
        """
        from config.llm import LLMProviderConfig

        if not self.llm_provider:
            return None

        provider = self.llm_provider.lower()
        key_map = {
            "openai": self.openai_api_key,
        }
        api_key = key_map.get(provider)
        if not api_key:
            return None

        return LLMProviderConfig(provider=provider, api_key=api_key)


@dataclass
class ServerConfiguration:
    """MCP server runtime configuration.

    Attributes:
        server_name: Name of the MCP server instance
        log_level: Logging verbosity level
        transport: Transport type for MCP communication
        enabled_tools: List of enabled tool names (empty = all enabled)
        disabled_tools: List of disabled tool names
        api_keys: API key configuration for AI providers
        expert_analysis_enabled: Enable expert analysis of audit findings
        expert_analysis_timeout: Timeout for expert analysis in seconds
        expert_analysis_max_findings: Maximum findings to analyze
    """
    server_name: str = "optix-mcp-server"
    log_level: LogLevel = LogLevel.INFO
    transport: Transport = Transport.STDIO
    enabled_tools: list[str] = field(default_factory=list)
    disabled_tools: list[str] = field(default_factory=list)
    api_keys: Optional[APIKeyConfig] = None
    expert_analysis_enabled: bool = False
    expert_analysis_timeout: int = 30
    expert_analysis_max_findings: int = 50

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        # Validate server_name
        if not self.server_name:
            raise ValueError("server_name must be non-empty")
        if not re.match(r"^[a-zA-Z0-9-]+$", self.server_name):
            raise ValueError(
                "server_name must be alphanumeric with hyphens allowed"
            )

        # Validate log_level
        if not isinstance(self.log_level, LogLevel):
            raise ValueError(
                f"log_level must be one of: {', '.join(l.value for l in LogLevel)}"
            )

        # Validate transport
        if not isinstance(self.transport, Transport):
            raise ValueError(
                f"transport must be one of: {', '.join(t.value for t in Transport)}"
            )

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled based on configuration.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is enabled
        """
        # If disabled_tools is set, check if tool is not in it
        if self.disabled_tools and tool_name in self.disabled_tools:
            return False

        # If enabled_tools is set, check if tool is in it
        if self.enabled_tools:
            return tool_name in self.enabled_tools

        # Default: all tools enabled
        return True

    def get_disabled_tools_list(self) -> list[str]:
        """Get list of disabled tools.

        Returns:
            List of disabled tool names
        """
        return self.disabled_tools.copy()

    @classmethod
    def from_env(cls) -> "ServerConfiguration":
        """Create configuration from environment variables.

        Environment variables:
            SERVER_NAME: Server name (default: optix-mcp-server)
            LOG_LEVEL: Logging level (default: INFO)
            TRANSPORT: Transport type (default: stdio)
            DISABLED_TOOLS: Comma-separated list of disabled tools
            EXPERT_ANALYSIS_ENABLED: Enable expert analysis (default: false)
            EXPERT_ANALYSIS_TIMEOUT: Timeout in seconds (default: 30)
            EXPERT_ANALYSIS_MAX_FINDINGS: Max findings to analyze (default: 50)

        Returns:
            ServerConfiguration instance
        """
        server_name = os.getenv("SERVER_NAME", "optix-mcp-server")

        log_level_str = os.getenv("OPTIX_LOG_LEVEL", "").strip()
        if not log_level_str:
            log_level_str = os.getenv("LOG_LEVEL", "INFO").strip()
        log_level_str = log_level_str.upper()

        try:
            log_level = LogLevel(log_level_str)
        except ValueError:
            log_level = LogLevel.INFO

        transport_str = os.getenv("TRANSPORT", "stdio").lower()
        try:
            transport = Transport(transport_str)
        except ValueError:
            transport = Transport.STDIO

        disabled_tools_str = os.getenv("DISABLED_TOOLS", "")
        disabled_tools = [
            t.strip() for t in disabled_tools_str.split(",") if t.strip()
        ]

        api_keys = APIKeyConfig.from_env()

        expert_analysis_enabled = (
            os.getenv("EXPERT_ANALYSIS_ENABLED", "false").lower() == "true"
        )
        expert_analysis_timeout = int(os.getenv("EXPERT_ANALYSIS_TIMEOUT", "30"))
        expert_analysis_max_findings = int(
            os.getenv("EXPERT_ANALYSIS_MAX_FINDINGS", "50")
        )

        return cls(
            server_name=server_name,
            log_level=log_level,
            transport=transport,
            disabled_tools=disabled_tools,
            api_keys=api_keys,
            expert_analysis_enabled=expert_analysis_enabled,
            expert_analysis_timeout=expert_analysis_timeout,
            expert_analysis_max_findings=expert_analysis_max_findings,
        )


@dataclass
class HealthCheckResponse:
    """Health check response data.

    Attributes:
        status: Server health status
        server_name: Name of the server
        version: Server version string
        uptime_seconds: Time since server start
        tools_available: List of available tool names
    """
    status: HealthStatus
    server_name: str
    version: str
    uptime_seconds: Optional[float] = None
    tools_available: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "status": self.status.value,
            "server_name": self.server_name,
            "version": self.version,
            "tools_available": self.tools_available,
        }
        if self.uptime_seconds is not None:
            result["uptime_seconds"] = self.uptime_seconds
        return result


@dataclass
class DashboardConfig:
    """Dashboard server configuration.

    Attributes:
        enabled: Whether the dashboard is enabled
        host: Host to bind the dashboard server to
        port: Port to bind the dashboard server to
    """
    enabled: bool = True
    host: str = "localhost"
    port: int = 24282

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        if self.host not in ("localhost", "127.0.0.1"):
            raise ValueError(
                "Dashboard host must be localhost or 127.0.0.1 for security"
            )
        if not 1024 <= self.port <= 65535:
            raise ValueError("Dashboard port must be between 1024 and 65535")

    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Create dashboard configuration from environment variables.

        Environment variables:
            DASHBOARD_ENABLED: Enable dashboard (default: true)
            DASHBOARD_HOST: Host to bind to (default: localhost)
            DASHBOARD_PORT: Port to bind to (default: 24282)

        Returns:
            DashboardConfig instance
        """
        return cls(
            enabled=os.getenv("DASHBOARD_ENABLED", "true").lower() == "true",
            host=os.getenv("DASHBOARD_HOST", "localhost"),
            port=int(os.getenv("DASHBOARD_PORT", "24282")),
        )
