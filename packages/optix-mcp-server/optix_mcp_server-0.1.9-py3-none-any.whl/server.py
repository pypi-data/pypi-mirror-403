#!/usr/bin/env python3
"""optix-mcp-server - MCP server for source code analysis.

This is the main entry point for the MCP server. It initializes the FastMCP
server and registers all available tools.
"""

from tools.dashboard_info import dashboard_info_impl
from tools.dashboard import start_dashboard_server, get_actual_port, is_dashboard_running
from tools.generate_report.tool import GenerateReportTool
from config.defaults import DashboardConfig, ServerConfiguration
from logging_utils import setup_file_logging, get_tool_logger
from tools.a11y_audit.tool import AccessibilityAuditTool
from tools.security_audit.tool import SecurityAuditTool
from tools.principal_audit.tool import PrincipalAuditTool
from tools.devops_audit.tool import DevOpsAuditTool
from tools.health_check.core import health_check_impl
from tools import register_tool, get_available_tools
from tools.pr_comment.tool import PRCommentTool

from config.defaults import ServerConfiguration
from mcp.server.fastmcp import FastMCP
import json
import logging
import signal
import sys
import time
import webbrowser
from typing import Any, Optional

from pathlib import Path
from dotenv import load_dotenv

# Load .env files: global config first, then local (local overrides global)
global_env = Path.home() / ".optix" / ".env"
if global_env.exists():
    load_dotenv(global_env)
load_dotenv(override=True)
# Server version
__version__ = "0.1.9"

# Global configuration (reloadable)
config: Optional[ServerConfiguration] = None

# Track server start time for uptime calculation
_server_start_time: float = time.time()

# Logger
logger = logging.getLogger(__name__)


def load_configuration() -> ServerConfiguration:
    """Load or reload configuration from environment.

    Returns:
        ServerConfiguration instance

    Raises:
        ValueError: If configuration is invalid
    """
    global config
    try:
        config = ServerConfiguration.from_env()
        logger.info(f"Configuration loaded: server_name={config.server_name}")
        if config.disabled_tools:
            logger.info(f"Disabled tools: {', '.join(config.disabled_tools)}")
        return config
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging based on configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    setup_file_logging()

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )


def handle_sighup(signum: int, frame: Any) -> None:
    """Handle SIGHUP signal to reload configuration.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Received SIGHUP, reloading configuration...")
    try:
        load_configuration()
        logger.info("Configuration reloaded successfully")
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")


def handle_shutdown(signum: int, frame: Any) -> None:
    """Handle shutdown signals (SIGTERM, SIGINT).

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    logger.info(f"Received {signal_name}, shutting down gracefully...")
    sys.exit(0)


def validate_startup() -> bool:
    """Validate server can start with current configuration.

    Returns:
        True if startup validation passes

    Raises:
        RuntimeError: If validation fails
    """
    if config is None:
        raise RuntimeError("Configuration not loaded")

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"E007: Configuration validation failed: {e}")
        raise RuntimeError(f"Invalid configuration: {e}")

    # Log API key status (for future provider integration)
    if config.api_keys:
        providers = config.api_keys.get_configured_providers()
        if providers:
            logger.info(f"API keys configured for: {', '.join(providers)}")
        else:
            logger.warning(
                "No API keys configured. Some tools may be unavailable.")

    # Validate expert analysis configuration
    if config.expert_analysis_enabled:
        if not config.api_keys or not config.api_keys.get_llm_provider_config():
            logger.warning(
                "EXPERT_ANALYSIS_ENABLED=true but no valid LLM provider configured. "
                "Expert analysis will be skipped. Please set OPTIX_LLM_PROVIDER and "
                "corresponding API key (OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY)"
            )
        else:
            llm_config = config.api_keys.get_llm_provider_config()
            logger.info(
                f"Expert analysis enabled using {llm_config.provider} "
                f"(timeout: {config.expert_analysis_timeout}s, "
                f"max findings: {config.expert_analysis_max_findings})"
            )

    return True


# Load initial configuration
config = load_configuration()

# Initialize FastMCP server
mcp = FastMCP(config.server_name)


@mcp.tool()
def health_check() -> str:
    """Check the health status of the MCP server.

    Returns a JSON object containing:
    - status: Server health status (healthy, degraded, unhealthy)
    - server_name: Name of the server
    - version: Server version
    - uptime_seconds: Time since server started
    - tools_available: List of available tool names

    Returns:
        JSON string with health check response
    """
    uptime = time.time() - _server_start_time
    tools = get_available_tools()
    disabled = config.disabled_tools if config else []
    server_name = config.server_name if config else "optix-mcp-server"

    result = health_check_impl(
        server_name=server_name,
        version=__version__,
        uptime_seconds=uptime,
        available_tools=tools,
        disabled_tools=disabled,
    )

    return json.dumps(result, indent=2)


register_tool(
    "health_check",
    impl=health_check_impl,
    description="Check the health status of the MCP server",
)


@mcp.tool()
def open_dashboard() -> str:
    """Open the Optix dashboard in the user's browser.

    This tool opens the dashboard URL in the default browser and returns status info.
    The dashboard is opened automatically - no further action is needed.

    Use this tool when the user wants to:
    - Open the Optix dashboard
    - View the dashboard
    - Access the dashboard UI
    - Launch the dashboard

    Returns:
        JSON string with dashboard status (browser already opened if running)
    """
    dashboard_config = DashboardConfig.from_env()
    actual_port = get_actual_port()
    running = is_dashboard_running()

    result = dashboard_info_impl(
        enabled=dashboard_config.enabled,
        host=dashboard_config.host,
        configured_port=dashboard_config.port,
        actual_port=actual_port,
        is_running=running,
    )

    if running and actual_port:
        url = f"http://{dashboard_config.host}:{actual_port}"
        webbrowser.open(url)
        result["browser_opened"] = True
        result["message"] = f"Dashboard opened in browser at {url}"
    else:
        result["browser_opened"] = False

    return json.dumps(result, indent=2)


register_tool(
    "open_dashboard",
    impl=dashboard_info_impl,
    description="Open the Optix dashboard in the user's browser",
)

_security_audit_tool = SecurityAuditTool()


@mcp.tool()
def security_audit(
    step_number: int,
    next_step_required: bool,
    files_examined: list[str],
    confidence: str,
    continuation_id: str | None = None,
    vulnerabilities_found: list[dict] | None = None,
    security_assessments: dict[str, str] | None = None,
    project_root_path: str | None = None,
) -> str:
    """Perform a guided multi-step security audit of a codebase.

    Returns step-specific guidance and accumulates findings across steps.
    Generates AUDIT.MD report at completion.

    Args:
        step_number: Current step number (1-6)
        next_step_required: Set to false on final step to generate report
        files_examined: List of files examined during this step
        confidence: Confidence level (exploring, low, medium, high, very_high, certain)
        continuation_id: UUID from previous step (omit for step 1)
        vulnerabilities_found: Security findings from this step. Each finding dict must have:
            - severity: str - "critical", "high", "medium", "low", or "info"
            - category: str - Vulnerability type (e.g., "SQL Injection", "XSS", "Authentication Bypass")
            - description: str - Clear description of the vulnerability
            - affected_files: list[str] - File paths affected
            Optional: remediation (str), cwe_id (str, e.g., "CWE-89")
        security_assessments: Domain-specific security assessments
        project_root_path: Optional path to project root for report file generation

    Returns:
        JSON string with audit response
    """
    response = _security_audit_tool.execute(
        step_number=step_number,
        next_step_required=next_step_required,
        files_examined=files_examined,
        confidence=confidence,
        continuation_id=continuation_id,
        findings=json.dumps(
            vulnerabilities_found) if vulnerabilities_found else "",
        vulnerabilities_found=vulnerabilities_found or [],
        security_assessments=security_assessments or {},
        project_root_path=project_root_path,
    )
    return json.dumps(response.to_dict(), indent=2)


register_tool(
    "security_audit",
    impl=_security_audit_tool.execute,
    description="Perform a guided multi-step security audit of a codebase",
)

_a11y_audit_tool = AccessibilityAuditTool()


@mcp.tool()
def a11y_audit(
    step_number: int,
    next_step_required: bool,
    files_examined: list[str],
    confidence: str,
    continuation_id: str | None = None,
    accessibility_findings: list[dict] | None = None,
    accessibility_assessments: dict[str, str] | None = None,
    project_root_path: str | None = None,
) -> str:
    """Perform step-by-step UI accessibility audit.
       SHOULD BE execute only in FrontEnd Projects

    Returns structured guidance for accessibility analysis including
    ARIA labels, keyboard navigation, focus management, color contrast,
    and semantic HTML checks aligned with WCAG 2.1/2.2.

    Steps:
    1. Structural Analysis & Discovery
    2. ARIA Labels & Attributes
    3. Keyboard Navigation
    4. Focus Management
    5. Visual Accessibility & Color Contrast
    6. Semantic HTML & WCAG Compliance

    Args:
        step_number: Current step number (1-6)
        continuation_id: UUID from previous step (omit for step 1)
        next_step_required: Set to false on final step to generate report
        files_examined: List of file paths examined
        accessibility_findings: Accessibility findings from this step. Each finding dict must have:
            - severity: str - "critical", "high", "medium", "low", or "info"
            - wcag_criterion: str - WCAG criterion in format "X.X.X" (e.g., "1.1.1", "2.1.1")
            - category: str - "ARIA", "Keyboard", "Contrast", "Semantic", or "Focus"
            - description: str - Clear description of accessibility barrier
            - affected_files: list[str] - Files with the issue
            - affected_elements: list[str] - HTML elements involved (e.g., ["button.primary"])
            - remediation: str - How to fix the issue
            - wcag_level: str - "A", "AA", or "AAA"
        accessibility_assessments: Positive accessibility observations by domain (e.g., {"ARIA": "Good landmark usage", "Keyboard": "Proper tab order"})
        confidence: Client-reported confidence level
        project_root_path: Optional path to project root for report file generation

    Returns:
        JSON string with audit response
    """
    step_names = {
        1: "Structural Analysis & Discovery",
        2: "ARIA Labels & Attributes",
        3: "Keyboard Navigation",
        4: "Focus Management",
        5: "Visual Accessibility & Color Contrast",
        6: "Semantic HTML & WCAG Compliance",
    }

    response = _a11y_audit_tool.execute(
        step=step_names.get(step_number, f"Step {step_number}"),
        step_number=step_number,
        total_steps=6,
        next_step_required=next_step_required,
        files_examined=files_examined,
        confidence=confidence,
        continuation_id=continuation_id,
        findings=json.dumps(
            accessibility_findings) if accessibility_findings else "",
        accessibility_findings=accessibility_findings or [],
        accessibility_assessments=accessibility_assessments or {},
        project_root_path=project_root_path,
    )
    return json.dumps(response.to_dict(), indent=2)


register_tool(
    "a11y_audit",
    impl=_a11y_audit_tool.execute,
    description="Perform a guided multi-step UI accessibility audit",
)

_devops_audit_tool = DevOpsAuditTool()


@mcp.tool()
def devops_audit(
    step_number: int,
    next_step_required: bool,
    files_examined: list[str],
    confidence: str,
    continuation_id: str | None = None,
    project_root_path: str | None = None,
    devops_issues_found: list[dict] | None = None,
    devops_assessments: dict[str, str] | None = None,
    artifacts_analyzed: dict | None = None,
    missing_context: list[str] | None = None,
) -> str:
    """Perform a guided multi-step DevOps audit of a codebase.

    Returns step-specific guidance and accumulates findings across steps.
    Generates DEVOPS_AUDIT_REPORT.md at completion.

    Args:
        step_number: Current step number (1-4)
        next_step_required: Set to false on final step to generate report
        files_examined: List of files examined during this step
        confidence: Confidence level (exploring, low, medium, high, very_high, certain)
        continuation_id: UUID from previous step (omit for step 1)
        project_root_path: Absolute path to project root (step 1 only)
        devops_issues_found: DevOps findings from this step. Each finding dict must have:
            - category: str - "dockerfile", "cicd", or "dependency"
            - severity: str - "critical", "high", "medium", "low", or "info"
            - description: str - Clear issue description
            - affected_files: list[str] - Files affected (must have at least one)
            Optional: remediation (str), line_numbers (list[int]), confidence (str)
        devops_assessments: Positive DevOps observations by domain (e.g., {"Docker": "Multi-stage builds used", "CI/CD": "Least-privilege permissions"})
        artifacts_analyzed: Analyzed vs omitted artifacts. Each finding dict must have:
            - dockerfiles: dict with "analyzed" (list[str]) and "omitted" (list[str])
            - workflows: dict with "analyzed" (list[str]) and "omitted" (list[str])
            - package_files: dict with "analyzed" (list[str]) and "omitted" (list[str])
        missing_context: Requested but not provided files

    Returns:
        JSON string with DevOps audit response
    """
    response = _devops_audit_tool.execute(
        step_number=step_number,
        next_step_required=next_step_required,
        files_examined=files_examined,
        confidence=confidence,
        continuation_id=continuation_id,
        findings=json.dumps(
            devops_issues_found) if devops_issues_found else "",
        project_root_path=project_root_path,
        devops_issues_found=devops_issues_found or [],
        devops_assessments=devops_assessments or {},
        artifacts_analyzed=artifacts_analyzed or {},
        missing_context=missing_context or [],
    )
    return json.dumps(response.to_dict(), indent=2)


register_tool(
    "devops_audit",
    impl=_devops_audit_tool.execute,
    description="Perform a guided multi-step DevOps audit of a codebase",
)

_principal_audit_tool = PrincipalAuditTool()


@mcp.tool()
def principal_audit(
    step_number: int,
    next_step_required: bool,
    files_examined: list[str],
    confidence: str,
    continuation_id: str | None = None,
    principal_findings: list[dict] | None = None,
    principal_assessments: dict[str, str] | None = None,
    project_root_path: str | None = None,
) -> str:
    """Perform a guided multi-step Principal Engineer audit of a codebase.

    Returns step-specific guidance and accumulates findings across steps.
    Generates PRINCIPAL_AUDIT_REPORT.md at completion.

    Steps:
    1. Complexity Analysis - Cyclomatic complexity detection
    2. DRY Violation Detection - Code duplication analysis
    3. Coupling Analysis - Module dependencies and coupling metrics
    4. Separation of Concerns - Responsibility mixing detection
    5. Maintainability Assessment - General maintainability + report

    Args:
        step_number: Current step number (1-5)
        next_step_required: Set to false on final step to generate report
        files_examined: List of files examined during this step
        confidence: Confidence level (exploring, low, medium, high, very_high, certain)
        continuation_id: UUID from previous step (omit for step 1)
        principal_findings: Code quality findings from this step. Each finding dict must have:
            - category: str - "complexity", "dry_violation", "coupling", "separation_of_concerns", or "maintainability_risk"
            - severity: str - "critical", "high", "medium", or "low"
            - description: str - Clear description of the issue
            - affected_files: list[dict] - Files affected, each with "file_path" (required), and optional "line_start", "line_end", "function_name"
            - remediation: str - Recommended fix or refactoring approach
            - confidence: str - "exploring", "low", "medium", "high", "very_high", or "certain"
            Optional fields: complexity_score (float), similarity_percentage (float), coupling_metrics (dict)
        principal_assessments: Positive code quality observations by domain (e.g., {"Architecture": "Clean layer separation", "Coupling": "Low module coupling"})
        project_root_path: Absolute path to project root (step 1 only)

    Returns:
        JSON string with Principal audit response
    """
    response = _principal_audit_tool.execute(
        step_number=step_number,
        next_step_required=next_step_required,
        files_examined=files_examined,
        confidence=confidence,
        continuation_id=continuation_id,
        findings=json.dumps(principal_findings) if principal_findings else "",
        principal_findings=principal_findings or [],
        principal_assessments=principal_assessments or {},
        project_root_path=project_root_path,
    )
    return json.dumps(response.to_dict(), indent=2)


register_tool(
    "principal_audit",
    impl=_principal_audit_tool.execute,
    description="Perform a guided multi-step Principal Engineer audit of a codebase",
)

_generate_report_tool = GenerateReportTool()


@mcp.tool()
def generate_report(
    continuation_id: str | None = None,
) -> str:
    """Generate a standardized audit report template.

    Creates a numbered markdown file in the reports directory with placeholder
    sections for the AI client to populate with audit findings.

    Args:
        continuation_id: Optional UUID from completed audit workflow.
            If omitted, uses the most recent workflow from WorkflowStateManager.

    Returns:
        JSON string with report generation response
    """
    response = _generate_report_tool.execute(
        continuation_id=continuation_id,
    )
    return json.dumps(response.to_dict(), indent=2)


register_tool(
    "generate_report",
    impl=_generate_report_tool.execute,
    description="Generate a standardized audit report template based on the last executed audit lens",
)

_pr_comment_tool = PRCommentTool()


@mcp.tool()
def pr_comment(
    pr_number: int | None = None,
    continuation_id: str | None = None,
    include_file_links: bool = False,
    repo: str | None = None,
) -> str:
    """Post audit findings as a PR comment.

    Posts findings from a completed audit workflow as a formatted comment
    on a GitHub Pull Request. If no pr_number is provided, lists the last
    5 open PRs for selection.

    Args:
        pr_number: GitHub PR number to comment on. If omitted, returns
            a list of recent PRs to choose from.
        continuation_id: Optional UUID from completed audit workflow.
            If omitted, uses the most recent workflow from WorkflowStateManager.
        include_file_links: Add GitHub permalinks to file references
        repo: Repository (owner/repo), auto-detected if omitted

    Returns:
        JSON string with PR list (if no pr_number) or comment response
    """
    response = _pr_comment_tool.execute(
        pr_number=pr_number,
        continuation_id=continuation_id,
        include_file_links=include_file_links,
        repo=repo,
    )
    return json.dumps(response.to_dict(), indent=2)


register_tool(
    "pr_comment",
    impl=_pr_comment_tool.execute,
    description="Post audit findings as a PR comment",
)


def main() -> None:
    """Run the MCP server."""
    setup_logging(config.log_level.value if config else "INFO")

    signal.signal(signal.SIGHUP, handle_sighup)
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        validate_startup()
    except RuntimeError as e:
        logger.error(f"Startup validation failed: {e}")
        sys.exit(7)

    from logging_utils.config import get_log_config
    log_config = get_log_config()

    logger.info(f"Starting {config.server_name} v{__version__}")
    logger.info(f"Transport: {config.transport.value}")
    logger.info(f"Log file: {log_config.log_file_path}")

    dashboard_config = DashboardConfig.from_env()
    if dashboard_config.enabled:
        start_dashboard_server(dashboard_config)

    transport = config.transport.value
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
