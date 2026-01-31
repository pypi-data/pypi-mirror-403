"""Base class for programmatic report generation.

Provides the abstract base and common section builders for all
lens-specific report generators.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from tools.generate_report.generators.escape import escape_markdown_content
from tools.generate_report.models import AuditLens, ReportMetadata
from tools.workflow.state import WorkflowState


FILE_CATEGORIES = {
    "Authentication": ["auth", "login", "session", "oauth", "jwt", "token"],
    "API Endpoints": ["api", "routes", "endpoints", "handlers", "controllers"],
    "Data Access": ["db", "database", "models", "repository", "dao", "orm"],
    "Configuration": ["config", "settings", "env", ".env", "yaml", "yml"],
    "Cryptography": ["crypto", "encrypt", "hash", "cipher", "ssl", "tls"],
    "Validation": ["validation", "validator", "schema", "sanitize"],
    "Middleware": ["middleware", "interceptor", "filter", "guard"],
    "Components": ["components", "component", "widget", "ui"],
    "Forms": ["form", "forms", "input"],
    "Navigation": ["nav", "navigation", "router", "menu"],
    "Tests": ["test", "tests", "spec", "specs", "__tests__"],
    "Utilities": ["util", "utils", "helper", "helpers", "lib"],
    "CI/CD": [".github", "workflow", "ci", "cd", "pipeline", "actions"],
    "Container": ["docker", "dockerfile", "compose", "kubernetes", "k8s"],
    "Infrastructure": ["terraform", "pulumi", "cloudformation", "iac"],
}


SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

SEVERITY_DISPLAY = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Info",
}


CATEGORY_PRIORITY = [
    "CI/CD",
    "Container",
    "Infrastructure",
    "Tests",
    "Authentication",
    "API Endpoints",
    "Data Access",
    "Configuration",
    "Cryptography",
    "Validation",
    "Middleware",
    "Components",
    "Forms",
    "Navigation",
    "Utilities",
]


def _categorize_file(file_path: str) -> str:
    """Categorize a file path based on path patterns.

    Uses priority ordering to ensure more specific patterns match first
    (e.g., ".github/workflows" matches CI/CD before "yml" matches Configuration).

    Args:
        file_path: Path to the file

    Returns:
        Category name or "Other" if no match
    """
    path_lower = file_path.lower()

    for category in CATEGORY_PRIORITY:
        patterns = FILE_CATEGORIES.get(category, [])
        for pattern in patterns:
            if pattern in path_lower:
                return category

    for category, patterns in FILE_CATEGORIES.items():
        if category not in CATEGORY_PRIORITY:
            for pattern in patterns:
                if pattern in path_lower:
                    return category

    return "Other"


@dataclass
class ReportGenerator(ABC):
    """Abstract base class for programmatic report generation.

    Transforms WorkflowState into complete markdown reports.
    Subclasses implement lens-specific sections.
    """

    lens: AuditLens
    state: WorkflowState
    metadata: ReportMetadata

    @abstractmethod
    def generate(self) -> str:
        """Generate complete markdown report from WorkflowState.

        Returns:
            Complete markdown report as string
        """
        pass

    def _build_header(self) -> str:
        """Build report header with metadata."""
        timestamp = self.metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S")
        project_name = self.metadata.project_name

        return f"""# {self.lens.value} Audit Report

**Generated:** {timestamp}
**Tool:** optix-mcp-server {self.lens.tool_name}
**Project:** {project_name}"""

    def _build_executive_summary(self) -> str:
        """Build executive summary with severity counts."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_executive_summary()

        summary = consolidated.get_audit_summary()
        severity_counts = summary.get("severity_counts", {})
        total_issues = summary.get("total_vulnerabilities", len(consolidated.issues_found))
        files_examined = summary.get("files_examined", len(consolidated.files_checked))

        overall_status = self._get_overall_status(severity_counts)

        lines = [
            "## Executive Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Issues | {total_issues} |",
        ]

        for severity in SEVERITY_ORDER:
            display = SEVERITY_DISPLAY.get(severity, severity.capitalize())
            count = severity_counts.get(severity, 0)
            lines.append(f"| {display} | {count} |")

        lines.extend([
            f"| Files Examined | {files_examined} |",
            f"| Overall Status | **{overall_status}** |",
        ])

        return "\n".join(lines)

    def _build_empty_executive_summary(self) -> str:
        """Build executive summary when no consolidated data exists."""
        return """## Executive Summary

| Metric | Value |
|--------|-------|
| Total Issues | 0 |
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Informational | 0 |
| Files Examined | 0 |
| Overall Status | **PASS** |"""

    def _build_risk_distribution(self) -> str:
        """Build ASCII risk distribution chart."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_risk_distribution()

        summary = consolidated.get_audit_summary()
        severity_counts = summary.get("severity_counts", {})
        total = sum(severity_counts.values())

        lines = ["### Risk Distribution", "", "```"]

        if total == 0:
            lines.append("No issues found.")
        else:
            for severity in SEVERITY_ORDER:
                count = severity_counts.get(severity, 0)
                percentage = (count / total * 100) if total > 0 else 0
                bar_length = int(percentage / 10)
                bar = "█" * bar_length + "░" * (10 - bar_length)
                display = SEVERITY_DISPLAY.get(severity, severity.capitalize())
                lines.append(f"{display:12s} {bar}  {count} ({percentage:.0f}%)")

        lines.append("```")
        return "\n".join(lines)

    def _build_empty_risk_distribution(self) -> str:
        """Build empty risk distribution chart."""
        return """### Risk Distribution

```
No issues found.
```"""

    def _build_findings_by_severity(self) -> str:
        """Build detailed findings grouped by severity.

        Findings are ordered deterministically by severity level,
        then by discovery order within each severity.
        """
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_findings()

        by_severity = consolidated.get_findings_by_severity()
        lines = ["## Findings", ""]

        for severity in SEVERITY_ORDER:
            findings = by_severity.get(severity, [])
            display = SEVERITY_DISPLAY.get(severity, severity.capitalize())
            lines.append(f"### {display} Severity")
            lines.append("")

            if not findings:
                lines.append(f"**No {severity} severity findings.**")
                lines.append("")
                continue

            for i, finding in enumerate(findings, 1):
                formatted = self._format_finding(finding, i)
                lines.append(formatted)
                lines.append("")
                lines.append("---")
                lines.append("")

        return "\n".join(lines)

    def _build_empty_findings(self) -> str:
        """Build empty findings section."""
        lines = ["## Findings", ""]
        for severity in SEVERITY_ORDER:
            display = SEVERITY_DISPLAY.get(severity, severity.capitalize())
            lines.append(f"### {display} Severity")
            lines.append("")
            lines.append(f"**No {severity} severity findings.**")
            lines.append("")
        return "\n".join(lines)

    def _format_finding(self, finding: dict | Any, number: int) -> str:
        """Format a single finding as markdown.

        Args:
            finding: Finding dictionary or object with to_dict method
            number: Finding number within severity group

        Returns:
            Formatted markdown string
        """
        if hasattr(finding, "to_dict"):
            finding = finding.to_dict()

        description = finding.get("description", "No description")
        category = finding.get("category", "Unknown")
        affected_files = finding.get("affected_files", [])
        remediation = finding.get("remediation", "")

        description = escape_markdown_content(description)
        remediation = escape_markdown_content(remediation) if remediation else ""

        title = description[:80] + "..." if len(description) > 80 else description

        if affected_files:
            if isinstance(affected_files[0], dict):
                file_info = affected_files[0]
                file_path = file_info.get("file_path", "unknown")
                line_start = file_info.get("line_start")
                if line_start:
                    file_display = f"`{file_path}:{line_start}`"
                else:
                    file_display = f"`{file_path}`"
            else:
                file_display = f"`{affected_files[0]}`"
        else:
            file_display = "N/A"

        lines = [
            f"#### {number}. {title}",
            "",
            f"**File:** {file_display}",
            f"**Category:** {category}",
            "",
            f"**Description:** {description}",
        ]

        if remediation:
            lines.extend([
                "",
                f"**Remediation:** {remediation}",
            ])

        return "\n".join(lines)

    def _build_files_examined(self) -> str:
        """Build categorized files examined section.

        Files are sorted alphabetically within categories for determinism.
        """
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_files_examined()

        files = list(consolidated.files_checked)
        if not files:
            return self._build_empty_files_examined()

        categorized: dict[str, list[str]] = {}
        for file_path in files:
            category = _categorize_file(file_path)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(file_path)

        for category in categorized:
            categorized[category] = sorted(categorized[category])

        lines = ["## Files Examined", ""]

        for category in sorted(categorized.keys()):
            lines.append(f"### {category}")
            for file_path in categorized[category]:
                lines.append(f"- `{file_path}`")
            lines.append("")

        return "\n".join(lines)

    def _build_empty_files_examined(self) -> str:
        """Build empty files examined section."""
        return """## Files Examined

No files were examined."""

    def _build_remediation_priority(self) -> str:
        """Build P0/P1/P2 remediation priorities."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_remediation()

        by_severity = consolidated.get_findings_by_severity()

        critical = by_severity.get("critical", [])
        high = by_severity.get("high", [])
        medium_low = by_severity.get("medium", []) + by_severity.get("low", [])

        lines = ["## Remediation Priority", ""]

        lines.append("### Immediate (P0) - Critical Issues")
        if critical:
            for i, finding in enumerate(critical, 1):
                desc = self._get_finding_description(finding)
                lines.append(f"{i}. {desc}")
        else:
            lines.append("No critical issues requiring immediate action.")
        lines.append("")

        lines.append("### Short-term (P1) - High Priority")
        if high:
            for i, finding in enumerate(high, 1):
                desc = self._get_finding_description(finding)
                lines.append(f"{i}. {desc}")
        else:
            lines.append("No high priority issues.")
        lines.append("")

        lines.append("### Medium-term (P2) - Standard Priority")
        if medium_low:
            for i, finding in enumerate(medium_low[:5], 1):
                desc = self._get_finding_description(finding)
                lines.append(f"{i}. {desc}")
            if len(medium_low) > 5:
                lines.append(f"... and {len(medium_low) - 5} more items")
        else:
            lines.append("No medium or low priority issues.")
        lines.append("")

        return "\n".join(lines)

    def _get_finding_description(self, finding: dict | Any) -> str:
        """Extract description from finding.

        Args:
            finding: Finding dict or object

        Returns:
            Description string (truncated if needed)
        """
        if hasattr(finding, "to_dict"):
            finding = finding.to_dict()
        desc = finding.get("description", "No description")
        desc = escape_markdown_content(desc)
        return desc[:100] + "..." if len(desc) > 100 else desc

    def _build_empty_remediation(self) -> str:
        """Build empty remediation section."""
        return """## Remediation Priority

### Immediate (P0) - Critical Issues
No critical issues requiring immediate action.

### Short-term (P1) - High Priority
No high priority issues.

### Medium-term (P2) - Standard Priority
No medium or low priority issues."""

    def _build_footer(self) -> str:
        """Build report footer."""
        return f"""---

*This report was generated automatically by optix-mcp-server {self.lens.tool_name} tool.
For questions or concerns, please contact your development team.*"""

    @staticmethod
    def _get_overall_status(severity_counts: dict[str, int]) -> str:
        """Determine PASS/NEEDS_ATTENTION/CRITICAL status.

        Args:
            severity_counts: Dictionary with severity counts

        Returns:
            Status string
        """
        critical = severity_counts.get("critical", 0)
        high = severity_counts.get("high", 0)

        if critical > 0:
            return "CRITICAL"
        if high > 0:
            return "NEEDS_ATTENTION"
        return "PASS"
