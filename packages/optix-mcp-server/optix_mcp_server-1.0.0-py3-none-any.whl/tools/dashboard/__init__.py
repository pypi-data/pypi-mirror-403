"""Dashboard module for Optix MCP Server.

Provides a lightweight web-based dashboard for monitoring audit workflows
and browsing generated reports.
"""

from tools.dashboard.server import (
    start_dashboard_server,
    stop_dashboard_server,
    is_dashboard_running,
    get_actual_port,
    get_websocket_port,
)

__all__ = [
    "start_dashboard_server",
    "stop_dashboard_server",
    "is_dashboard_running",
    "get_actual_port",
    "get_websocket_port",
]
