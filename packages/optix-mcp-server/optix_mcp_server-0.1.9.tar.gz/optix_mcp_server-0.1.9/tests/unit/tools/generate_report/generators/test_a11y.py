"""Unit tests for A11yReportGenerator."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.generate_report.generators.a11y import A11yReportGenerator
from tools.generate_report.models import AuditLens, ReportMetadata
from tools.workflow.state import WorkflowState


@pytest.fixture
def metadata():
    return ReportMetadata(
        lens=AuditLens.A11Y,
        report_number=1,
        report_path=Path("/tmp/reports/A11Y_AUDIT_REPORT_1.md"),
        generated_at=datetime(2026, 1, 22, 14, 30, 45),
        project_name="test-project",
    )


@pytest.fixture
def mock_consolidated():
    mock = MagicMock()
    mock.files_checked = {"src/components/Button.tsx", "src/pages/Home.tsx"}
    mock.issues_found = [
        {
            "severity": "critical",
            "category": "ARIA",
            "description": "Missing aria-label on button",
            "affected_files": ["src/components/Button.tsx"],
            "wcag_criterion": "1.1.1",
            "wcag_level": "A",
            "remediation": "Add aria-label attribute",
        },
        {
            "severity": "high",
            "category": "Keyboard",
            "description": "Focus trap in modal",
            "affected_files": ["src/components/Modal.tsx"],
            "wcag_criterion": "2.1.2",
            "wcag_level": "A",
            "remediation": "Implement focus management",
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
    mock.relevant_context = {"Landmarks: Good use of main/nav roles", "Color Contrast: Passes AA"}
    return mock


@pytest.fixture
def workflow_state(mock_consolidated):
    state = WorkflowState(
        continuation_id="test-uuid",
        tool_name="a11y_audit",
    )
    state.consolidated = mock_consolidated
    return state


@pytest.fixture
def generator(metadata, workflow_state):
    return A11yReportGenerator(
        lens=AuditLens.A11Y,
        state=workflow_state,
        metadata=metadata,
    )


class TestA11yReportGenerator:
    """Tests for A11yReportGenerator."""

    def test_generate_produces_complete_report(self, generator):
        report = generator.generate()
        assert "# A11Y Audit Report" in report
        assert "Executive Summary" in report
        assert "WCAG Compliance Matrix" in report

    def test_wcag_compliance_matrix(self, generator):
        section = generator._build_wcag_compliance_matrix()
        assert "WCAG Compliance Matrix" in section
        assert "Level | Passed | Failed" in section

    def test_issue_distribution_shows_categories(self, generator):
        section = generator._build_issue_distribution()
        assert "ARIA" in section
        assert "Keyboard" in section

    def test_wcag_criterion_coverage(self, generator):
        section = generator._build_wcag_criterion_coverage()
        assert "1.1.1" in section
        assert "2.1.2" in section

    def test_positive_findings_from_assessments(self, generator):
        section = generator._build_positive_findings()
        assert "Positive Findings" in section
        assert "Landmarks" in section

    def test_report_contains_all_sections(self, generator):
        report = generator.generate()
        assert "## Executive Summary" in report
        assert "## WCAG Compliance Matrix" in report
        assert "## Issue Distribution" in report
        assert "## Findings" in report


class TestA11yHtmlEscaping:
    """Tests for HTML escaping in a11y reports."""

    def test_positive_findings_escapes_html_tags(self, metadata):
        mock = MagicMock()
        mock.files_checked = set()
        mock.issues_found = []
        mock.get_audit_summary.return_value = {"severity_counts": {}, "files_examined": 0}
        mock.get_findings_by_severity.return_value = {
            "critical": [], "high": [], "medium": [], "low": [], "info": []
        }
        mock.relevant_context = {
            "Semantic HTML: Layout uses proper <main> element",
            "Navigation: Sidenav uses <nav> and <ul>/<li> structure",
        }

        state = WorkflowState(continuation_id="test", tool_name="a11y_audit")
        state.consolidated = mock

        gen = A11yReportGenerator(lens=AuditLens.A11Y, state=state, metadata=metadata)
        section = gen._build_positive_findings()

        assert "`<main>`" in section
        assert "`<nav>`" in section
        assert "`<ul>`" in section
        assert "`<li>`" in section
        assert "<main>" not in section.replace("`<main>`", "")


class TestA11yEmptyReport:
    """Tests for empty a11y report."""

    def test_empty_wcag_matrix(self, metadata):
        state = WorkflowState(continuation_id="test", tool_name="a11y_audit")
        state.consolidated = None

        gen = A11yReportGenerator(lens=AuditLens.A11Y, state=state, metadata=metadata)
        section = gen._build_wcag_compliance_matrix()
        assert "No WCAG data available" in section
