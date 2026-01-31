"""Unit tests for DevOpsReportGenerator."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.generate_report.generators.devops import DevOpsReportGenerator
from tools.generate_report.models import AuditLens, ReportMetadata
from tools.workflow.state import WorkflowState


@pytest.fixture
def metadata():
    return ReportMetadata(
        lens=AuditLens.DEVOPS,
        report_number=1,
        report_path=Path("/tmp/reports/DEVOPS_AUDIT_REPORT_1.md"),
        generated_at=datetime(2026, 1, 22, 14, 30, 45),
        project_name="test-project",
    )


@pytest.fixture
def mock_consolidated():
    mock = MagicMock()
    mock.files_checked = {"Dockerfile", ".github/workflows/ci.yml"}
    mock.issues_found = [
        {
            "severity": "critical",
            "category": "dockerfile",
            "description": "Running as root",
            "affected_files": ["Dockerfile"],
            "remediation": "Use non-root USER",
        },
        {
            "severity": "high",
            "category": "cicd",
            "description": "Secrets in plain text",
            "affected_files": [".github/workflows/ci.yml"],
            "remediation": "Use GitHub secrets",
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
    mock.get_artifact_coverage_summary.return_value = {
        "dockerfiles": {"analyzed": 1, "omitted": 0, "files": ["Dockerfile"]},
        "workflows": {"analyzed": 1, "omitted": 0, "files": [".github/workflows/ci.yml"]},
        "package_files": {"analyzed": 0, "omitted": 0, "files": []},
    }
    mock.get_missing_context_summary.return_value = {
        "missing_lockfiles": ["package-lock.json"],
        "other_missing_context": [],
    }
    mock.relevant_context = {"Multi-stage builds: Using multi-stage Docker builds"}
    return mock


@pytest.fixture
def workflow_state(mock_consolidated):
    state = WorkflowState(
        continuation_id="test-uuid",
        tool_name="devops_audit",
    )
    state.consolidated = mock_consolidated
    return state


@pytest.fixture
def generator(metadata, workflow_state):
    return DevOpsReportGenerator(
        lens=AuditLens.DEVOPS,
        state=workflow_state,
        metadata=metadata,
    )


class TestDevOpsReportGenerator:
    """Tests for DevOpsReportGenerator."""

    def test_generate_produces_complete_report(self, generator):
        report = generator.generate()
        assert "# DEVOPS Audit Report" in report
        assert "Executive Summary" in report
        assert "Artifact Coverage" in report

    def test_artifact_coverage_shows_analyzed_files(self, generator):
        section = generator._build_artifact_coverage()
        assert "Artifact Coverage" in section
        assert "dockerfiles" in section
        assert "workflows" in section

    def test_missing_context_shows_missing_files(self, generator):
        section = generator._build_missing_context()
        assert "Missing Context" in section
        assert "package-lock.json" in section

    def test_positive_findings_from_assessments(self, generator):
        section = generator._build_positive_findings()
        assert "Multi-stage builds" in section

    def test_report_contains_all_sections(self, generator):
        report = generator.generate()
        assert "## Executive Summary" in report
        assert "## Artifact Coverage" in report
        assert "## Findings" in report
        assert "## Missing Context" in report


class TestDevOpsEmptyReport:
    """Tests for empty devops report."""

    def test_empty_artifact_coverage(self, metadata):
        state = WorkflowState(continuation_id="test", tool_name="devops_audit")
        state.consolidated = None

        gen = DevOpsReportGenerator(lens=AuditLens.DEVOPS, state=state, metadata=metadata)
        section = gen._build_artifact_coverage()
        assert "No artifact data available" in section

    def test_all_artifacts_available(self, metadata):
        mock = MagicMock()
        mock.files_checked = set()
        mock.issues_found = []
        mock.get_audit_summary.return_value = {"severity_counts": {}, "files_examined": 0}
        mock.get_findings_by_severity.return_value = {
            "critical": [], "high": [], "medium": [], "low": [], "info": []
        }
        mock.get_missing_context_summary.return_value = {
            "missing_lockfiles": [],
            "other_missing_context": [],
        }
        mock.relevant_context = set()

        state = WorkflowState(continuation_id="test", tool_name="devops_audit")
        state.consolidated = mock

        gen = DevOpsReportGenerator(lens=AuditLens.DEVOPS, state=state, metadata=metadata)
        section = gen._build_missing_context()
        assert "All requested artifacts were available" in section
