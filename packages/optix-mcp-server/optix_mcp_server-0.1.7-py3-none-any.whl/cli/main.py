"""CLI entry point for optix-mcp-server."""

import argparse
import sys
from importlib.metadata import version, PackageNotFoundError

from cli.installer.agents import get_agent_names


def get_version() -> str:
    """Get package version."""
    try:
        return version("optix-mcp-server")
    except PackageNotFoundError:
        return "0.1.1"


def cmd_server(args: argparse.Namespace) -> int:
    """Run the MCP server."""
    from server import main as server_main
    server_main()
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    """Run the installation wizard."""
    from cli.installer.wizard import InstallationWizard, InstallationOptions

    agents = []
    if args.agents:
        agents = [a.strip() for a in args.agents.split(",")]

    expert = None
    if args.expert:
        expert = True
    elif args.no_expert:
        expert = False

    options = InstallationOptions(
        agents=agents,
        scope=args.scope or "",
        expert=expert,
        quiet=args.quiet,
        verbose=args.verbose,
    )

    wizard = InstallationWizard(options)
    success = wizard.run()

    return 0 if success else 1


def cmd_health(args: argparse.Namespace) -> int:
    """Check configuration status."""
    from rich.console import Console
    from rich.table import Table
    from cli.installer.agents import get_all_agents
    from cli.installer.uv_manager import check_uv

    console = Console()

    console.print("\n[bold]Optix Configuration Status[/bold]\n")

    is_valid, uv_path, uv_version = check_uv()
    if is_valid:
        console.print(f"[green]✓[/green] uv {uv_version} installed at {uv_path}")
    else:
        console.print("[red]✗[/red] uv not installed or outdated")

    console.print()

    table = Table(title="Agent Configurations")
    table.add_column("Agent", style="cyan")
    table.add_column("Global Config", style="dim")
    table.add_column("Local Config", style="dim")
    table.add_column("Status")

    for agent in get_all_agents():
        global_path = agent.get_config_path("global")
        local_path = agent.get_config_path("local")

        global_exists = global_path.exists()
        local_exists = local_path.exists()

        if global_exists or local_exists:
            status = "[green]configured[/green]"
        else:
            status = "[dim]not configured[/dim]"

        table.add_row(
            agent.label,
            "[green]✓[/green]" if global_exists else "[dim]-[/dim]",
            "[green]✓[/green]" if local_exists else "[dim]-[/dim]",
            status,
        )

    console.print(table)
    console.print()

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="optix",
        description="Optix MCP Server - Source code analysis tools",
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    subparsers = parser.add_subparsers(dest="command")

    server_parser = subparsers.add_parser(
        "server",
        help="Run the MCP server (default when no command given)",
    )
    server_parser.set_defaults(func=cmd_server)

    install_parser = subparsers.add_parser(
        "install",
        help="Run the installation wizard",
    )
    install_parser.add_argument(
        "--agents",
        type=str,
        help=f"Comma-separated agent list ({','.join(get_agent_names())})",
    )
    install_parser.add_argument(
        "--scope",
        type=str,
        choices=["global", "local"],
        help="Installation scope (global or local)",
    )
    install_parser.add_argument(
        "--expert",
        action="store_true",
        help="Enable expert analysis feature",
    )
    install_parser.add_argument(
        "--no-expert",
        action="store_true",
        help="Disable expert analysis feature",
    )
    install_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output",
    )
    install_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed output",
    )
    install_parser.set_defaults(func=cmd_install)

    health_parser = subparsers.add_parser(
        "health",
        help="Check configuration status",
    )
    health_parser.set_defaults(func=cmd_health)

    args = parser.parse_args()

    if args.command is None:
        return cmd_server(args)

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
