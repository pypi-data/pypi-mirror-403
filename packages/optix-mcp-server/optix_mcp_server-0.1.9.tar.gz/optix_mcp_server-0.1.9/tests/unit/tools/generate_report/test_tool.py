"""Unit tests for GenerateReportTool."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.generate_report.models import AuditLens, ReportGenerationError
from tools.generate_report.tool import GenerateReportTool
from tools.workflow.state import WorkflowState, WorkflowStateManager


@pytest.fixture
def tool():
    return GenerateReportTool()


@pytest.fixture
def mock_consolidated():
    mock = MagicMock()
    mock.files_checked = {"src/auth.py", "src/api.py"}
    mock.issues_found = [
        {
            "severity": "critical",
            "category": "SQL Injection",
            "description": "SQL injection vulnerability",
            "affected_files": ["src/api.py"],
            "remediation": "Use parameterized queries",
        },
    ]
    mock.get_audit_summary.return_value = {
        "total_vulnerabilities": 1,
        "severity_counts": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
        "files_examined": 2,
    }
    mock.get_findings_by_severity.return_value = {
        "critical": [mock.issues_found[0]],
        "high": [],
        "medium": [],
        "low": [],
        "info": [],
    }
    mock.relevant_context = set()
    return mock


@pytest.fixture
def finished_workflow_state(mock_consolidated):
    state = WorkflowState(
        continuation_id="test-uuid-finished",
        tool_name="security_audit",
    )
    state.consolidated = mock_consolidated
    state.is_finished = True
    return state


@pytest.fixture
def unfinished_workflow_state(mock_consolidated):
    state = WorkflowState(
        continuation_id="test-uuid-unfinished",
        tool_name="security_audit",
    )
    state.consolidated = mock_consolidated
    state.is_finished = False
    return state


class TestGenerateReportTool:
    """Tests for GenerateReportTool."""

    def test_execute_requires_finished_workflow(self, tool, unfinished_workflow_state):
        tool._state_manager._workflows = {"test-uuid": unfinished_workflow_state}

        result = tool.execute(continuation_id="test-uuid")

        assert isinstance(result, ReportGenerationError)
        assert "WorkflowIncomplete" in result.error_type

    def test_execute_generates_report_for_finished_workflow(
        self, tool, finished_workflow_state
    ):
        with tempfile.TemporaryDirectory() as tmp_dir:
            finished_workflow_state.project_root_path = tmp_dir
            tool._state_manager._workflows = {
                "test-uuid-finished": finished_workflow_state
            }

            result = tool.execute(continuation_id="test-uuid-finished")

            assert result.success is True
            assert "SECURITY_AUDIT_REPORT" in str(result.report_path)
            assert result.lens == AuditLens.SECURITY
            assert result.severity_counts == {
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
            }
            assert result.files_examined == 2

    def test_execute_creates_report_file(self, tool, finished_workflow_state):
        with tempfile.TemporaryDirectory() as tmp_dir:
            finished_workflow_state.project_root_path = tmp_dir
            tool._state_manager._workflows = {
                "test-uuid-finished": finished_workflow_state
            }

            result = tool.execute(continuation_id="test-uuid-finished")

            assert result.success is True
            assert Path(result.report_path).exists()
            content = Path(result.report_path).read_text()
            assert "# SECURITY Audit Report" in content
            assert "Executive Summary" in content

    def test_execute_populates_findings(self, tool, finished_workflow_state):
        with tempfile.TemporaryDirectory() as tmp_dir:
            finished_workflow_state.project_root_path = tmp_dir
            tool._state_manager._workflows = {
                "test-uuid-finished": finished_workflow_state
            }

            result = tool.execute(continuation_id="test-uuid-finished")

            content = Path(result.report_path).read_text()
            assert "SQL injection vulnerability" in content
            assert "parameterized queries" in content

    def test_execute_uses_most_recent_finished(self, tool, mock_consolidated):
        state1 = WorkflowState(
            continuation_id="uuid-1",
            tool_name="security_audit",
        )
        state1.consolidated = mock_consolidated
        state1.is_finished = True
        state1.updated_at = datetime(2026, 1, 1, 10, 0, 0)

        state2 = WorkflowState(
            continuation_id="uuid-2",
            tool_name="security_audit",
        )
        state2.consolidated = mock_consolidated
        state2.is_finished = True
        state2.updated_at = datetime(2026, 1, 2, 10, 0, 0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            state1.project_root_path = tmp_dir
            state2.project_root_path = tmp_dir
            tool._state_manager._workflows = {
                "uuid-1": state1,
                "uuid-2": state2,
            }

            result = tool.execute()

            assert result.success is True

    def test_execute_no_audit_found_error(self, tool):
        tool._state_manager._workflows = {}

        result = tool.execute()

        assert isinstance(result, ReportGenerationError)
        assert "No completed audit found" in result.error


class TestGenerateReportToolWithDifferentLenses:
    """Tests for generating reports with different lens types."""

    @pytest.fixture
    def base_mock_consolidated(self):
        mock = MagicMock()
        mock.files_checked = set()
        mock.issues_found = []
        mock.get_audit_summary.return_value = {
            "severity_counts": {},
            "files_examined": 0,
        }
        mock.get_findings_by_severity.return_value = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }
        mock.relevant_context = set()
        return mock

    def test_security_lens_report(self, tool, base_mock_consolidated):
        state = WorkflowState(continuation_id="test", tool_name="security_audit")
        state.consolidated = base_mock_consolidated
        state.is_finished = True

        with tempfile.TemporaryDirectory() as tmp_dir:
            state.project_root_path = tmp_dir
            tool._state_manager._workflows = {"test": state}

            result = tool.execute(continuation_id="test")

            assert result.success
            assert result.lens == AuditLens.SECURITY
            content = Path(result.report_path).read_text()
            assert "SECURITY Audit Report" in content

    def test_a11y_lens_report(self, tool, base_mock_consolidated):
        state = WorkflowState(continuation_id="test", tool_name="a11y_audit")
        state.consolidated = base_mock_consolidated
        state.is_finished = True

        with tempfile.TemporaryDirectory() as tmp_dir:
            state.project_root_path = tmp_dir
            tool._state_manager._workflows = {"test": state}

            result = tool.execute(continuation_id="test")

            assert result.success
            assert result.lens == AuditLens.A11Y
            content = Path(result.report_path).read_text()
            assert "A11Y Audit Report" in content

    def test_devops_lens_report(self, tool, base_mock_consolidated):
        base_mock_consolidated.get_artifact_coverage_summary = MagicMock(return_value={})
        base_mock_consolidated.get_missing_context_summary = MagicMock(
            return_value={"missing_lockfiles": [], "other_missing_context": []}
        )

        state = WorkflowState(continuation_id="test", tool_name="devops_audit")
        state.consolidated = base_mock_consolidated
        state.is_finished = True

        with tempfile.TemporaryDirectory() as tmp_dir:
            state.project_root_path = tmp_dir
            tool._state_manager._workflows = {"test": state}

            result = tool.execute(continuation_id="test")

            assert result.success
            assert result.lens == AuditLens.DEVOPS
            content = Path(result.report_path).read_text()
            assert "DEVOPS Audit Report" in content

    def test_principal_lens_report(self, tool, base_mock_consolidated):
        base_mock_consolidated.complexity_findings = []
        base_mock_consolidated.dry_violations = []

        state = WorkflowState(continuation_id="test", tool_name="principal_audit")
        state.consolidated = base_mock_consolidated
        state.is_finished = True

        with tempfile.TemporaryDirectory() as tmp_dir:
            state.project_root_path = tmp_dir
            tool._state_manager._workflows = {"test": state}

            result = tool.execute(continuation_id="test")

            assert result.success
            assert result.lens == AuditLens.PRINCIPAL
            content = Path(result.report_path).read_text()
            assert "PRINCIPAL Audit Report" in content
