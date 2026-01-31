"""Unit tests for DevOpsFinding and ConsolidatedDevOpsFindings."""

import pytest

from tools.devops_audit import DevOpsCategory, DevOpsFinding, Severity
from tools.devops_audit.finding import ConsolidatedDevOpsFindings


class TestDevOpsFinding:
    def test_create_finding_with_minimum_fields(self):
        finding = DevOpsFinding(
            severity=Severity.CRITICAL,
            category=DevOpsCategory.DOCKERFILE,
            description="Test finding",
            affected_files=["Dockerfile"],
        )
        assert finding.severity == Severity.CRITICAL
        assert finding.category == DevOpsCategory.DOCKERFILE
        assert finding.description == "Test finding"
        assert finding.affected_files == ["Dockerfile"]

    def test_create_finding_with_string_severity(self):
        finding = DevOpsFinding(
            severity="high",
            category=DevOpsCategory.CICD,
            description="Test",
            affected_files=["ci.yml"],
        )
        assert finding.severity == Severity.HIGH

    def test_create_finding_with_string_category(self):
        finding = DevOpsFinding(
            severity=Severity.MEDIUM,
            category="dependency",
            description="Test",
            affected_files=["package.json"],
        )
        assert finding.category == DevOpsCategory.DEPENDENCY

    def test_finding_requires_description(self):
        with pytest.raises(ValueError, match="description must be non-empty"):
            DevOpsFinding(
                severity=Severity.LOW,
                category=DevOpsCategory.DOCKERFILE,
                description="",
                affected_files=["Dockerfile"],
            )

    def test_finding_requires_affected_files(self):
        with pytest.raises(ValueError, match="affected_files must contain"):
            DevOpsFinding(
                severity=Severity.LOW,
                category=DevOpsCategory.DOCKERFILE,
                description="Test",
                affected_files=[],
            )

    def test_finding_to_dict(self):
        finding = DevOpsFinding(
            severity=Severity.CRITICAL,
            category=DevOpsCategory.DOCKERFILE,
            description="Running as root",
            affected_files=["Dockerfile"],
            remediation="Add USER directive",
            line_numbers=[10],
        )
        d = finding.to_dict()
        assert d["severity"] == "critical"
        assert d["category"] == "dockerfile"
        assert d["description"] == "Running as root"
        assert d["remediation"] == "Add USER directive"
        assert d["line_numbers"] == [10]

    def test_finding_from_dict(self):
        data = {
            "severity": "high",
            "category": "cicd",
            "description": "Unpinned action",
            "affected_files": [".github/workflows/ci.yml"],
            "remediation": "Pin to SHA",
        }
        finding = DevOpsFinding.from_dict(data)
        assert finding.severity == Severity.HIGH
        assert finding.category == DevOpsCategory.CICD
        assert finding.description == "Unpinned action"


class TestConsolidatedDevOpsFindings:
    def test_default_initialization(self):
        consolidated = ConsolidatedDevOpsFindings()
        assert consolidated.dockerfiles_analyzed == []
        assert consolidated.workflows_analyzed == []
        assert consolidated.package_files_analyzed == []
        assert consolidated.missing_lockfiles == []

    def test_get_findings_by_category(self):
        consolidated = ConsolidatedDevOpsFindings()
        consolidated.add_issue({
            "severity": "critical",
            "category": "dockerfile",
            "description": "Running as root",
            "affected_files": ["Dockerfile"],
        })
        consolidated.add_issue({
            "severity": "high",
            "category": "cicd",
            "description": "Unpinned action",
            "affected_files": ["ci.yml"],
        })

        by_category = consolidated.get_findings_by_category()
        assert len(by_category[DevOpsCategory.DOCKERFILE]) == 1
        assert len(by_category[DevOpsCategory.CICD]) == 1
        assert len(by_category[DevOpsCategory.DEPENDENCY]) == 0

    def test_get_artifact_coverage_summary(self):
        consolidated = ConsolidatedDevOpsFindings()
        consolidated.dockerfiles_analyzed = ["Dockerfile", "Dockerfile.prod"]
        consolidated.dockerfiles_omitted = ["Dockerfile.dev"]
        consolidated.workflows_analyzed = ["ci.yml"]

        coverage = consolidated.get_artifact_coverage_summary()
        assert coverage["dockerfiles"]["analyzed"] == 2
        assert coverage["dockerfiles"]["omitted"] == 1
        assert coverage["workflows"]["analyzed"] == 1

    def test_get_missing_context_summary(self):
        consolidated = ConsolidatedDevOpsFindings()
        consolidated.missing_lockfiles = ["package-lock.json"]
        consolidated.missing_context_requested = ["credentials.json"]

        summary = consolidated.get_missing_context_summary()
        assert "package-lock.json" in summary["missing_lockfiles"]
        assert "credentials.json" in summary["other_missing_context"]

    def test_get_devops_audit_summary(self):
        consolidated = ConsolidatedDevOpsFindings()
        consolidated.add_issue({
            "severity": "critical",
            "category": "dockerfile",
            "description": "Test",
            "affected_files": ["Dockerfile"],
        })
        consolidated.add_issue({
            "severity": "high",
            "category": "cicd",
            "description": "Test",
            "affected_files": ["ci.yml"],
        })

        summary = consolidated.get_devops_audit_summary()
        assert summary["total_findings"] == 2
        assert summary["severity_counts"]["critical"] == 1
        assert summary["severity_counts"]["high"] == 1
        assert summary["category_counts"]["dockerfile"] == 1
        assert summary["category_counts"]["cicd"] == 1
