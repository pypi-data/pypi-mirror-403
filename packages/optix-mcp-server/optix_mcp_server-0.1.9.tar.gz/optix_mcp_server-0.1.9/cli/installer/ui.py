"""Terminal UI components for the installation wizard."""

import socket
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import questionary
from questionary import Style

OPTIX_HEADER = """
   ██████╗ ██████╗ ████████╗██╗██╗  ██╗
  ██╔═══██╗██╔══██╗╚══██╔══╝██║╚██╗██╔╝
  ██║   ██║██████╔╝   ██║   ██║ ╚███╔╝
  ██║   ██║██╔═══╝    ██║   ██║ ██╔██╗
  ╚██████╔╝██║        ██║   ██║██╔╝ ██╗
   ╚═════╝ ╚═╝        ╚═╝   ╚═╝╚═╝  ╚═╝

  MCP Server Installation Wizard
"""

OPTIX_DESCRIPTION = """AI-powered MCP server for comprehensive code analysis.

  Audit Tools:
    • Security Audit - Vulnerability detection and security analysis
    • Accessibility Audit - WCAG 2.1/2.2 compliance checks
    • DevOps Audit - Docker, CI/CD, and dependency analysis
    • Principal Audit - Code quality, complexity, and coupling metrics

  Supporting Features:
    • Report Generation - Standardized audit reports
    • Dashboard UI - Real-time audit monitoring
    • PR Comments - Post findings to GitHub PRs
    • Expert Analysis - AI-enhanced insights"""

QUESTIONARY_STYLE = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "bold"),
    ("answer", "fg:cyan bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan"),
    ("selected", "fg:cyan bold"),
    ("separator", "fg:gray"),
    ("instruction", "fg:gray"),
])


@dataclass
class AgentChoice:
    """Represents an agent selection choice."""
    name: str
    label: str
    checked: bool = False


class ConsoleUI:
    """Terminal UI handler using rich and questionary."""

    def __init__(self, quiet: bool = False, verbose: bool = False):
        self.console = Console()
        self.quiet = quiet
        self.verbose = verbose

    def show_header(self) -> None:
        if self.quiet:
            return
        self.console.print(Text(OPTIX_HEADER, style="cyan"))
        self.console.print(
            Panel(
                OPTIX_DESCRIPTION,
                border_style="cyan",
                padding=(0, 1),
            )
        )
        self.console.print()

    def info(self, message: str) -> None:
        if self.quiet:
            return
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def success(self, message: str) -> None:
        if self.quiet:
            return
        self.console.print(f"[green]✓[/green] {message}")

    def warn(self, message: str) -> None:
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str) -> None:
        self.console.print(f"[red]✗[/red] {message}", style="red")

    def debug(self, message: str) -> None:
        if self.verbose:
            self.console.print(f"[cyan]→[/cyan] {message}")

    def newline(self) -> None:
        if not self.quiet:
            self.console.print()

    def select_agents(self, choices: list[AgentChoice]) -> list[str]:
        """Multi-select agent checkboxes using native checkbox widget."""
        checkbox_choices = [
            questionary.Choice(
                title=choice.label,
                value=choice.name,
                checked=choice.checked,
            )
            for choice in choices
        ]

        result = questionary.checkbox(
            "Select AI agents to configure:",
            choices=checkbox_choices,
            style=QUESTIONARY_STYLE,
            instruction="(Space to toggle, Enter to submit)",
        ).ask()

        if result is None:
            raise KeyboardInterrupt()

        if not result:
            self.warn("Please select at least one agent")
            return self.select_agents(choices)

        return result

    def select_scope(self) -> str:
        """Single select for installation scope."""
        choices = [
            questionary.Choice(title="Global (user-wide)", value="global"),
            questionary.Choice(title="Local (current project)", value="local"),
        ]

        selected = questionary.select(
            "Select installation scope:",
            choices=choices,
            style=QUESTIONARY_STYLE,
        ).ask()

        if selected is None:
            raise KeyboardInterrupt()

        return selected

    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask for confirmation."""
        result = questionary.confirm(
            message,
            default=default,
            style=QUESTIONARY_STYLE,
        ).ask()

        if result is None:
            raise KeyboardInterrupt()

        return result

    def prompt_password(self, message: str) -> str:
        """Prompt for password/secret input (hidden)."""
        result = questionary.password(
            message,
            style=QUESTIONARY_STYLE,
        ).ask()

        if result is None:
            raise KeyboardInterrupt()

        return result or ""

    def prompt_text(self, message: str, default: str = "") -> str:
        """Prompt for text input."""
        result = questionary.text(
            message,
            default=default,
            style=QUESTIONARY_STYLE,
        ).ask()

        if result is None:
            raise KeyboardInterrupt()

        return result or ""

    def show_completion(
        self,
        agents: list[str],
        scope: str,
        expert_enabled: bool,
        dashboard_enabled: bool = False,
        dashboard_port: int = 24282,
    ) -> None:
        """Show final completion panel."""
        self.newline()

        agent_list = "\n".join(f"    • {agent}" for agent in agents)
        expert_status = "[cyan]enabled[/cyan]" if expert_enabled else "disabled"
        dashboard_status = f"[cyan]enabled[/cyan] (port {dashboard_port})" if dashboard_enabled else "disabled"

        content = f"""[bold]Configured agents:[/bold]
{agent_list}

[bold]Scope:[/bold] {scope}
[bold]Expert analysis:[/bold] {expert_status}
[bold]Dashboard UI:[/bold] {dashboard_status}

[bold]Next steps:[/bold]
  1. Restart your AI agent application
  2. Verify installation with: health_check tool
  3. Run your first audit: security_audit tool

[bold]Documentation:[/bold]
  https://github.com/ravnhq/ravn-labs-optix-2#readme"""

        panel = Panel(
            content,
            title="[cyan]Installation Complete![/cyan]",
            border_style="cyan",
        )
        self.console.print(panel)

    def select_yes_no(self, message: str, default: bool = False) -> bool:
        """Yes/No selection with immediate selection on Enter."""
        choices = [
            questionary.Choice(title="Yes", value=True),
            questionary.Choice(title="No", value=False),
        ]

        result = questionary.select(
            message,
            choices=choices,
            style=QUESTIONARY_STYLE,
        ).ask()

        if result is None:
            raise KeyboardInterrupt()

        return result

    def validate_port(self, port_str: str) -> tuple[bool, int, str]:
        """Validate port number.

        Returns: (is_valid, port_number, error_message)
        """
        try:
            port = int(port_str)
        except ValueError:
            return False, 0, "Invalid port number - must be an integer"

        if port < 1024:
            return False, 0, "Ports 1-1023 are reserved and require admin privileges"

        if port > 65535:
            return False, 0, "Port must be between 1024 and 65535"

        if self._is_port_in_use(port):
            return False, 0, f"Port {port} is already in use"

        return True, port, ""

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("localhost", port)) == 0

    def prompt_port(self, message: str, default: int = 24282) -> int:
        """Prompt for port number with validation."""
        while True:
            result = questionary.text(
                message,
                default=str(default),
                style=QUESTIONARY_STYLE,
            ).ask()

            if result is None:
                raise KeyboardInterrupt()

            is_valid, port, error = self.validate_port(result)
            if is_valid:
                return port

            self.warn(error)
