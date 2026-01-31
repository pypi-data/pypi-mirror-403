"""HTTP request handlers for the Optix Dashboard.

Provides routing and request handling for all dashboard endpoints.
"""

import json
import re
import subprocess
import time
import traceback
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional

from config.defaults import HealthStatus
from logging_utils import get_tool_logger
from tools import get_available_tools
from tools.workflow.state import WorkflowState, WorkflowStateManager
from tools.dashboard.models import (
    WORKFLOW_ACTIVE_THRESHOLD_SECONDS,
    HealthResponse,
    ReportSummary,
    WorkflowDebugDetail,
    WorkflowDetail,
    WorkflowSummary,
)


REPORTS_DIR = Path("reports")
DASHBOARD_DIR = Path(__file__).resolve().parent
STATIC_DIR = (DASHBOARD_DIR / "static").resolve()
TEMPLATES_DIR = (DASHBOARD_DIR / "templates").resolve()

CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def get_project_name(project_root_path: Optional[str]) -> Optional[str]:
    """Extract project name from a project root path.

    Tries to get the git repository name first, falls back to directory name.

    Args:
        project_root_path: Path to the project root

    Returns:
        Project name or None if path is not provided
    """
    if not project_root_path:
        return None

    root = Path(project_root_path)

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return root.name


def json_response(handler: BaseHTTPRequestHandler, data: Any, status: int = 200) -> None:
    """Send a JSON API response."""
    response = {
        "success": status < 400,
        "data": data,
    }
    if status >= 400:
        response["error"] = data if isinstance(data, str) else None
        response["data"] = None

    body = json.dumps(response, default=str).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler: BaseHTTPRequestHandler, message: str, status: int = 400) -> None:
    """Send an error JSON response."""
    response = {
        "success": False,
        "data": None,
        "error": message,
    }
    body = json.dumps(response).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def validate_report_path(filename: str, reports_dir: Path) -> Optional[Path]:
    """Validate that a filename is safe and exists within reports directory."""
    if "/" in filename or "\\" in filename:
        return None

    if ".." in filename:
        return None

    file_path = (reports_dir / filename).resolve()

    try:
        file_path.relative_to(reports_dir.resolve())
        return file_path if file_path.exists() and file_path.is_file() else None
    except ValueError:
        return None


def get_workflows_snapshot() -> dict[str, WorkflowState]:
    """Get a thread-safe snapshot of all workflows."""
    manager = WorkflowStateManager()
    return manager._workflows.copy()


def determine_status(state: WorkflowState) -> str:
    """Determine if a workflow is active, completed, or cancelled."""
    if state.is_cancelled:
        return "cancelled"

    if state.is_finished:
        return "completed"

    threshold = timedelta(seconds=WORKFLOW_ACTIVE_THRESHOLD_SECONDS)
    time_since_update = datetime.now() - state.updated_at

    if time_since_update < threshold:
        return "active"
    return "completed"


def list_reports(reports_dir: Path) -> list[ReportSummary]:
    """List all report files in the reports directory."""
    if not reports_dir.exists():
        return []

    reports = []
    for file_path in reports_dir.glob("*.md"):
        if file_path.is_file():
            try:
                reports.append(ReportSummary.from_file(file_path))
            except (OSError, ValueError):
                continue

    return sorted(reports, key=lambda r: r.created_at, reverse=True)


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard routes."""

    server_version = "OptixDashboard/1.0"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        self.logger = get_tool_logger("dashboard")
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args) -> None:
        """Override to use our logger."""
        self.logger.debug(f"{self.address_string()} - {format % args}")

    def log_error(self, format: str, *args) -> None:
        """Override to use our logger."""
        self.logger.error(f"{self.address_string()} - {format % args}")

    def _log_request(self, status_code: int) -> None:
        """Log request with method, path, and status."""
        self.logger.debug(f"{self.command} {self.path} {status_code}")

    def do_GET(self) -> None:
        """Handle GET requests."""
        try:
            path = self.path.split("?")[0]

            if path == "/":
                self._handle_index()
            elif path.startswith("/static/"):
                self._handle_static(path)
            elif path == "/api/health":
                self._handle_health()
            elif path == "/api/workflows":
                self._handle_workflows_list()
            elif path.startswith("/api/workflows/"):
                workflow_id = path[len("/api/workflows/"):]
                self._handle_workflow_detail(workflow_id)
            elif path == "/api/reports":
                self._handle_reports_list()
            elif path.startswith("/api/reports/"):
                filename = path[len("/api/reports/"):]
                self._handle_report_content(filename)
            elif path == "/api/project":
                self._handle_project()
            elif path == "/api/websocket":
                self._handle_websocket_info()
            elif path.startswith("/api/debug/"):
                workflow_id = path[len("/api/debug/"):]
                self._handle_debug(workflow_id)
            else:
                self._handle_not_found()

        except Exception as e:
            self.logger.error(f"Error handling request: {e}\n{traceback.format_exc()}")
            error_response(self, "Internal server error", 500)
            self._log_request(500)

    def do_POST(self) -> None:
        """Handle POST requests."""
        try:
            path = self.path.split("?")[0]

            if path.startswith("/api/workflows/") and path.endswith("/stop"):
                workflow_id = path[len("/api/workflows/"):-len("/stop")]
                self._handle_stop_workflow(workflow_id)
            else:
                self._handle_not_found()

        except Exception as e:
            self.logger.error(f"Error handling POST request: {e}\n{traceback.format_exc()}")
            error_response(self, "Internal server error", 500)
            self._log_request(500)

    def _handle_index(self) -> None:
        """Serve the dashboard HTML page from template."""
        template_path = TEMPLATES_DIR / "index.html"

        if not template_path.exists():
            self.logger.error(f"Template not found: {template_path}")
            error_response(self, "Dashboard template not found", 500)
            self._log_request(500)
            return

        try:
            body = template_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            self._log_request(200)
        except Exception as e:
            self.logger.error(f"Error reading template: {e}")
            error_response(self, "Error reading dashboard template", 500)
            self._log_request(500)

    def _handle_static(self, path: str) -> None:
        """Serve static files from tools/dashboard/static/."""
        relative_path = path[len("/static/"):]

        if ".." in relative_path or relative_path.startswith("/"):
            error_response(self, "Invalid path", 400)
            self._log_request(400)
            return

        file_path = STATIC_DIR / relative_path

        self.logger.debug(f"Static file request: {path} -> {file_path}")

        if not file_path.exists() or not file_path.is_file():
            self.logger.error(f"Static file not found: {file_path} (STATIC_DIR={STATIC_DIR})")
            error_response(self, f"Not found: {path}", 404)
            self._log_request(404)
            return

        try:
            file_path.resolve().relative_to(STATIC_DIR)
        except ValueError:
            error_response(self, "Invalid path", 400)
            self._log_request(400)
            return

        suffix = file_path.suffix.lower()
        content_type = CONTENT_TYPES.get(suffix, "application/octet-stream")

        try:
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)
            self._log_request(200)
        except Exception as e:
            self.logger.error(f"Error reading static file {file_path}: {e}")
            error_response(self, "Error reading file", 500)
            self._log_request(500)

    def _handle_health(self) -> None:
        """Handle GET /api/health."""
        from server import __version__, _server_start_time, config

        uptime = time.time() - _server_start_time
        tools = get_available_tools()
        server_name = config.server_name if config else "optix-mcp-server"

        workflows = get_workflows_snapshot()
        active_count = sum(
            1 for state in workflows.values()
            if determine_status(state) == "active"
        )

        response = HealthResponse.from_health_check(
            status=HealthStatus.HEALTHY.value,
            server_name=server_name,
            version=__version__,
            uptime_seconds=uptime,
            tools_available=tools,
            active_workflow_count=active_count,
        )

        json_response(self, response.to_dict())
        self._log_request(200)

    def _handle_workflows_list(self) -> None:
        """Handle GET /api/workflows."""
        workflows = get_workflows_snapshot()

        summaries = []
        for state in workflows.values():
            status = determine_status(state)
            summaries.append(WorkflowSummary.from_state(state, status).to_dict())

        summaries.sort(key=lambda x: x["updated_at"], reverse=True)

        json_response(self, summaries)
        self._log_request(200)

    def _handle_workflow_detail(self, workflow_id: str) -> None:
        """Handle GET /api/workflows/{id}."""
        workflows = get_workflows_snapshot()

        if workflow_id not in workflows:
            error_response(self, f"Workflow not found: {workflow_id}", 404)
            self._log_request(404)
            return

        state = workflows[workflow_id]
        status = determine_status(state)
        detail = WorkflowDetail.from_state(state, status)

        json_response(self, detail.to_dict())
        self._log_request(200)

    def _handle_reports_list(self) -> None:
        """Handle GET /api/reports."""
        reports = list_reports(REPORTS_DIR)
        json_response(self, [r.to_dict() for r in reports])
        self._log_request(200)

    def _handle_report_content(self, filename: str) -> None:
        """Handle GET /api/reports/{filename}."""
        from urllib.parse import unquote
        filename = unquote(filename)

        file_path = validate_report_path(filename, REPORTS_DIR)

        if file_path is None:
            if "/" in filename or "\\" in filename or ".." in filename:
                error_response(self, "Invalid filename: path traversal not allowed", 400)
                self._log_request(400)
            else:
                error_response(self, f"Report not found: {filename}", 404)
                self._log_request(404)
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            json_response(self, {"filename": filename, "content": content})
            self._log_request(200)
        except Exception as e:
            self.logger.error(f"Error reading report {filename}: {e}")
            error_response(self, f"Error reading report: {filename}", 500)
            self._log_request(500)

    def _handle_project(self) -> None:
        """Handle GET /api/project."""
        workflows = get_workflows_snapshot()
        project_name = None
        project_root = None

        if workflows:
            sorted_workflows = sorted(
                workflows.values(),
                key=lambda w: w.updated_at,
                reverse=True,
            )
            for state in sorted_workflows:
                if state.project_root_path:
                    project_root = state.project_root_path
                    project_name = get_project_name(project_root)
                    if project_name:
                        break

        if not project_name:
            project_root = str(Path.cwd())
            project_name = get_project_name(project_root)

        json_response(self, {
            "project_name": project_name,
            "project_root_path": project_root,
        })
        self._log_request(200)

    def _handle_debug(self, workflow_id: str) -> None:
        """Handle GET /api/debug/{id}."""
        workflows = get_workflows_snapshot()

        if workflow_id not in workflows:
            error_response(self, f"Workflow not found: {workflow_id}", 404)
            self._log_request(404)
            return

        state = workflows[workflow_id]
        json_response(self, state.to_dict())
        self._log_request(200)

    def _handle_websocket_info(self) -> None:
        """Handle GET /api/websocket."""
        from tools.dashboard.server import get_websocket_port, get_actual_port

        ws_port = get_websocket_port()
        http_port = get_actual_port()

        json_response(self, {
            "websocket_port": ws_port,
            "websocket_url": f"ws://127.0.0.1:{ws_port}" if ws_port else None,
            "http_port": http_port,
            "websocket_available": ws_port is not None,
        })
        self._log_request(200)

    def _handle_stop_workflow(self, workflow_id: str) -> None:
        """Handle POST /api/workflows/{id}/stop."""
        manager = WorkflowStateManager()
        workflow = manager.get(workflow_id)

        if not workflow:
            error_response(self, f"Workflow not found: {workflow_id}", 404)
            self._log_request(404)
            return

        if workflow.is_finished:
            json_response(self, {
                "success": False,
                "workflow_id": workflow_id,
                "audit_type": workflow.tool_name,
                "message": "Workflow already finished"
            })
            self._log_request(200)
            return

        if workflow.is_cancelled:
            json_response(self, {
                "success": False,
                "workflow_id": workflow_id,
                "audit_type": workflow.tool_name,
                "message": "Workflow already cancelled"
            })
            self._log_request(200)
            return

        success = manager.cancel(workflow_id)
        self.logger.info(f"Audit cancelled via HTTP: {workflow_id} ({workflow.tool_name})")

        json_response(self, {
            "success": success,
            "workflow_id": workflow_id,
            "audit_type": workflow.tool_name,
            "message": "Audit cancelled successfully" if success else "Failed to cancel"
        })
        self._log_request(200)

    def _handle_not_found(self) -> None:
        """Handle 404 Not Found."""
        error_response(self, f"Not found: {self.path}", 404)
        self._log_request(404)
