"""DevOps-specific report generator.

Generates complete DevOps audit reports from WorkflowState.
"""

from tools.generate_report.generators.base import ReportGenerator
from tools.generate_report.models import AuditLens


class DevOpsReportGenerator(ReportGenerator):
    """Generate DevOps audit reports from WorkflowState."""

    def generate(self) -> str:
        """Generate complete DevOps audit report."""
        parts = [
            self._build_header(),
            self._build_executive_summary(),
            self._build_risk_distribution(),
            self._build_artifact_coverage(),
            self._build_findings_by_severity(),
            self._build_positive_findings(),
            self._build_missing_context(),
            self._build_files_examined(),
            self._build_remediation_priority(),
            self._build_footer(),
        ]
        return "\n\n".join(parts)

    def _build_artifact_coverage(self) -> str:
        """Build artifact coverage table from ConsolidatedDevOpsFindings."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_artifact_coverage()

        if not hasattr(consolidated, "get_artifact_coverage_summary"):
            return self._build_empty_artifact_coverage()

        coverage = consolidated.get_artifact_coverage_summary()

        lines = [
            "## Artifact Coverage",
            "",
            "| Artifact Type | Analyzed | Omitted | Files |",
            "|---------------|----------|---------|-------|",
        ]

        for artifact_type, data in sorted(coverage.items()):
            analyzed = data.get("analyzed", 0)
            omitted = data.get("omitted", 0)
            files = data.get("files", [])
            files_str = ", ".join(f"`{f}`" for f in files[:3])
            if len(files) > 3:
                files_str += f" (+{len(files) - 3} more)"
            status = "✅" if analyzed > 0 else "❌"
            lines.append(f"| {artifact_type} | {status} {analyzed} | {omitted} | {files_str or 'None'} |")

        return "\n".join(lines)

    def _build_empty_artifact_coverage(self) -> str:
        """Build empty artifact coverage."""
        return """## Artifact Coverage

No artifact data available."""

    def _build_positive_findings(self) -> str:
        """Build positive findings from devops_assessments."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        assessments = getattr(consolidated, "relevant_context", set())
        if not assessments:
            return ""

        devops_assessments = [a for a in assessments if ":" in a]
        if not devops_assessments:
            return ""

        lines = [
            "## Positive Findings",
            "",
            "| Practice | Assessment |",
            "|----------|------------|",
        ]

        for assessment in sorted(devops_assessments):
            parts = assessment.split(":", 1)
            if len(parts) == 2:
                lines.append(f"| {parts[0].strip()} | {parts[1].strip()} |")

        return "\n".join(lines)

    def _build_missing_context(self) -> str:
        """Build missing context section."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        if not hasattr(consolidated, "get_missing_context_summary"):
            return ""

        missing = consolidated.get_missing_context_summary()
        missing_lockfiles = missing.get("missing_lockfiles", [])
        other_missing = missing.get("other_missing_context", [])

        if not missing_lockfiles and not other_missing:
            return """## Missing Context

**All requested artifacts were available for analysis.**"""

        lines = ["## Missing Context", ""]

        if missing_lockfiles:
            lines.append("### Missing Lockfiles")
            for item in sorted(missing_lockfiles):
                lines.append(f"- {item}")
            lines.append("")

        if other_missing:
            lines.append("### Other Missing Context")
            for item in sorted(other_missing):
                lines.append(f"- {item}")

        return "\n".join(lines)
