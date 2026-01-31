"""Unit tests for PrincipalReportGenerator."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.generate_report.generators.principal import PrincipalReportGenerator
from tools.generate_report.models import AuditLens, ReportMetadata
from tools.workflow.state import WorkflowState


@pytest.fixture
def metadata():
    return ReportMetadata(
        lens=AuditLens.PRINCIPAL,
        report_number=1,
        report_path=Path("/tmp/reports/PRINCIPAL_AUDIT_REPORT_1.md"),
        generated_at=datetime(2026, 1, 22, 14, 30, 45),
        project_name="test-project",
    )


@pytest.fixture
def mock_consolidated():
    mock = MagicMock()
    mock.files_checked = {"src/services/user.py", "src/services/auth.py"}
    mock.issues_found = [
        {
            "severity": "critical",
            "category": "complexity",
            "description": "Function exceeds complexity threshold",
            "affected_files": [{"file_path": "src/services/user.py", "function_name": "process_user"}],
            "remediation": "Extract methods",
            "complexity_score": 25,
        },
        {
            "severity": "high",
            "category": "dry_violation",
            "description": "Duplicated validation logic",
            "affected_files": [
                {"file_path": "src/services/user.py"},
                {"file_path": "src/services/auth.py"},
            ],
            "remediation": "Extract to shared validator",
            "similarity_percentage": 85,
        },
    ]
    mock.get_audit_summary.return_value = {
        "total_vulnerabilities": 2,
        "severity_counts": {"critical": 1, "high": 1, "medium": 0, "low": 0, "info": 0},
        "files_examined": 2,
    }
    mock.get_findings_by_severity.return_value = {
        "critical": [mock.issues_found[0]],
        "high": [mock.issues_found[1]],
        "medium": [],
        "low": [],
        "info": [],
    }
    mock.complexity_findings = [mock.issues_found[0]]
    mock.dry_violations = [mock.issues_found[1]]
    mock.relevant_context = {"Architecture: Clean separation of concerns", "Naming: Consistent naming conventions"}
    return mock


@pytest.fixture
def workflow_state(mock_consolidated):
    state = WorkflowState(
        continuation_id="test-uuid",
        tool_name="principal_audit",
    )
    state.consolidated = mock_consolidated
    return state


@pytest.fixture
def generator(metadata, workflow_state):
    return PrincipalReportGenerator(
        lens=AuditLens.PRINCIPAL,
        state=workflow_state,
        metadata=metadata,
    )


class TestPrincipalReportGenerator:
    """Tests for PrincipalReportGenerator."""

    def test_generate_produces_complete_report(self, generator):
        report = generator.generate()
        assert "# PRINCIPAL Audit Report" in report
        assert "Executive Summary" in report
        assert "Code Health Score" in report

    def test_code_health_score_calculation(self, generator):
        section = generator._build_code_health_score()
        assert "Code Health Score" in section
        assert "/ 100" in section

    def test_complexity_hotspots(self, generator):
        section = generator._build_complexity_hotspots()
        assert "Complexity Hotspots" in section
        assert "process_user" in section
        assert "25" in section

    def test_duplication_analysis(self, generator):
        section = generator._build_duplication_analysis()
        assert "Duplication Analysis" in section
        assert "85%" in section

    def test_positive_findings_from_assessments(self, generator):
        section = generator._build_positive_findings()
        assert "Architecture" in section

    def test_report_contains_all_sections(self, generator):
        report = generator.generate()
        assert "## Executive Summary" in report
        assert "## Code Health Score" in report
        assert "## Findings" in report
        assert "## Remediation Priority" in report


class TestPrincipalEmptyReport:
    """Tests for empty principal report."""

    def test_empty_code_health_shows_100(self, metadata):
        state = WorkflowState(continuation_id="test", tool_name="principal_audit")
        state.consolidated = None

        gen = PrincipalReportGenerator(lens=AuditLens.PRINCIPAL, state=state, metadata=metadata)
        section = gen._build_code_health_score()
        assert "100 / 100" in section

    def test_no_complexity_hotspots(self, metadata):
        mock = MagicMock()
        mock.files_checked = set()
        mock.issues_found = []
        mock.complexity_findings = []
        mock.get_audit_summary.return_value = {"severity_counts": {}, "files_examined": 0}
        mock.get_findings_by_severity.return_value = {
            "critical": [], "high": [], "medium": [], "low": [], "info": []
        }
        mock.relevant_context = set()

        state = WorkflowState(continuation_id="test", tool_name="principal_audit")
        state.consolidated = mock

        gen = PrincipalReportGenerator(lens=AuditLens.PRINCIPAL, state=state, metadata=metadata)
        section = gen._build_complexity_hotspots()
        assert section == ""
