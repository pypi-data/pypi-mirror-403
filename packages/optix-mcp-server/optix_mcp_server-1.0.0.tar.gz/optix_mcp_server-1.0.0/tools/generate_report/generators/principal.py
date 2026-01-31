"""Principal/code quality-specific report generator.

Generates complete principal engineer audit reports from WorkflowState.
"""

from tools.generate_report.generators.base import ReportGenerator
from tools.generate_report.models import AuditLens


class PrincipalReportGenerator(ReportGenerator):
    """Generate principal engineer audit reports from WorkflowState."""

    def generate(self) -> str:
        """Generate complete principal audit report."""
        parts = [
            self._build_header(),
            self._build_executive_summary(),
            self._build_risk_distribution(),
            self._build_code_health_score(),
            self._build_findings_by_severity(),
            self._build_positive_findings(),
            self._build_complexity_hotspots(),
            self._build_duplication_analysis(),
            self._build_files_examined(),
            self._build_remediation_priority(),
            self._build_footer(),
        ]
        return "\n\n".join(parts)

    def _build_code_health_score(self) -> str:
        """Build code health score visualization."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return self._build_empty_code_health()

        total_findings = len(consolidated.issues_found)
        if total_findings == 0:
            score = 100
        elif total_findings < 5:
            score = 80
        elif total_findings < 10:
            score = 60
        elif total_findings < 20:
            score = 40
        else:
            score = 20

        bar_length = score // 10
        bar = "█" * bar_length + "░" * (10 - bar_length)

        lines = [
            "## Code Health Score",
            "",
            f"**Overall Score:** {score} / 100",
            "",
            "```",
            f"Code Health  {bar}  {score}/100",
            "```",
        ]

        return "\n".join(lines)

    def _build_empty_code_health(self) -> str:
        """Build empty code health score."""
        return """## Code Health Score

**Overall Score:** 100 / 100

```
Code Health  ██████████  100/100
```"""

    def _build_positive_findings(self) -> str:
        """Build positive findings from principal_assessments."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        assessments = getattr(consolidated, "relevant_context", set())
        if not assessments:
            return ""

        principal_assessments = [a for a in assessments if ":" in a]
        if not principal_assessments:
            return ""

        lines = [
            "## Positive Findings",
            "",
            "| Good Practice | Assessment |",
            "|---------------|------------|",
        ]

        for assessment in sorted(principal_assessments):
            parts = assessment.split(":", 1)
            if len(parts) == 2:
                lines.append(f"| {parts[0].strip()} | {parts[1].strip()} |")

        return "\n".join(lines)

    def _build_complexity_hotspots(self) -> str:
        """Build complexity hotspots table."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        if not hasattr(consolidated, "complexity_findings"):
            hotspots = [
                i for i in consolidated.issues_found
                if (i.get("category") if hasattr(i, "get") else getattr(i, "category", None)) == "complexity"
            ]
        else:
            hotspots = getattr(consolidated, "complexity_findings", [])

        if not hotspots:
            return ""

        lines = [
            "## Complexity Hotspots",
            "",
            "| Function/Method | File | Complexity Score |",
            "|-----------------|------|------------------|",
        ]

        for finding in hotspots[:10]:
            if hasattr(finding, "to_dict"):
                finding = finding.to_dict()
            affected = finding.get("affected_files", [])
            if affected:
                if isinstance(affected[0], dict):
                    file_path = affected[0].get("file_path", "unknown")
                    func_name = affected[0].get("function_name", "N/A")
                else:
                    file_path = affected[0]
                    func_name = "N/A"
            else:
                file_path = "unknown"
                func_name = "N/A"
            score = finding.get("complexity_score", "N/A")
            lines.append(f"| {func_name} | `{file_path}` | {score} |")

        return "\n".join(lines)

    def _build_duplication_analysis(self) -> str:
        """Build duplication analysis section."""
        consolidated = self.state.consolidated
        if consolidated is None:
            return ""

        if not hasattr(consolidated, "dry_violations"):
            duplications = [
                i for i in consolidated.issues_found
                if (i.get("category") if hasattr(i, "get") else getattr(i, "category", None)) == "dry_violation"
            ]
        else:
            duplications = getattr(consolidated, "dry_violations", [])

        if not duplications:
            return ""

        lines = [
            "## Duplication Analysis",
            "",
            "| Description | Files | Similarity |",
            "|-------------|-------|------------|",
        ]

        for finding in duplications[:5]:
            if hasattr(finding, "to_dict"):
                finding = finding.to_dict()
            desc = finding.get("description", "")[:50]
            affected = finding.get("affected_files", [])
            files_str = ", ".join(
                f.get("file_path", str(f)) if isinstance(f, dict) else str(f)
                for f in affected[:2]
            )
            similarity = finding.get("similarity_percentage", "N/A")
            if similarity != "N/A":
                similarity = f"{similarity}%"
            lines.append(f"| {desc}... | {files_str} | {similarity} |")

        return "\n".join(lines)
