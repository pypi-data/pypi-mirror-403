"""health_check tool core implementation.

This module contains the pure business logic for the health_check tool.
It has NO MCP dependencies and can be:
- Called directly without MCP context
- Unit tested in isolation
- Reused in different server implementations
"""

from typing import Optional

from logging_utils import get_tool_logger

_logger = None


def _get_logger():
    """Get or create logger for health_check."""
    global _logger
    if _logger is None:
        _logger = get_tool_logger("health_check")
    return _logger


def health_check_impl(
    server_name: str,
    version: str,
    uptime_seconds: float,
    available_tools: list[str],
    disabled_tools: Optional[list[str]] = None,
) -> dict:
    """Check the health status of the MCP server.

    This is a pure function with no MCP dependencies. It takes all required
    data as parameters and returns a dictionary that can be JSON serialized.

    Args:
        server_name: Name of the server
        version: Server version string (semver format)
        uptime_seconds: Time since server started in seconds
        available_tools: List of all available tool names
        disabled_tools: Optional list of disabled tool names to filter out

    Returns:
        Dictionary containing:
        - status: Server health status (healthy, degraded, unhealthy)
        - server_name: Name of the server
        - version: Server version
        - uptime_seconds: Time since server started
        - tools_available: List of available (non-disabled) tool names
    """
    logger = _get_logger()
    logger.debug("Health check starting")

    tools = available_tools.copy()
    if disabled_tools:
        tools = [t for t in tools if t not in disabled_tools]

    logger.debug(f"Found {len(tools)} available tools")

    if len(tools) == 0:
        status = "degraded"
        logger.warn("No tools available - status degraded")
    else:
        status = "healthy"

    logger.info(f"Health check completed: status={status}")

    return {
        "status": status,
        "server_name": server_name,
        "version": version,
        "uptime_seconds": round(uptime_seconds, 2),
        "tools_available": tools,
    }
