"""Unit tests for security audit report generation."""

import pytest

from tools.security_audit.report import AuditReportGenerator
from tools.workflow.findings import ConsolidatedFindings


@pytest.fixture
def empty_findings():
    """Create empty consolidated findings."""
    return ConsolidatedFindings()


@pytest.fixture
def findings_with_issues():
    """Create consolidated findings with various severity issues."""
    findings = ConsolidatedFindings()
    findings.files_checked.update(["auth.py", "login.py", "api.py"])

    findings.add_issue({
        "severity": "critical",
        "category": "SQL Injection",
        "description": "User input directly concatenated in SQL query",
        "affected_files": ["api.py"],
        "remediation": "Use parameterized queries",
        "cwe_id": "CWE-89",
    })

    findings.add_issue({
        "severity": "high",
        "category": "Broken Authentication",
        "description": "No password complexity requirements",
        "affected_files": ["auth.py", "login.py"],
    })

    findings.add_issue({
        "severity": "medium",
        "category": "Missing HTTPS",
        "description": "API endpoints not enforcing HTTPS",
        "affected_files": ["api.py"],
    })

    findings.add_issue({
        "severity": "low",
        "category": "Verbose Error Messages",
        "description": "Stack traces exposed in error responses",
        "affected_files": ["api.py"],
    })

    return findings


class TestReportHeader:
    """Tests for report header generation (T042)."""

    def test_header_contains_project_name(self, empty_findings):
        """Header should contain project name."""
        generator = AuditReportGenerator("My Project Security Audit")
        report = generator.generate(empty_findings)
        assert "My Project Security Audit" in report

    def test_header_contains_timestamp(self, empty_findings):
        """Header should contain generation timestamp."""
        generator = AuditReportGenerator()
        report = generator.generate(empty_findings)
        assert "Generated:" in report

    def test_header_contains_tool_name(self, empty_findings):
        """Header should reference the tool."""
        generator = AuditReportGenerator()
        report = generator.generate(empty_findings)
        assert "optix-mcp-server" in report


class TestExecutiveSummary:
    """Tests for executive summary section (T043)."""

    def test_summary_contains_total_vulnerabilities(self, findings_with_issues):
        """Summary should show total vulnerability count."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "Total Vulnerabilities" in report
        assert "4" in report

    def test_summary_contains_severity_breakdown(self, findings_with_issues):
        """Summary should show severity breakdown."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "Critical" in report
        assert "High" in report
        assert "Medium" in report
        assert "Low" in report

    def test_summary_contains_files_examined_count(self, findings_with_issues):
        """Summary should show files examined count."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "Files Examined" in report

    def test_summary_shows_risk_level(self, findings_with_issues):
        """Summary should show overall risk level."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "Risk Level" in report


class TestRiskLevelDetermination:
    """Tests for risk level calculation (T044)."""

    def test_critical_findings_result_in_critical_risk(self):
        """Critical findings should result in CRITICAL risk level."""
        findings = ConsolidatedFindings()
        findings.add_issue({"severity": "critical", "category": "test"})
        generator = AuditReportGenerator()
        report = generator.generate(findings)
        assert "CRITICAL" in report

    def test_high_findings_without_critical_result_in_high_risk(self):
        """High findings (no critical) should result in HIGH risk level."""
        findings = ConsolidatedFindings()
        findings.add_issue({"severity": "high", "category": "test"})
        generator = AuditReportGenerator()
        report = generator.generate(findings)
        assert "HIGH" in report

    def test_medium_findings_only_result_in_medium_risk(self):
        """Medium findings only should result in MEDIUM risk level."""
        findings = ConsolidatedFindings()
        findings.add_issue({"severity": "medium", "category": "test"})
        generator = AuditReportGenerator()
        report = generator.generate(findings)
        assert "MEDIUM" in report

    def test_no_findings_result_in_none_risk(self):
        """No findings should result in NONE risk level."""
        findings = ConsolidatedFindings()
        generator = AuditReportGenerator()
        report = generator.generate(findings)
        assert "NONE" in report


class TestFindingsSection:
    """Tests for findings section (T045-T048)."""

    def test_findings_grouped_by_severity(self, findings_with_issues):
        """Findings should be grouped by severity."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "### CRITICAL Severity" in report
        assert "### HIGH Severity" in report
        assert "### MEDIUM Severity" in report
        assert "### LOW Severity" in report

    def test_finding_shows_category(self, findings_with_issues):
        """Finding should show category."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "SQL Injection" in report
        assert "Broken Authentication" in report

    def test_finding_shows_description(self, findings_with_issues):
        """Finding should show description."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "User input directly concatenated" in report

    def test_finding_shows_affected_files(self, findings_with_issues):
        """Finding should show affected files."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "Affected Files:" in report
        assert "`api.py`" in report

    def test_finding_shows_remediation(self, findings_with_issues):
        """Finding should show remediation when available."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "Remediation:" in report
        assert "parameterized queries" in report

    def test_finding_shows_cwe_link(self, findings_with_issues):
        """Finding should show CWE link when available."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "CWE-89" in report
        assert "cwe.mitre.org" in report

    def test_empty_findings_shows_no_vulnerabilities(self, empty_findings):
        """Empty findings should show 'no vulnerabilities' message."""
        generator = AuditReportGenerator()
        report = generator.generate(empty_findings)
        assert "No security vulnerabilities found" in report


class TestFilesExaminedSection:
    """Tests for files examined section (T049)."""

    def test_files_are_listed(self, findings_with_issues):
        """Examined files should be listed."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "## Files Examined" in report
        assert "`auth.py`" in report
        assert "`login.py`" in report
        assert "`api.py`" in report

    def test_files_are_sorted(self, findings_with_issues):
        """Files should be sorted alphabetically."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        api_pos = report.find("`api.py`")
        auth_pos = report.find("`auth.py`")
        login_pos = report.find("`login.py`")
        assert api_pos < auth_pos < login_pos

    def test_empty_files_shows_message(self, empty_findings):
        """Empty files list should show message."""
        generator = AuditReportGenerator()
        report = generator.generate(empty_findings)
        assert "No files were examined" in report


class TestRecommendationsSection:
    """Tests for recommendations section (T050-T051)."""

    def test_critical_findings_get_immediate_action(self):
        """Critical findings should recommend immediate action."""
        findings = ConsolidatedFindings()
        findings.add_issue({"severity": "critical", "category": "test"})
        generator = AuditReportGenerator()
        report = generator.generate(findings)
        assert "IMMEDIATE ACTION REQUIRED" in report

    def test_high_findings_get_high_priority(self):
        """High findings should recommend high priority."""
        findings = ConsolidatedFindings()
        findings.add_issue({"severity": "high", "category": "test"})
        generator = AuditReportGenerator()
        report = generator.generate(findings)
        assert "HIGH PRIORITY" in report

    def test_no_findings_get_positive_message(self, empty_findings):
        """No findings should get positive recommendation."""
        generator = AuditReportGenerator()
        report = generator.generate(empty_findings)
        assert "No critical security issues found" in report


class TestReportFooter:
    """Tests for report footer (T052)."""

    def test_footer_present(self, empty_findings):
        """Report should have footer."""
        generator = AuditReportGenerator()
        report = generator.generate(empty_findings)
        assert "---" in report

    def test_footer_mentions_automatic_generation(self, empty_findings):
        """Footer should mention automatic generation."""
        generator = AuditReportGenerator()
        report = generator.generate(empty_findings)
        assert "automatically" in report


class TestMarkdownFormatting:
    """Tests for proper markdown formatting (T053-T054)."""

    def test_report_is_valid_markdown(self, findings_with_issues):
        """Report should be valid markdown."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert report.startswith("#")
        assert "##" in report
        assert "|" in report

    def test_report_has_proper_sections(self, findings_with_issues):
        """Report should have all required sections."""
        generator = AuditReportGenerator()
        report = generator.generate(findings_with_issues)
        assert "## Executive Summary" in report
        assert "## Findings" in report
        assert "## Files Examined" in report
        assert "## Recommendations" in report
