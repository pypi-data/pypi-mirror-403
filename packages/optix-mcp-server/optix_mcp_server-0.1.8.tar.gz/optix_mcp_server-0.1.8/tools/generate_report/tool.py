"""MCP tool implementation for generate_report.

Provides the main tool logic for generating complete
audit reports based on completed audit workflows.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from tools.generate_report.file_operations import atomic_write_file, create_reports_directory
from tools.generate_report.generators import GENERATOR_MAP
from tools.generate_report.models import (
    AuditLens,
    ReportGenerationError,
    ReportGenerationResponse,
    ReportMetadata,
)
from tools.generate_report.numbering import allocate_report_number
from tools.workflow.state import WorkflowStateManager


class GenerateReportTool:
    """MCP tool for generating complete audit reports."""

    def __init__(self) -> None:
        """Initialize the report generation tool."""
        self._state_manager = WorkflowStateManager()

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "generate_report"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return (
            "Generate a complete audit report from WorkflowState data. "
            "Creates a numbered markdown file in the reports directory with "
            "all findings programmatically populated. No post-processing required."
        )

    def execute(
        self,
        continuation_id: Optional[str] = None,
    ) -> ReportGenerationResponse | ReportGenerationError:
        """Execute the report generation tool.

        Args:
            continuation_id: Optional UUID of specific workflow to use.
                If omitted, uses most recent workflow from WorkflowStateManager.

        Returns:
            ReportGenerationResponse on success, ReportGenerationError on failure
        """
        try:
            state, lens, project_root = self._get_audit_context(continuation_id)

            if not state.is_finished:
                return ReportGenerationError(
                    error="Workflow must be completed (is_finished=true) before generating report",
                    error_type="WorkflowIncomplete",
                )

            reports_dir = create_reports_directory(project_root)
            report_number, report_path = allocate_report_number(reports_dir, lens)

            metadata = ReportMetadata(
                lens=lens,
                report_number=report_number,
                report_path=report_path,
                generated_at=datetime.now(),
                project_name=project_root.name,
            )

            generator_class = GENERATOR_MAP.get(lens)
            if generator_class is None:
                return ReportGenerationError(
                    error=f"No generator found for lens: {lens.value}",
                    error_type="UnknownLens",
                )

            generator = generator_class(
                lens=lens,
                state=state,
                metadata=metadata,
            )
            content = generator.generate()

            atomic_write_file(report_path, content)

            summary = state.consolidated.get_audit_summary() if state.consolidated else {}
            severity_counts = summary.get("severity_counts", {})
            files_examined = summary.get("files_examined", 0)

            return ReportGenerationResponse(
                success=True,
                report_path=report_path,
                report_number=report_number,
                lens=lens,
                message=f"Report generated successfully at: {report_path}",
                severity_counts=severity_counts,
                files_examined=files_examined,
            )

        except ValueError as e:
            error_msg = str(e)
            if "Unknown tool name" in error_msg:
                return ReportGenerationError(
                    error=error_msg,
                    error_type="UnknownLens",
                )
            if "No completed audit" in error_msg or "No audit workflow" in error_msg:
                return ReportGenerationError(
                    error=error_msg,
                    error_type="NoAuditFound",
                )
            return ReportGenerationError(
                error=error_msg,
                error_type="GeneralError",
            )

        except PermissionError as e:
            return ReportGenerationError(
                error=str(e),
                error_type="PermissionDenied",
            )

        except RuntimeError as e:
            error_msg = str(e)
            if "retry attempts" in error_msg.lower():
                return ReportGenerationError(
                    error=error_msg,
                    error_type="RetryExhausted",
                )
            return ReportGenerationError(
                error=error_msg,
                error_type="GeneralError",
            )

        except OSError as e:
            return ReportGenerationError(
                error=f"File system error: {e}",
                error_type="FileSystemError",
            )

        except Exception as e:
            print(f"[ERROR] Unexpected error in generate_report: {e}", file=sys.stderr)
            return ReportGenerationError(
                error=f"Unexpected error: {e}",
                error_type="GeneralError",
            )

    def _get_audit_context(
        self, continuation_id: Optional[str]
    ) -> tuple["WorkflowState", AuditLens, Path]:
        """Retrieve workflow state, audit lens and project root from WorkflowStateManager.

        Args:
            continuation_id: Optional specific workflow ID to use

        Returns:
            Tuple of (WorkflowState, AuditLens, project_root Path)

        Raises:
            ValueError: If no audit found or invalid tool name
        """
        from tools.workflow.state import WorkflowState

        if continuation_id:
            state = self._state_manager.get(continuation_id)
            if state is None:
                raise ValueError(
                    f"No audit workflow found with continuation_id: {continuation_id}. "
                    "Please ensure you completed an audit workflow first."
                )
        else:
            state = self._get_most_recent_finished()
            if state is None:
                workflows = self._state_manager._workflows
                if not workflows:
                    raise ValueError(
                        "No completed audit found. Please run an audit "
                        "(security_audit, a11y_audit, principal_audit, or devops_audit) "
                        "before generating a report"
                    )
                state = max(
                    workflows.values(),
                    key=lambda w: (w.updated_at, -w.created_at.timestamp()),
                )

        tool_name = state.tool_name
        lens = AuditLens.from_tool_name(tool_name)

        if state.project_root_path:
            project_root = Path(state.project_root_path)
        else:
            project_root = Path.cwd()

        return state, lens, project_root

    def _get_most_recent_finished(self) -> Optional["WorkflowState"]:
        """Get the most recently finished workflow.

        Returns:
            Most recent finished WorkflowState, or None if none found
        """
        workflows = self._state_manager._workflows
        finished = [w for w in workflows.values() if w.is_finished]
        if not finished:
            return None
        return max(finished, key=lambda w: w.updated_at)
