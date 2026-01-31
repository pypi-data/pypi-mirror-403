"""Security-specific report generator.

Generates complete security audit reports from WorkflowState.
"""

from tools.generate_report.generators.base import ReportGenerator
from tools.generate_report.models import AuditLens


class SecurityReportGenerator(ReportGenerator):
    """Generate security audit reports from WorkflowState."""

    def generate(self) -> str:
        """Generate complete security audit report."""
        parts = [
            self._build_header(),
            self._build_executive_summary(),
            self._build_risk_distribution(),
            self._build_vulnerability_distribution(),
            self._build_findings_by_severity(),
            self._build_positive_findings(),
            self._build_cwe_references(),
            self._build_files_examined(),
            self._build_remediation_priority(),
            self._build_footer(),
        ]
        return "\n\n".join(parts)

    def _build_vulnerability_distribution(self) -> str:
        """Build vulnerability category distribution table."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_vulnerability_distribution()

        categories: dict[str, int] = {}
        for issue in consolidated.issues_found:
            if hasattr(issue, "get"):
                cat = issue.get("category", "Unknown")
            else:
                cat = getattr(issue, "category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1

        if not categories:
            return self._build_empty_vulnerability_distribution()

        lines = [
            "## Vulnerability Distribution",
            "",
            "| Category | Count |",
            "|----------|-------|",
        ]

        for category in sorted(categories.keys()):
            lines.append(f"| {category} | {categories[category]} |")

        return "\n".join(lines)

    def _build_empty_vulnerability_distribution(self) -> str:
        """Build empty vulnerability distribution."""
        return """## Vulnerability Distribution

No vulnerabilities found."""

    def _build_positive_findings(self) -> str:
        """Build positive findings from security_assessments."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        assessments = getattr(consolidated, "relevant_context", set())
        if not assessments:
            return ""

        security_assessments = [a for a in assessments if ":" in a]
        if not security_assessments:
            return ""

        lines = [
            "## Positive Findings",
            "",
            "| Security Control | Assessment |",
            "|------------------|------------|",
        ]

        for assessment in sorted(security_assessments):
            parts = assessment.split(":", 1)
            if len(parts) == 2:
                lines.append(f"| {parts[0].strip()} | {parts[1].strip()} |")

        return "\n".join(lines)

    def _build_cwe_references(self) -> str:
        """Build CWE reference table from findings."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        cwe_data: dict[str, dict] = {}

        for issue in consolidated.issues_found:
            if hasattr(issue, "get"):
                cwe_id = issue.get("cwe_id")
                category = issue.get("category", "Unknown")
                severity = issue.get("severity", "info")
            else:
                cwe_id = getattr(issue, "cwe_id", None)
                category = getattr(issue, "category", "Unknown")
                severity = getattr(issue, "severity", "info")

            if cwe_id:
                if cwe_id not in cwe_data:
                    cwe_data[cwe_id] = {"category": category, "severity": severity, "count": 1}
                else:
                    cwe_data[cwe_id]["count"] += 1
                    if severity_order.get(severity, 4) < severity_order.get(cwe_data[cwe_id]["severity"], 4):
                        cwe_data[cwe_id]["severity"] = severity

        if not cwe_data:
            return ""

        lines = [
            "## CWE References",
            "",
            "| CWE ID | Category | Severity | Count |",
            "|--------|----------|----------|-------|",
        ]

        for cwe_id in sorted(cwe_data.keys()):
            data = cwe_data[cwe_id]
            lines.append(f"| {cwe_id} | {data['category']} | {data['severity']} | {data['count']} |")

        return "\n".join(lines)
