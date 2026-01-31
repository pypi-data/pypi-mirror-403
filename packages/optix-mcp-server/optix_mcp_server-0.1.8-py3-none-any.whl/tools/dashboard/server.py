"""HTTP server for the Optix Dashboard.

Provides a lightweight threaded HTTP server using Python stdlib.
"""

import threading
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from typing import Optional

from config.defaults import DashboardConfig
from logging_utils import get_tool_logger
from tools.dashboard.handlers import DashboardHandler


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for handling concurrent requests."""
    daemon_threads = True
    allow_reuse_address = True


_server_instance: Optional[ThreadedHTTPServer] = None
_server_thread: Optional[threading.Thread] = None
_actual_port: Optional[int] = None
_websocket_port: Optional[int] = None

MAX_PORT_ATTEMPTS = 10


def start_dashboard_server(config: Optional[DashboardConfig] = None) -> Optional[threading.Thread]:
    """Start the dashboard HTTP server in a daemon thread.

    Args:
        config: Optional dashboard configuration. If not provided,
                loads from environment variables.

    Returns:
        The server thread if started successfully, None if disabled
    """
    global _server_instance, _server_thread

    logger = get_tool_logger("dashboard")

    if config is None:
        config = DashboardConfig.from_env()

    if not config.enabled:
        logger.info("Dashboard is disabled")
        return None

    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Invalid dashboard configuration: {e}")
        return None

    if _server_instance is not None:
        logger.warning("Dashboard server already running")
        return _server_thread

    global _actual_port

    for port_offset in range(MAX_PORT_ATTEMPTS):
        try_port = config.port + port_offset
        if try_port > 65535:
            break

        try:
            _server_instance = ThreadedHTTPServer(
                (config.host, try_port),
                DashboardHandler,
            )
            _actual_port = try_port

            _server_thread = threading.Thread(
                target=_server_instance.serve_forever,
                daemon=True,
                name="DashboardServer",
            )
            _server_thread.start()

            if try_port != config.port:
                logger.info(f"Port {config.port} in use, using {try_port}")
            logger.info(f"Dashboard server started at http://{config.host}:{try_port}")

            _start_websocket_server(config.host, try_port + 1)

            return _server_thread

        except OSError as e:
            if "Address already in use" in str(e) or "already in use" in str(e).lower():
                logger.debug(f"Port {try_port} in use, trying next...")
                continue
            logger.error(f"Failed to start dashboard server: {e}")
            _server_instance = None
            _actual_port = None
            return None

    logger.error(f"Failed to start dashboard server: all ports {config.port}-{config.port + MAX_PORT_ATTEMPTS - 1} in use")
    return None


def _start_websocket_server(host: str, port: int) -> None:
    """Start the WebSocket server for real-time communication."""
    global _websocket_port

    logger = get_tool_logger("dashboard")

    try:
        from tools.dashboard.websocket import start_websocket_server
        if start_websocket_server(host, port):
            _websocket_port = port
            logger.info(f"WebSocket server started at ws://{host}:{port}")
    except ImportError as e:
        logger.warning(f"WebSocket server not available: {e}")
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")


def stop_dashboard_server() -> None:
    """Stop the dashboard HTTP server and WebSocket server."""
    global _server_instance, _server_thread, _actual_port, _websocket_port

    logger = get_tool_logger("dashboard")

    try:
        from tools.dashboard.websocket import stop_websocket_server
        stop_websocket_server()
    except ImportError:
        pass

    if _server_instance is not None:
        _server_instance.shutdown()
        _server_instance = None
        _server_thread = None
        _actual_port = None
        _websocket_port = None
        logger.info("Dashboard server stopped")


def is_dashboard_running() -> bool:
    """Check if the dashboard server is running."""
    return _server_instance is not None and _server_thread is not None and _server_thread.is_alive()


def get_actual_port() -> Optional[int]:
    """Get the actual port the dashboard is running on.

    Returns:
        The actual port number if the server is running, None otherwise
    """
    return _actual_port


def get_websocket_port() -> Optional[int]:
    """Get the port the WebSocket server is running on.

    Returns:
        The WebSocket port number if running, None otherwise
    """
    return _websocket_port
