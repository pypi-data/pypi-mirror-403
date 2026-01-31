"""health_check tool package.

This module provides the health_check tool implementation which can be:
- Called directly without MCP context
- Registered with FastMCP server
- Unit tested in isolation
"""

from tools.health_check.core import health_check_impl

__all__ = ["health_check_impl"]
