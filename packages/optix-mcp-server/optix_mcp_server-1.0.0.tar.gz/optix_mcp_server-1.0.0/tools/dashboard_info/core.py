"""Core implementation for the dashboard_info tool."""

from typing import Optional


def dashboard_info_impl(
    enabled: bool,
    host: str,
    configured_port: int,
    actual_port: Optional[int],
    is_running: bool,
) -> dict:
    """Get dashboard connection information.

    Args:
        enabled: Whether the dashboard is enabled in configuration
        host: The configured host address
        configured_port: The port configured in settings
        actual_port: The actual port the dashboard is running on (may differ if configured port was in use)
        is_running: Whether the dashboard server is currently running

    Returns:
        Dictionary with dashboard status and connection info
    """
    if not enabled:
        return {
            "enabled": False,
            "running": False,
            "url": None,
            "host": host,
            "configured_port": configured_port,
            "actual_port": None,
            "message": "Dashboard is disabled in configuration",
        }

    if not is_running:
        return {
            "enabled": True,
            "running": False,
            "url": None,
            "host": host,
            "configured_port": configured_port,
            "actual_port": None,
            "message": "Dashboard is enabled but not currently running",
        }

    url = f"http://{host}:{actual_port}"
    message = f"Dashboard is running at {url}"

    if actual_port != configured_port:
        message += f" (configured port {configured_port} was in use)"

    return {
        "enabled": True,
        "running": True,
        "url": url,
        "host": host,
        "configured_port": configured_port,
        "actual_port": actual_port,
        "message": message,
    }
