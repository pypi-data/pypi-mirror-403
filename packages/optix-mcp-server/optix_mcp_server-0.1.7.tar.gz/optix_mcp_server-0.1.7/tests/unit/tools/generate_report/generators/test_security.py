"""Unit tests for SecurityReportGenerator."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.generate_report.generators.security import SecurityReportGenerator
from tools.generate_report.models import AuditLens, ReportMetadata
from tools.workflow.state import WorkflowState


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
    mock.files_checked = {"src/auth/login.py", "src/api/routes.py"}
    mock.issues_found = [
        {
            "severity": "critical",
            "category": "SQL Injection",
            "description": "SQL injection in user query",
            "affected_files": ["src/api/routes.py"],
            "remediation": "Use parameterized queries",
            "cwe_id": "CWE-89",
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
    mock.relevant_context = {"Encryption: Using AES-256", "Input Validation: Proper sanitization"}
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
    return SecurityReportGenerator(
        lens=AuditLens.SECURITY,
        state=workflow_state,
        metadata=metadata,
    )


class TestSecurityReportGenerator:
    """Tests for SecurityReportGenerator."""

    def test_generate_produces_complete_report(self, generator):
        report = generator.generate()
        assert "# SECURITY Audit Report" in report
        assert "Executive Summary" in report
        assert "Findings" in report
        assert "Vulnerability Distribution" in report

    def test_vulnerability_distribution_shows_categories(self, generator):
        section = generator._build_vulnerability_distribution()
        assert "SQL Injection" in section
        assert "Authentication" in section

    def test_cwe_references_shows_cwe_ids(self, generator):
        section = generator._build_cwe_references()
        assert "CWE-89" in section

    def test_cwe_references_shows_category_severity_count(self, generator):
        section = generator._build_cwe_references()
        assert "| CWE ID | Category | Severity | Count |" in section
        assert "| CWE-89 | SQL Injection | critical | 1 |" in section

    def test_cwe_references_aggregates_duplicates_with_highest_severity(self, metadata):
        mock = MagicMock()
        mock.issues_found = [
            {"cwe_id": "CWE-79", "category": "XSS", "severity": "low"},
            {"cwe_id": "CWE-79", "category": "XSS", "severity": "critical"},
            {"cwe_id": "CWE-79", "category": "XSS", "severity": "medium"},
        ]
        mock.files_checked = set()
        mock.get_audit_summary.return_value = {"severity_counts": {}, "files_examined": 0}
        mock.get_findings_by_severity.return_value = {"critical": [], "high": [], "medium": [], "low": [], "info": []}
        mock.relevant_context = set()

        state = WorkflowState(continuation_id="test", tool_name="security_audit")
        state.consolidated = mock

        gen = SecurityReportGenerator(lens=AuditLens.SECURITY, state=state, metadata=metadata)
        section = gen._build_cwe_references()
        assert "| CWE-79 | XSS | critical | 3 |" in section

    def test_positive_findings_from_assessments(self, generator):
        section = generator._build_positive_findings()
        assert "Positive Findings" in section
        assert "Encryption" in section

    def test_report_contains_all_sections(self, generator):
        report = generator.generate()
        assert "## Executive Summary" in report
        assert "### Risk Distribution" in report
        assert "## Vulnerability Distribution" in report
        assert "## Findings" in report
        assert "## Files Examined" in report
        assert "## Remediation Priority" in report


class TestSecurityEmptyReport:
    """Tests for empty security report."""

    def test_empty_vulnerabilities_distribution(self, metadata):
        mock = MagicMock()
        mock.issues_found = []
        mock.files_checked = set()
        mock.get_audit_summary.return_value = {
            "severity_counts": {},
            "files_examined": 0,
        }
        mock.get_findings_by_severity.return_value = {
            "critical": [], "high": [], "medium": [], "low": [], "info": []
        }
        mock.relevant_context = set()

        state = WorkflowState(continuation_id="test", tool_name="security_audit")
        state.consolidated = mock

        gen = SecurityReportGenerator(lens=AuditLens.SECURITY, state=state, metadata=metadata)
        section = gen._build_vulnerability_distribution()
        assert "No vulnerabilities found" in section
