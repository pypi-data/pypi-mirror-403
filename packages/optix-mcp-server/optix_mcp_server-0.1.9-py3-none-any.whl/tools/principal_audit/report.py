"""Report generator for Principal Engineer Audit results."""

from datetime import datetime
from typing import Any, Optional

from tools.principal_audit.category import FindingCategory
from tools.principal_audit.finding import (
    ConsolidatedPrincipalFindings,
    PrincipalEngineerFinding,
)
from tools.principal_audit.severity import Severity


class PrincipalAuditReportGenerator:
    """Generates markdown reports from Principal Engineer audit findings."""

    def __init__(self, project_name: str = "Principal Engineer Audit"):
        self._project_name = project_name

    def generate(
        self,
        consolidated: ConsolidatedPrincipalFindings,
        expert_analysis: Optional[dict[str, Any]] = None
    ) -> str:
        sections = [
            self._generate_header(),
            self._generate_executive_summary(consolidated),
            self._generate_analysis_overview(consolidated),
            self._generate_findings_by_category(consolidated),
            self._generate_files_section(consolidated),
            self._generate_recommendations(consolidated),
        ]

        if expert_analysis:
            sections.append(self._generate_expert_analysis_section(expert_analysis))

        sections.append(self._generate_footer())
        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# {self._project_name}

**Generated:** {timestamp}
**Tool:** optix-mcp-server principal_audit"""

    def _generate_executive_summary(
        self, consolidated: ConsolidatedPrincipalFindings
    ) -> str:
        by_severity = consolidated.get_findings_by_severity()
        all_findings = consolidated.get_all_findings()
        total = len(all_findings)

        health_score = self._calculate_health_score(consolidated)
        health_grade = self._get_health_grade(health_score)

        return f"""## Executive Summary

| Metric | Value |
|--------|-------|
| Total Findings | {total} |
| Critical | {len(by_severity['critical'])} |
| High | {len(by_severity['high'])} |
| Medium | {len(by_severity['medium'])} |
| Low | {len(by_severity['low'])} |
| Files Analyzed | {len(consolidated.files_analyzed)} |
| Files Omitted | {len(consolidated.files_omitted)} |
| Code Health Score | **{health_score}/100** |
| Grade | **{health_grade}** |"""

    def _calculate_health_score(
        self, consolidated: ConsolidatedPrincipalFindings
    ) -> int:
        base_score = 100
        by_severity = consolidated.get_findings_by_severity()

        penalty = (
            len(by_severity['critical']) * 20 +
            len(by_severity['high']) * 10 +
            len(by_severity['medium']) * 5 +
            len(by_severity['low']) * 2
        )

        return max(0, min(100, base_score - penalty))

    def _get_health_grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"

    def _generate_analysis_overview(
        self, consolidated: ConsolidatedPrincipalFindings
    ) -> str:
        return f"""## Analysis Overview

| Category | Findings |
|----------|----------|
| Complexity Issues | {len(consolidated.complexity_findings)} |
| DRY Violations | {len(consolidated.dry_violations)} |
| Coupling Issues | {len(consolidated.coupling_issues)} |
| Separation of Concerns | {len(consolidated.separation_of_concerns_issues)} |
| Maintainability Risks | {len(consolidated.maintainability_risks)} |"""

    def _generate_findings_by_category(
        self, consolidated: ConsolidatedPrincipalFindings
    ) -> str:
        sections = ["## Detailed Findings"]

        category_data = [
            ("Complexity Issues (Step 1)", FindingCategory.COMPLEXITY, consolidated.complexity_findings),
            ("DRY Violations (Step 2)", FindingCategory.DRY_VIOLATION, consolidated.dry_violations),
            ("Coupling Issues (Step 3)", FindingCategory.COUPLING, consolidated.coupling_issues),
            ("Separation of Concerns (Step 4)", FindingCategory.SEPARATION_OF_CONCERNS, consolidated.separation_of_concerns_issues),
            ("Maintainability Risks (Step 5)", FindingCategory.MAINTAINABILITY_RISK, consolidated.maintainability_risks),
        ]

        for title, category, findings in category_data:
            sections.append(f"\n### {title}\n")
            if findings:
                sorted_findings = sorted(
                    findings,
                    key=lambda f: f.severity.numeric_value(),
                    reverse=True
                )
                for i, finding in enumerate(sorted_findings, 1):
                    sections.append(self._format_finding(finding, i))
            else:
                sections.append("No issues found in this category.")

        return "\n".join(sections)

    def _format_finding(
        self, finding: PrincipalEngineerFinding, index: int
    ) -> str:
        severity_badge = self._get_severity_badge(finding.severity)
        lines = [f"#### {index}. {severity_badge} {finding.description[:80]}"]

        if len(finding.description) > 80:
            lines.append(f"\n**Full Description:** {finding.description}")

        if finding.affected_files:
            affected = finding.affected_files
            if len(affected) <= 3:
                for af in affected:
                    loc = f"`{af.file_path}`"
                    if af.line_start:
                        loc += f" (line {af.line_start}"
                        if af.line_end:
                            loc += f"-{af.line_end}"
                        loc += ")"
                    if af.function_name:
                        loc += f" in `{af.function_name}`"
                    lines.append(f"\n**Location:** {loc}")
            else:
                files_str = ", ".join(f"`{af.file_path}`" for af in affected[:5])
                lines.append(f"\n**Affected Files:** {files_str}")

        if finding.complexity_score is not None:
            lines.append(f"\n**Complexity Score:** {finding.complexity_score:.0f}")

        if finding.similarity_percentage is not None:
            lines.append(f"\n**Similarity:** {finding.similarity_percentage:.1f}%")

        if finding.coupling_metrics:
            cm = finding.coupling_metrics
            lines.append(f"\n**Coupling Metrics:** Ca={cm.afferent_coupling}, Ce={cm.efferent_coupling}, I={cm.instability:.2f}")

        lines.append(f"\n**Remediation:** {finding.remediation}")
        lines.append(f"\n**Confidence:** {finding.confidence.value}")

        return "\n".join(lines) + "\n"

    def _get_severity_badge(self, severity: Severity) -> str:
        badges = {
            Severity.CRITICAL: "🔴 CRITICAL",
            Severity.HIGH: "🟠 HIGH",
            Severity.MEDIUM: "🟡 MEDIUM",
            Severity.LOW: "🟢 LOW",
        }
        return badges.get(severity, severity.value.upper())

    def _generate_files_section(
        self, consolidated: ConsolidatedPrincipalFindings
    ) -> str:
        sections = ["## Files"]

        if consolidated.files_analyzed:
            sections.append("\n### Analyzed Files\n")
            sorted_files = sorted(consolidated.files_analyzed)
            for f in sorted_files[:50]:
                sections.append(f"- `{f}`")
            if len(sorted_files) > 50:
                sections.append(f"\n*...and {len(sorted_files) - 50} more files*")

        if consolidated.files_omitted:
            sections.append("\n### Omitted Files\n")
            if consolidated.omitted_priority_1:
                sections.append("\n**Priority 1 (Critical):**")
                for f in consolidated.omitted_priority_1[:10]:
                    sections.append(f"- `{f}`")

            if consolidated.omitted_priority_2:
                sections.append("\n**Priority 2 (High):**")
                for f in consolidated.omitted_priority_2[:10]:
                    sections.append(f"- `{f}`")

            if consolidated.omitted_priority_3:
                sections.append("\n**Priority 3 (Normal):**")
                for f in consolidated.omitted_priority_3[:10]:
                    sections.append(f"- `{f}`")

        return "\n".join(sections)

    def _generate_recommendations(
        self, consolidated: ConsolidatedPrincipalFindings
    ) -> str:
        by_severity = consolidated.get_findings_by_severity()
        recommendations = ["## Recommendations"]

        if by_severity["critical"]:
            recommendations.append(
                "\n### 🔴 Immediate Action Required\n"
                "Address critical findings before merging or deploying:\n"
            )
            for f in by_severity["critical"][:3]:
                recommendations.append(f"- {f.description[:100]}")

        if by_severity["high"]:
            recommendations.append(
                "\n### 🟠 High Priority\n"
                "Schedule these for the current development cycle:\n"
            )
            for f in by_severity["high"][:5]:
                recommendations.append(f"- {f.description[:100]}")

        if consolidated.coupling_issues:
            recommendations.append(
                "\n### Architecture Review\n"
                "Consider architectural improvements:\n"
                "- Review module dependencies and reduce coupling\n"
                "- Apply dependency injection patterns\n"
                "- Break circular dependencies if detected"
            )

        if consolidated.dry_violations:
            recommendations.append(
                "\n### Code Deduplication\n"
                "Consider extracting duplicated code:\n"
                "- Create shared utility functions\n"
                "- Apply Extract Method refactoring\n"
                "- Use composition over duplication"
            )

        health_score = self._calculate_health_score(consolidated)
        if health_score >= 80:
            recommendations.append(
                "\n### 🎉 Overall Assessment\n"
                "The codebase is in good shape. Continue maintaining code quality."
            )
        elif health_score >= 60:
            recommendations.append(
                "\n### ⚠️ Overall Assessment\n"
                "The codebase needs attention. Plan refactoring sessions to address findings."
            )
        else:
            recommendations.append(
                "\n### 🚨 Overall Assessment\n"
                "The codebase requires significant refactoring. Prioritize addressing critical and high findings."
            )

        return "\n".join(recommendations)

    def _generate_expert_analysis_section(
        self, expert_analysis: dict[str, Any]
    ) -> str:
        sections = ["## Expert Analysis"]

        metadata = expert_analysis.get("metadata", {})
        if metadata:
            provider = metadata.get("provider", "unknown")
            model = metadata.get("model", "unknown")
            timestamp = metadata.get("timestamp", "unknown")
            execution_time = metadata.get("execution_time_seconds", 0)

            sections.append(
                f"\n**Provider:** {provider} ({model})  "
                f"\n**Analysis Time:** {execution_time:.2f}s  "
                f"\n**Timestamp:** {timestamp}"
            )

        overall = expert_analysis.get("overall_assessment", "")
        if overall:
            sections.append(f"\n### Overall Assessment\n\n{overall}")

        validated = expert_analysis.get("validated_findings", [])
        if validated:
            sections.append("\n### Validated Findings\n")
            sections.append(self._format_validated_findings_table(validated))

        additional = expert_analysis.get("additional_concerns", [])
        if additional:
            sections.append("\n### Additional Concerns Identified\n")
            sections.append(self._format_additional_concerns(additional))

        priorities = expert_analysis.get("remediation_priorities", [])
        if priorities:
            sections.append("\n### Remediation Priorities\n")
            sections.append(self._format_remediation_priorities(priorities))

        return "\n".join(sections)

    def _format_validated_findings_table(
        self, validated_findings: list[dict[str, Any]]
    ) -> str:
        if not validated_findings:
            return "No findings validated."

        lines = [
            "| Original ID | Confirmed | Original Severity | Adjusted Severity | Confidence | Reasoning |",
            "|-------------|-----------|-------------------|-------------------|------------|-----------|",
        ]

        for finding in validated_findings:
            original_id = finding.get("original_id", "N/A")
            confirmed = "✓" if finding.get("confirmed", False) else "✗"
            original_severity = finding.get("original_severity", "N/A")
            adjusted_severity = finding.get("adjusted_severity") or original_severity
            confidence = finding.get("confidence", 0)
            reasoning = finding.get("reasoning", "")[:100]

            lines.append(
                f"| {original_id} | {confirmed} | {original_severity} | "
                f"{adjusted_severity} | {confidence:.0%} | {reasoning}... |"
            )

        return "\n".join(lines)

    def _format_additional_concerns(
        self, additional_concerns: list[dict[str, Any]]
    ) -> str:
        if not additional_concerns:
            return "No additional concerns identified."

        sections = []
        for i, concern in enumerate(additional_concerns, 1):
            if isinstance(concern, str):
                sections.append(f"#### {i}. Additional Concern")
                sections.append(f"\n**Description:** {concern}")
                sections.append("")
                continue

            title = concern.get("title", "Untitled Concern")
            description = concern.get("description") or concern.get("concern", "No description")
            severity = concern.get("severity", "unknown").upper()
            affected_files = concern.get("affected_files", [])
            remediation = concern.get("remediation", "")
            confidence = concern.get("confidence", 0)

            sections.append(f"#### {i}. {title} ({severity})")
            sections.append(f"\n**Description:** {description}")

            if affected_files:
                files_str = ", ".join(f"`{f}`" for f in affected_files)
                sections.append(f"\n**Affected Files:** {files_str}")

            if remediation:
                sections.append(f"\n**Remediation:** {remediation}")

            if isinstance(confidence, (int, float)):
                sections.append(f"\n**Confidence:** {confidence:.0%}")
            sections.append("")

        return "\n".join(sections)

    def _format_remediation_priorities(
        self, remediation_priorities: list[dict[str, Any]]
    ) -> str:
        if not remediation_priorities:
            return "No specific remediation priorities identified."

        lines = []
        for priority_item in sorted(
            remediation_priorities, key=lambda x: x.get("priority", 999)
        ):
            priority = priority_item.get("priority", "?")
            action = priority_item.get("action", "No action specified")
            rationale = priority_item.get("rationale", "")
            effort = priority_item.get("estimated_effort", "unknown").upper()
            related = priority_item.get("related_findings", [])

            lines.append(f"**{priority}.** {action}")
            lines.append(f"   - **Rationale:** {rationale}")
            lines.append(f"   - **Estimated Effort:** {effort}")

            if related:
                related_str = ", ".join(related)
                lines.append(f"   - **Related Findings:** {related_str}")

            lines.append("")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        return """---

*This report was generated automatically by optix-mcp-server principal_audit tool.
For questions or concerns, please contact your engineering team.*"""
