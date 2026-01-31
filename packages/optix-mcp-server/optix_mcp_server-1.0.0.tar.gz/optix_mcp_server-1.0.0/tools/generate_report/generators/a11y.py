"""Accessibility-specific report generator.

Generates complete accessibility audit reports from WorkflowState.
"""

from tools.generate_report.generators.base import ReportGenerator, SEVERITY_ORDER
from tools.generate_report.generators.escape import escape_for_table_cell, escape_markdown_content
from tools.generate_report.models import AuditLens


SEVERITY_MAPPING = {
    "blocker": "critical",
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
}


class A11yReportGenerator(ReportGenerator):
    """Generate accessibility audit reports from WorkflowState."""

    def generate(self) -> str:
        """Generate complete a11y audit report."""
        parts = [
            self._build_header(),
            self._build_executive_summary(),
            self._build_risk_distribution(),
            self._build_wcag_compliance_matrix(),
            self._build_issue_distribution(),
            self._build_findings_by_severity(),
            self._build_positive_findings(),
            self._build_wcag_criterion_coverage(),
            self._build_files_examined(),
            self._build_remediation_priority(),
            self._build_footer(),
        ]
        return "\n\n".join(parts)

    def _build_wcag_compliance_matrix(self) -> str:
        """Build WCAG level compliance matrix."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_wcag_matrix()

        level_stats = {"A": {"passed": 0, "failed": 0}, "AA": {"passed": 0, "failed": 0}, "AAA": {"passed": 0, "failed": 0}}

        for issue in consolidated.issues_found:
            if hasattr(issue, "get"):
                wcag_level = issue.get("wcag_level", "A")
            else:
                wcag_level = getattr(issue, "wcag_level", "A")
            if wcag_level in level_stats:
                level_stats[wcag_level]["failed"] += 1

        lines = [
            "## WCAG Compliance Matrix",
            "",
            "| Level | Passed | Failed | Compliance |",
            "|-------|--------|--------|------------|",
        ]

        for level in ["A", "AA", "AAA"]:
            passed = level_stats[level]["passed"]
            failed = level_stats[level]["failed"]
            total = passed + failed
            compliance = f"{(passed / total * 100):.0f}%" if total > 0 else "N/A"
            lines.append(f"| {level} | {passed} | {failed} | {compliance} |")

        return "\n".join(lines)

    def _build_empty_wcag_matrix(self) -> str:
        """Build empty WCAG matrix."""
        return """## WCAG Compliance Matrix

No WCAG data available."""

    def _build_issue_distribution(self) -> str:
        """Build issue distribution by category."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_issue_distribution()

        categories: dict[str, int] = {}
        for issue in consolidated.issues_found:
            if hasattr(issue, "get"):
                cat = issue.get("category", "Unknown")
            else:
                cat = getattr(issue, "category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1

        if not categories:
            return self._build_empty_issue_distribution()

        lines = [
            "## Issue Distribution",
            "",
            "| Category | Count |",
            "|----------|-------|",
        ]

        for category in sorted(categories.keys()):
            lines.append(f"| {escape_for_table_cell(category)} | {categories[category]} |")

        return "\n".join(lines)

    def _build_empty_issue_distribution(self) -> str:
        """Build empty issue distribution."""
        return """## Issue Distribution

No issues found."""

    def _build_positive_findings(self) -> str:
        """Build positive findings from accessibility_assessments."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        assessments = getattr(consolidated, "relevant_context", set())
        if not assessments:
            return ""

        a11y_assessments = [a for a in assessments if ":" in a]
        if not a11y_assessments:
            return ""

        lines = [
            "## Positive Findings",
            "",
            "| Accessibility Feature | Assessment |",
            "|----------------------|------------|",
        ]

        for assessment in sorted(a11y_assessments):
            parts = assessment.split(":", 1)
            if len(parts) == 2:
                feature = escape_for_table_cell(parts[0].strip())
                value = escape_for_table_cell(escape_markdown_content(parts[1].strip()))
                lines.append(f"| {feature} | {value} |")

        return "\n".join(lines)

    def _build_wcag_criterion_coverage(self) -> str:
        """Build WCAG criterion coverage table."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        criteria: dict[str, str] = {}
        for issue in consolidated.issues_found:
            if hasattr(issue, "get"):
                criterion = issue.get("wcag_criterion")
            else:
                criterion = getattr(issue, "wcag_criterion", None)
            if criterion:
                criteria[criterion] = "❌"

        if not criteria:
            return ""

        lines = [
            "## WCAG Criterion Coverage",
            "",
            "| Criterion | Status |",
            "|-----------|--------|",
        ]

        for criterion in sorted(criteria.keys()):
            lines.append(f"| {criterion} | {criteria[criterion]} |")

        return "\n".join(lines)
