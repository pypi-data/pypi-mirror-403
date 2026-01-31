"""Installation wizard orchestration."""

import os
import platform
import sys
from dataclasses import dataclass, field

from cli.installer.agents import (
    AGENTS,
    AgentConfig,
    ConfigFormat,
    get_agent,
    get_all_agents,
)
from cli.installer.config_writers import JSONConfigWriter, TOMLConfigWriter
from cli.installer.ui import AgentChoice, ConsoleUI
from cli.installer.uv_manager import ensure_uv


@dataclass
class InstallationOptions:
    """Options for the installation wizard."""
    agents: list[str] = field(default_factory=list)
    scope: str = ""
    expert: bool | None = None
    quiet: bool = False
    verbose: bool = False


class InstallationWizard:
    """Main installation wizard orchestrator."""

    def __init__(self, options: InstallationOptions | None = None):
        self.options = options or InstallationOptions()
        self.ui = ConsoleUI(
            quiet=self.options.quiet,
            verbose=self.options.verbose,
        )
        self.selected_agents: list[str] = []
        self.scope: str = ""
        self.expert_enabled: bool = False
        self.api_keys: dict[str, str] = {
            "openai": "",
        }
        self.os_type: str = ""
        self.dashboard_enabled: bool = False
        self.dashboard_port: int = 24282

    def run(self) -> bool:
        """Run the installation wizard.

        Returns:
            True if installation completed successfully
        """
        try:
            self.ui.show_header()

            self._detect_os()

            if not ensure_uv(self.ui):
                return False

            self._select_agents()
            self._select_scope()
            self._configure_expert()
            self._configure_dashboard()
            self._configure_agents()

            self.ui.show_completion(
                agents=self.selected_agents,
                scope=self.scope,
                expert_enabled=self.expert_enabled,
                dashboard_enabled=self.dashboard_enabled,
                dashboard_port=self.dashboard_port,
            )

            return True

        except KeyboardInterrupt:
            self.ui.newline()
            self.ui.warn("Installation interrupted. Run the wizard again to start fresh.")
            return False

    def _detect_os(self) -> None:
        """Detect and validate operating system."""
        self.ui.info("Detecting operating system...")

        system = platform.system()

        if system == "Darwin":
            self.os_type = "macos"
            self.ui.success("Detected macOS")
        elif system == "Linux":
            self.os_type = "linux"
            self.ui.success("Detected Linux")
        elif system == "Windows":
            self.os_type = "windows"
            self.ui.success("Detected Windows")
        else:
            self.ui.error(f"Unsupported operating system: {system}")
            self.ui.error("This installer supports macOS, Linux, and Windows.")
            sys.exit(1)

    def _select_agents(self) -> None:
        """Select which agents to configure."""
        if self.options.agents:
            for agent_name in self.options.agents:
                agent = get_agent(agent_name)
                if not agent:
                    self.ui.error(f"Unknown agent: {agent_name}")
                    self.ui.error(f"Valid agents: {', '.join(AGENTS.keys())}")
                    sys.exit(1)
                self.selected_agents.append(agent_name.lower())

            if not self.selected_agents:
                self.ui.error("At least one agent must be selected")
                sys.exit(1)

            self.ui.info(f"Selected agents: {', '.join(self.selected_agents)}")
            return

        self.ui.newline()
        choices = [
            AgentChoice(name=agent.name, label=agent.label)
            for agent in get_all_agents()
        ]

        self.selected_agents = self.ui.select_agents(choices)
        self.ui.success(f"Selected agents: {', '.join(self.selected_agents)}")

    def _select_scope(self) -> None:
        """Select installation scope (global/local)."""
        if self.options.scope:
            if self.options.scope not in ("global", "local"):
                self.ui.error(f"Invalid scope: {self.options.scope}")
                self.ui.error("Scope must be 'global' or 'local'")
                sys.exit(1)

            self.scope = self.options.scope
            self.ui.info(f"Installation scope: {self.scope}")
            return

        self.ui.newline()
        self.scope = self.ui.select_scope()
        self.ui.success(f"Installation scope: {self.scope}")

    def _configure_expert(self) -> None:
        """Configure expert analysis feature."""
        if self.options.expert is not None:
            self.expert_enabled = self.options.expert
            status = "enabled" if self.expert_enabled else "disabled"
            self.ui.info(f"Expert analysis: {status}")

            if self.expert_enabled:
                self._prompt_api_keys()
            return

        self.ui.newline()
        self.ui.info("Enable Expert Analysis (multi-LLM consensus)?")
        self.ui.console.print(
            "  Expert analysis uses multiple OpenAI models for improved accuracy.\n"
            "  Requires an OpenAI API key."
        )
        self.ui.newline()

        self.expert_enabled = self.ui.select_yes_no("Enable expert analysis?", default=False)

        if self.expert_enabled:
            self._prompt_api_keys()
        else:
            self.ui.info("Expert analysis disabled")

    def _configure_dashboard(self) -> None:
        """Configure dashboard UI settings."""
        self.ui.newline()
        self.ui.info("Dashboard UI Configuration")
        self.ui.console.print(
            "  The dashboard provides a web interface for viewing audit results.\n"
        )

        self.dashboard_enabled = self.ui.select_yes_no(
            "Enable dashboard UI?",
            default=False
        )

        if self.dashboard_enabled:
            self.dashboard_port = self.ui.prompt_port(
                "Dashboard port:",
                default=24282
            )
            self.ui.success(f"Dashboard will run on port {self.dashboard_port}")
        else:
            self.ui.info("Dashboard disabled")

    def _prompt_api_keys(self) -> None:
        """Prompt for API keys or use existing environment variables."""
        self.ui.newline()
        self.ui.info("Configure LLM API Keys:")

        existing_keys = {
            "openai": os.environ.get("OPENAI_API_KEY", ""),
        }

        has_existing = any(existing_keys.values())

        if has_existing:
            self.ui.info("Detected existing API key in environment:")
            if existing_keys["openai"]:
                self.ui.console.print(f"    OpenAI: ***{existing_keys['openai'][-4:]}")

            if self.options.expert is not None:
                self.api_keys = existing_keys
                self.ui.success("Using existing API keys (non-interactive mode)")
                return

            self.ui.newline()
            use_existing = self.ui.select_yes_no("Use detected keys?", default=True)

            if use_existing:
                self.api_keys = existing_keys
                self.ui.success("Using existing API keys")
                return

        self.ui.console.print("\n  Press Enter to skip.\n")

        self.api_keys["openai"] = self.ui.prompt_password("  OpenAI API Key:")

        if not self.api_keys["openai"]:
            self.ui.warn("No OpenAI API key provided. Expert analysis will be disabled.")
            self.expert_enabled = False
        else:
            self.ui.success("OpenAI API key configured")

    def _configure_agents(self) -> None:
        """Configure all selected agents."""
        self.ui.newline()
        self.ui.info("Configuring agent(s)...")

        for agent_name in self.selected_agents:
            agent = get_agent(agent_name)
            if agent:
                self._configure_single_agent(agent)

    def _build_env_vars(self) -> dict[str, str]:
        """Build environment variables dict for MCP config."""
        env_vars = {
            "SERVER_NAME": "optix-mcp-server",
            "LOG_LEVEL": "INFO",
            "TRANSPORT": "stdio",
            "EXPERT_ANALYSIS_ENABLED": "true" if self.expert_enabled else "false",
            "DASHBOARD_ENABLED": "true" if self.dashboard_enabled else "false",
        }

        if self.api_keys.get("openai"):
            env_vars["OPENAI_API_KEY"] = self.api_keys["openai"]
            env_vars["OPTIX_LLM_PROVIDER"] = "openai"

        if self.dashboard_enabled:
            env_vars["DASHBOARD_PORT"] = str(self.dashboard_port)

        return env_vars

    def _configure_single_agent(self, agent: AgentConfig) -> None:
        """Configure a single agent."""
        config_path = agent.get_config_path(self.scope)

        if agent.config_format == ConfigFormat.JSON:
            writer = JSONConfigWriter()
        else:
            writer = TOMLConfigWriter()

        env_vars = self._build_env_vars()

        server_config = dict(agent.server_config)
        server_config["env"] = env_vars

        writer.merge_server_config(
            path=config_path,
            key_path=agent.key_path,
            server_name="optix",
            config=server_config,
        )

        self.ui.success(f"Configured {agent.label}: {config_path}")
