"""MCP tool implementations for optix-mcp-server.

This module provides the tool registry for managing MCP-agnostic tools.
Tools are implemented as pure functions that can be:
- Called directly without MCP context
- Registered with FastMCP server via thin wrappers
- Unit tested in isolation
"""

from typing import Any, Callable

from tools.base import Tool, ToolFunction

# Tool registry mapping tool names to their implementations and metadata
TOOL_REGISTRY: dict[str, dict[str, Any]] = {}

# Legacy list for backward compatibility
AVAILABLE_TOOLS: list[str] = []


def register_tool(
    name: str,
    impl: Callable[..., Any] | None = None,
    description: str = "",
) -> None:
    """Register a tool as available.

    Args:
        name: Tool name to register
        impl: Optional implementation function (for new-style registration)
        description: Optional tool description
    """
    if name not in AVAILABLE_TOOLS:
        AVAILABLE_TOOLS.append(name)

    if impl is not None:
        TOOL_REGISTRY[name] = {
            "impl": impl,
            "description": description,
        }


def get_available_tools() -> list[str]:
    """Get list of all available tools.

    Returns:
        List of tool names
    """
    return AVAILABLE_TOOLS.copy()


def is_tool_available(name: str) -> bool:
    """Check if a tool is available.

    Args:
        name: Tool name to check

    Returns:
        True if tool is available
    """
    return name in AVAILABLE_TOOLS


def get_tool_impl(name: str) -> Callable[..., Any]:
    """Get the implementation function for a tool.

    Args:
        name: Tool name to look up

    Returns:
        The tool implementation function

    Raises:
        KeyError: If tool is not registered with an implementation
    """
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{name}' not found in registry")
    return TOOL_REGISTRY[name]["impl"]


def get_tool_description(name: str) -> str:
    """Get the description for a tool.

    Args:
        name: Tool name to look up

    Returns:
        The tool description

    Raises:
        KeyError: If tool is not registered
    """
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{name}' not found in registry")
    return TOOL_REGISTRY[name]["description"]


__all__ = [
    "Tool",
    "ToolFunction",
    "TOOL_REGISTRY",
    "AVAILABLE_TOOLS",
    "register_tool",
    "get_available_tools",
    "is_tool_available",
    "get_tool_impl",
    "get_tool_description",
]
