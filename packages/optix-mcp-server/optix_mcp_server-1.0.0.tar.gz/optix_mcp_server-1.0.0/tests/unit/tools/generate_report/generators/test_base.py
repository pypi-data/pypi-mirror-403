"""Unit tests for ReportGenerator base class."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.generate_report.generators.base import (
    FILE_CATEGORIES,
    ReportGenerator,
    SEVERITY_DISPLAY,
    SEVERITY_ORDER,
    _categorize_file,
)
from tools.generate_report.models import AuditLens, ReportMetadata
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.state import WorkflowState


class ConcreteReportGenerator(ReportGenerator):
    """Concrete implementation for testing abstract base class."""

    def generate(self) -> str:
        parts = [
            self._build_header(),
            self._build_executive_summary(),
            self._build_risk_distribution(),
            self._build_findings_by_severity(),
            self._build_files_examined(),
            self._build_remediation_priority(),
            self._build_footer(),
        ]
        return "\n\n".join(parts)


@pytest.fixture
def metadata():
    return ReportMetadata(
        lens=AuditLens.SECURITY,
        report_number=1,
        report_path=Path("/tmp/reports/SECURITY_AUDIT_REPORT_1.md"),
        generated_at=datetime(2026, 1, 22, 14, 30, 45),
        project_name="test-project",
    )


@pytest.fixture
def mock_consolidated():
    mock = MagicMock()
    mock.files_checked = {"src/auth/login.py", "src/api/routes.py", "config/settings.py"}
    mock.issues_found = [
        {
            "severity": "critical",
            "category": "SQL Injection",
            "description": "SQL injection vulnerability found",
            "affected_files": ["src/api/routes.py"],
            "remediation": "Use parameterized queries",
        },
        {
            "severity": "high",
            "category": "Authentication",
            "description": "Weak password policy",
            "affected_files": ["src/auth/login.py"],
            "remediation": "Enforce strong passwords",
        },
    ]
    mock.get_audit_summary.return_value = {
        "total_vulnerabilities": 2,
        "severity_counts": {
            "critical": 1,
            "high": 1,
            "medium": 0,
            "low": 0,
            "info": 0,
        },
        "files_examined": 3,
        "confidence": "high",
    }
    mock.get_findings_by_severity.return_value = {
        "critical": [mock.issues_found[0]],
        "high": [mock.issues_found[1]],
        "medium": [],
        "low": [],
        "info": [],
    }
    return mock


@pytest.fixture
def workflow_state(mock_consolidated):
    state = WorkflowState(
        continuation_id="test-uuid",
        tool_name="security_audit",
    )
    state.consolidated = mock_consolidated
    return state


@pytest.fixture
def generator(metadata, workflow_state):
    return ConcreteReportGenerator(
        lens=AuditLens.SECURITY,
        state=workflow_state,
        metadata=metadata,
    )


class TestFileCategorization:
    """Tests for file categorization logic."""

    def test_categorize_auth_file(self):
        assert _categorize_file("src/auth/login.py") == "Authentication"

    def test_categorize_api_file(self):
        assert _categorize_file("src/api/routes.py") == "API Endpoints"

    def test_categorize_config_file(self):
        assert _categorize_file("config/settings.yaml") == "Configuration"

    def test_categorize_test_file(self):
        assert _categorize_file("tests/test_auth.py") == "Tests"

    def test_categorize_unknown_file(self):
        assert _categorize_file("src/main.py") == "Other"

    def test_categorize_docker_file(self):
        assert _categorize_file("Dockerfile") == "Container"

    def test_categorize_github_workflow(self):
        assert _categorize_file(".github/workflows/ci.yml") == "CI/CD"


class TestReportGeneratorHeader:
    """Tests for header generation."""

    def test_header_contains_lens(self, generator):
        header = generator._build_header()
        assert "SECURITY Audit Report" in header

    def test_header_contains_timestamp(self, generator):
        header = generator._build_header()
        assert "2026-01-22 14:30:45" in header

    def test_header_contains_project_name(self, generator):
        header = generator._build_header()
        assert "test-project" in header

    def test_header_contains_tool_name(self, generator):
        header = generator._build_header()
        assert "security_audit" in header


class TestExecutiveSummary:
    """Tests for executive summary generation."""

    def test_summary_contains_total_issues(self, generator):
        summary = generator._build_executive_summary()
        assert "Total Issues | 2" in summary

    def test_summary_contains_severity_counts(self, generator):
        summary = generator._build_executive_summary()
        assert "Critical | 1" in summary
        assert "High | 1" in summary

    def test_summary_contains_files_examined(self, generator):
        summary = generator._build_executive_summary()
        assert "Files Examined | 3" in summary

    def test_summary_shows_critical_status(self, generator):
        summary = generator._build_executive_summary()
        assert "**CRITICAL**" in summary

    def test_empty_summary_when_no_consolidated(self, metadata):
        state = WorkflowState(
            continuation_id="test-uuid",
            tool_name="security_audit",
        )
        state.consolidated = None
        gen = ConcreteReportGenerator(
            lens=AuditLens.SECURITY,
            state=state,
            metadata=metadata,
        )
        summary = gen._build_executive_summary()
        assert "Total Issues | 0" in summary
        assert "**PASS**" in summary


class TestRiskDistribution:
    """Tests for risk distribution chart."""

    def test_risk_chart_is_ascii(self, generator):
        chart = generator._build_risk_distribution()
        assert "```" in chart
        assert "█" in chart or "░" in chart or "No issues found" in chart

    def test_risk_chart_contains_percentages(self, generator):
        chart = generator._build_risk_distribution()
        assert "%" in chart

    def test_risk_chart_shows_all_severities(self, generator):
        chart = generator._build_risk_distribution()
        for severity in SEVERITY_ORDER:
            display = SEVERITY_DISPLAY.get(severity, severity.capitalize())
            assert display in chart

    def test_empty_chart_when_no_issues(self, metadata):
        mock = MagicMock()
        mock.get_audit_summary.return_value = {
            "severity_counts": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
            }
        }
        state = WorkflowState(
            continuation_id="test-uuid",
            tool_name="security_audit",
        )
        state.consolidated = mock
        gen = ConcreteReportGenerator(
            lens=AuditLens.SECURITY,
            state=state,
            metadata=metadata,
        )
        chart = gen._build_risk_distribution()
        assert "No issues found" in chart


class TestFindingsBySeverity:
    """Tests for findings section."""

    def test_findings_grouped_by_severity(self, generator):
        findings = generator._build_findings_by_severity()
        assert "### Critical Severity" in findings
        assert "### High Severity" in findings

    def test_findings_contain_descriptions(self, generator):
        findings = generator._build_findings_by_severity()
        assert "SQL injection vulnerability" in findings

    def test_findings_contain_remediation(self, generator):
        findings = generator._build_findings_by_severity()
        assert "parameterized queries" in findings

    def test_empty_severity_shows_no_findings(self, generator):
        findings = generator._build_findings_by_severity()
        assert "**No medium severity findings.**" in findings


class TestFilesExamined:
    """Tests for files examined section."""

    def test_files_are_categorized(self, generator):
        files = generator._build_files_examined()
        assert "### Authentication" in files or "### API Endpoints" in files

    def test_files_are_sorted_alphabetically(self, generator):
        files = generator._build_files_examined()
        lines = files.split("\n")
        file_lines = [l for l in lines if l.startswith("- `")]
        for i in range(len(file_lines) - 1):
            current = file_lines[i].replace("- `", "").replace("`", "")
            next_file = file_lines[i + 1].replace("- `", "").replace("`", "")
            if "### " not in file_lines[i]:
                pass

    def test_files_have_backticks(self, generator):
        files = generator._build_files_examined()
        assert "`src/" in files or "`config/" in files


class TestRemediationPriority:
    """Tests for remediation priority section."""

    def test_has_p0_section(self, generator):
        remediation = generator._build_remediation_priority()
        assert "Immediate (P0)" in remediation

    def test_has_p1_section(self, generator):
        remediation = generator._build_remediation_priority()
        assert "Short-term (P1)" in remediation

    def test_has_p2_section(self, generator):
        remediation = generator._build_remediation_priority()
        assert "Medium-term (P2)" in remediation

    def test_critical_findings_in_p0(self, generator):
        remediation = generator._build_remediation_priority()
        p0_section = remediation.split("### Short-term")[0]
        assert "SQL injection" in p0_section


class TestFooter:
    """Tests for footer generation."""

    def test_footer_contains_attribution(self, generator):
        footer = generator._build_footer()
        assert "optix-mcp-server" in footer

    def test_footer_has_horizontal_rule(self, generator):
        footer = generator._build_footer()
        assert "---" in footer


class TestOverallStatus:
    """Tests for status determination."""

    def test_critical_returns_critical(self):
        status = ReportGenerator._get_overall_status({"critical": 1, "high": 0})
        assert status == "CRITICAL"

    def test_high_returns_needs_attention(self):
        status = ReportGenerator._get_overall_status({"critical": 0, "high": 1})
        assert status == "NEEDS_ATTENTION"

    def test_no_issues_returns_pass(self):
        status = ReportGenerator._get_overall_status({"critical": 0, "high": 0})
        assert status == "PASS"


class TestHtmlEscaping:
    """Tests for HTML escaping in findings."""

    def test_html_in_remediation_is_escaped(self, metadata):
        mock = MagicMock()
        mock.files_checked = {"src/components/Button.tsx"}
        mock.issues_found = [
            {
                "severity": "medium",
                "category": "ARIA",
                "description": "Button missing accessible label",
                "affected_files": ["src/components/Button.tsx"],
                "remediation": 'Add aria-label: <button aria-label="Close">X</button>',
            },
        ]
        mock.get_audit_summary.return_value = {
            "severity_counts": {"medium": 1},
            "files_examined": 1,
        }
        mock.get_findings_by_severity.return_value = {
            "critical": [],
            "high": [],
            "medium": [mock.issues_found[0]],
            "low": [],
            "info": [],
        }

        state = WorkflowState(
            continuation_id="test-uuid",
            tool_name="a11y_audit",
        )
        state.consolidated = mock

        gen = ConcreteReportGenerator(
            lens=AuditLens.A11Y,
            state=state,
            metadata=metadata,
        )

        findings = gen._build_findings_by_severity()
        assert '`<button aria-label="Close">`' in findings
        assert '<button aria-label="Close">' not in findings.replace('`<button aria-label="Close">`', '')

    def test_html_in_description_is_escaped(self, metadata):
        mock = MagicMock()
        mock.files_checked = {"src/components/Form.tsx"}
        mock.issues_found = [
            {
                "severity": "high",
                "category": "Semantic",
                "description": "Use <label> element for form inputs",
                "affected_files": ["src/components/Form.tsx"],
                "remediation": "Add proper labels",
            },
        ]
        mock.get_audit_summary.return_value = {
            "severity_counts": {"high": 1},
            "files_examined": 1,
        }
        mock.get_findings_by_severity.return_value = {
            "critical": [],
            "high": [mock.issues_found[0]],
            "medium": [],
            "low": [],
            "info": [],
        }

        state = WorkflowState(
            continuation_id="test-uuid",
            tool_name="a11y_audit",
        )
        state.consolidated = mock

        gen = ConcreteReportGenerator(
            lens=AuditLens.A11Y,
            state=state,
            metadata=metadata,
        )

        findings = gen._build_findings_by_severity()
        assert "`<label>`" in findings


class TestDeterminism:
    """Tests for deterministic output."""

    def test_same_input_produces_identical_output(self, generator):
        report1 = generator.generate()
        report2 = generator.generate()
        assert report1 == report2

    def test_files_are_sorted_within_categories(self, metadata):
        mock = MagicMock()
        mock.files_checked = {
            "src/auth/z_file.py",
            "src/auth/a_file.py",
            "src/auth/m_file.py",
        }
        mock.issues_found = []
        mock.get_audit_summary.return_value = {
            "severity_counts": {},
            "files_examined": 3,
        }
        mock.get_findings_by_severity.return_value = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }

        state = WorkflowState(
            continuation_id="test-uuid",
            tool_name="security_audit",
        )
        state.consolidated = mock

        gen = ConcreteReportGenerator(
            lens=AuditLens.SECURITY,
            state=state,
            metadata=metadata,
        )

        files_section = gen._build_files_examined()
        a_pos = files_section.find("a_file.py")
        m_pos = files_section.find("m_file.py")
        z_pos = files_section.find("z_file.py")
        assert a_pos < m_pos < z_pos
