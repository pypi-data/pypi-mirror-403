"""Base interfaces for MCP-agnostic tool implementations.

This module defines the Protocol interface for tools that can be:
- Called directly without MCP context
- Registered with FastMCP server
- Unit tested in isolation
"""

from typing import Any, Callable, Protocol


class Tool(Protocol):
    """Protocol for MCP-agnostic tool implementations.

    Tools implementing this protocol can be:
    - Called directly without MCP context
    - Registered with FastMCP server
    - Unit tested in isolation
    """

    @property
    def name(self) -> str:
        """Unique identifier for the tool.

        Returns:
            Tool name (lowercase, alphanumeric with underscores)
        """
        ...

    @property
    def description(self) -> str:
        """Human-readable description.

        Returns:
            Description string for MCP schema and documentation
        """
        ...

    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with given arguments.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            JSON-serializable result

        Raises:
            ValueError: For invalid input
            RuntimeError: For execution failures
        """
        ...


# Type alias for function-based tools
ToolFunction = Callable[..., Any]
