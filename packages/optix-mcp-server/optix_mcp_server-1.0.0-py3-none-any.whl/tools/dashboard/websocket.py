"""WebSocket server for real-time dashboard communication.

Provides bidirectional communication for:
- Stop audit commands (client -> server)
- Real-time workflow updates (server -> client)
"""

import asyncio
import json
import threading
from typing import Optional, Set
from datetime import datetime

from logging_utils import get_tool_logger
from tools.workflow.state import WorkflowStateManager


class DashboardWebSocket:
    """WebSocket manager for dashboard real-time communication."""

    _instance: Optional["DashboardWebSocket"] = None
    _clients: Set[asyncio.Queue]
    _server: Optional[asyncio.AbstractServer] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None

    def __new__(cls) -> "DashboardWebSocket":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._clients = set()
            cls._instance._server = None
            cls._instance._loop = None
            cls._instance._thread = None
        return cls._instance

    def start(self, host: str = "127.0.0.1", port: int = 8081) -> bool:
        """Start the WebSocket server in a background thread."""
        logger = get_tool_logger("dashboard.websocket")

        if self._server is not None:
            logger.warning("WebSocket server already running")
            return True

        try:
            self._thread = threading.Thread(
                target=self._run_server,
                args=(host, port),
                daemon=True,
                name="DashboardWebSocket",
            )
            self._thread.start()
            logger.info(f"WebSocket server starting on ws://{host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False

    def _run_server(self, host: str, port: int) -> None:
        """Run the WebSocket server (called in background thread)."""
        logger = get_tool_logger("dashboard.websocket")

        try:
            import websockets
            import websockets.server
        except ImportError:
            logger.error("websockets library not installed. Run: pip install websockets")
            return

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def handler(websocket: websockets.server.WebSocketServerProtocol) -> None:
            """Handle a WebSocket connection."""
            client_queue: asyncio.Queue = asyncio.Queue()
            self._clients.add(client_queue)
            logger.debug(f"WebSocket client connected. Total: {len(self._clients)}")

            try:
                async def send_updates():
                    while True:
                        msg = await client_queue.get()
                        await websocket.send(msg)

                async def receive_commands():
                    async for message in websocket:
                        await self._handle_message(message, websocket)

                await asyncio.gather(
                    send_updates(),
                    receive_commands(),
                    return_exceptions=True
                )
            except websockets.exceptions.ConnectionClosed:
                logger.debug("WebSocket client disconnected")
            finally:
                self._clients.discard(client_queue)

        async def main():
            async with websockets.serve(handler, host, port) as server:
                self._server = server
                logger.info(f"WebSocket server running on ws://{host}:{port}")
                await asyncio.Future()

        try:
            self._loop.run_until_complete(main())
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")

    async def _handle_message(self, message: str, websocket) -> None:
        """Handle incoming WebSocket message."""
        logger = get_tool_logger("dashboard.websocket")

        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "stop_audit":
                workflow_id = data.get("workflow_id")
                if not workflow_id:
                    await websocket.send(json.dumps({
                        "action": "error",
                        "message": "workflow_id is required"
                    }))
                    return

                result = self._stop_audit(workflow_id)
                await websocket.send(json.dumps(result))

                if result.get("success"):
                    await self.broadcast({
                        "action": "workflow_cancelled",
                        "workflow_id": workflow_id,
                        "audit_type": result.get("audit_type"),
                        "timestamp": datetime.now().isoformat()
                    })

            elif action == "ping":
                await websocket.send(json.dumps({"action": "pong"}))

            else:
                await websocket.send(json.dumps({
                    "action": "error",
                    "message": f"Unknown action: {action}"
                }))

        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "action": "error",
                "message": "Invalid JSON"
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await websocket.send(json.dumps({
                "action": "error",
                "message": str(e)
            }))

    def _stop_audit(self, workflow_id: str) -> dict:
        """Stop an audit workflow."""
        logger = get_tool_logger("dashboard.websocket")

        manager = WorkflowStateManager()
        workflow = manager.get(workflow_id)

        if not workflow:
            return {
                "action": "audit_stopped",
                "success": False,
                "workflow_id": workflow_id,
                "message": f"Workflow not found: {workflow_id}"
            }

        if workflow.is_finished:
            return {
                "action": "audit_stopped",
                "success": False,
                "workflow_id": workflow_id,
                "audit_type": workflow.tool_name,
                "message": "Workflow already finished"
            }

        if workflow.is_cancelled:
            return {
                "action": "audit_stopped",
                "success": False,
                "workflow_id": workflow_id,
                "audit_type": workflow.tool_name,
                "message": "Workflow already cancelled"
            }

        success = manager.cancel(workflow_id)
        logger.info(f"Audit cancelled: {workflow_id} ({workflow.tool_name})")

        return {
            "action": "audit_stopped",
            "success": success,
            "workflow_id": workflow_id,
            "audit_type": workflow.tool_name,
            "message": "Audit cancelled successfully" if success else "Failed to cancel"
        }

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        if not self._clients:
            return

        msg_str = json.dumps(message)
        for client_queue in self._clients.copy():
            try:
                await client_queue.put(msg_str)
            except Exception:
                pass

    def broadcast_sync(self, message: dict) -> None:
        """Synchronous broadcast (can be called from non-async code)."""
        if not self._loop or not self._clients:
            return

        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast(message),
                self._loop
            )
        except Exception:
            pass

    def stop(self) -> None:
        """Stop the WebSocket server."""
        logger = get_tool_logger("dashboard.websocket")

        if self._server:
            self._server.close()
            self._server = None

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None

        self._thread = None
        self._clients.clear()
        logger.info("WebSocket server stopped")

    @property
    def is_running(self) -> bool:
        """Check if the WebSocket server is running."""
        return self._server is not None and self._thread is not None and self._thread.is_alive()

    @property
    def client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self._clients)


_websocket_instance: Optional[DashboardWebSocket] = None


def get_websocket_server() -> DashboardWebSocket:
    """Get the singleton WebSocket server instance."""
    global _websocket_instance
    if _websocket_instance is None:
        _websocket_instance = DashboardWebSocket()
    return _websocket_instance


def start_websocket_server(host: str = "127.0.0.1", port: int = 8081) -> bool:
    """Start the WebSocket server."""
    return get_websocket_server().start(host, port)


def stop_websocket_server() -> None:
    """Stop the WebSocket server."""
    get_websocket_server().stop()
