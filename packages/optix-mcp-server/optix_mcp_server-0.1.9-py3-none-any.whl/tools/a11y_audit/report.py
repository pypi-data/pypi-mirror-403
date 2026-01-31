"""Report generator for accessibility audit results."""

from datetime import datetime
from typing import Any, Optional

from tools.a11y_audit.wcag import get_criterion
from tools.workflow.findings import ConsolidatedFindings


class A11yAuditReportGenerator:
    """Generates markdown accessibility audit reports from consolidated findings."""

    def __init__(self, project_name: str = "UI Accessibility Audit Report"):
        self._project_name = project_name

    def generate(
        self,
        consolidated: ConsolidatedFindings,
        expert_analysis: Optional[dict[str, Any]] = None
    ) -> str:
        """Generate a complete A11Y-AUDIT.MD markdown report.

        Args:
            consolidated: Aggregated findings from all workflow steps
            expert_analysis: Optional expert LLM analysis results

        Returns:
            Markdown string for A11Y-AUDIT.MD
        """
        sections = [
            self._generate_header(),
            self._generate_executive_summary(consolidated),
            self._generate_findings_by_severity(consolidated),
            self._generate_findings_by_wcag(consolidated),
            self._generate_files_examined(consolidated),
            self._generate_recommendations(consolidated),
        ]

        if expert_analysis:
            sections.append(self._generate_expert_analysis_section(expert_analysis))

        sections.append(self._generate_footer())
        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# {self._project_name}

**Generated:** {timestamp}
**Tool:** optix-mcp-server a11y_audit"""

    def _generate_executive_summary(self, consolidated: ConsolidatedFindings) -> str:
        """Generate executive summary section with WCAG compliance level."""
        summary = consolidated.get_audit_summary()
        severity_counts = summary["severity_counts"]

        wcag_compliance = self._determine_wcag_compliance(severity_counts)

        return f"""## Executive Summary

| Metric | Value |
|--------|-------|
| Total Violations | {summary['total_vulnerabilities']} |
| Critical | {severity_counts['critical']} |
| High | {severity_counts['high']} |
| Medium | {severity_counts['medium']} |
| Low | {severity_counts['low']} |
| Info | {severity_counts['info']} |
| Files Examined | {summary['files_examined']} |
| WCAG Compliance Level | **{wcag_compliance}** |"""

    def _determine_wcag_compliance(self, severity_counts: dict[str, int]) -> str:
        """Determine WCAG compliance level based on severity of findings.

        WCAG compliance logic:
        - Non-compliant: Has critical violations (Level A failures)
        - A: No critical, but has high violations (Level AA failures)
        - AA: No critical or high, but has medium violations
        - AAA: Only low or info level findings
        """
        if severity_counts["critical"] > 0:
            return "Non-compliant"
        elif severity_counts["high"] > 0:
            return "Level A"
        elif severity_counts["medium"] > 0:
            return "Level AA"
        return "Level AAA"

    def _generate_findings_by_severity(
        self, consolidated: ConsolidatedFindings
    ) -> str:
        """Generate findings grouped by severity."""
        by_severity = consolidated.get_findings_by_severity()
        sections = ["## Findings by Severity"]

        for severity in ["critical", "high", "medium", "low", "info"]:
            findings = by_severity[severity]
            if findings:
                sections.append(f"\n### {severity.upper()} Severity\n")
                for i, finding in enumerate(findings, 1):
                    sections.append(self._format_finding(finding, i))

        if not any(by_severity.values()):
            sections.append("\nNo accessibility violations found.")

        return "\n".join(sections)

    def _generate_findings_by_wcag(self, consolidated: ConsolidatedFindings) -> str:
        """Generate findings grouped by WCAG criterion."""
        by_severity = consolidated.get_findings_by_severity()

        all_findings = []
        for findings_list in by_severity.values():
            all_findings.extend(findings_list)

        if not all_findings:
            return "## Findings by WCAG Criterion\n\nNo WCAG violations found."

        by_wcag: dict[str, list[dict[str, Any]]] = {}
        for finding in all_findings:
            criterion = finding.get("wcag_criterion", "Unknown")
            if criterion not in by_wcag:
                by_wcag[criterion] = []
            by_wcag[criterion].append(finding)

        sections = ["## Findings by WCAG Criterion"]

        for criterion in sorted(by_wcag.keys()):
            criterion_info = get_criterion(criterion)
            criterion_name = criterion_info.get("name", "Unknown") if criterion_info else "Unknown"
            wcag_level = criterion_info.get("level", "") if criterion_info else ""
            level_str = f" (Level {wcag_level})" if wcag_level else ""

            sections.append(f"\n### WCAG {criterion}: {criterion_name}{level_str}\n")

            findings = by_wcag[criterion]
            for finding in findings:
                severity = finding.get("severity", "unknown").upper()
                description = finding.get("description", "No description")
                sections.append(f"- {description} ({severity})")

        return "\n".join(sections)

    def _format_finding(self, finding: dict[str, Any], index: int) -> str:
        """Format a single finding for the report."""
        category = finding.get("category", "Unknown Category")
        wcag_criterion = finding.get("wcag_criterion", "N/A")

        lines = [f"#### {index}. {category} - WCAG {wcag_criterion}"]

        description = finding.get("description", "No description provided")
        lines.append(f"\n**Description:** {description}")

        affected_files = finding.get("affected_files", [])
        if affected_files:
            files_str = ", ".join(f"`{f}`" for f in affected_files)
            lines.append(f"\n**Affected Files:** {files_str}")

        affected_elements = finding.get("affected_elements", [])
        if affected_elements:
            elements_str = ", ".join(f"`{e}`" for e in affected_elements)
            lines.append(f"\n**Affected Elements:** {elements_str}")

        remediation = finding.get("remediation")
        if remediation:
            lines.append(f"\n**Remediation:** {remediation}")

        wcag_level = finding.get("wcag_level")
        if wcag_level:
            lines.append(f"\n**WCAG Level:** {wcag_level}")

        return "\n".join(lines)

    def _generate_files_examined(self, consolidated: ConsolidatedFindings) -> str:
        """Generate files examined section."""
        files = sorted(consolidated.files_checked)
        if not files:
            return "## Files Examined\n\nNo files were examined."

        file_list = "\n".join(f"- `{f}`" for f in files)
        return f"""## Files Examined

{file_list}"""

    def _generate_recommendations(self, consolidated: ConsolidatedFindings) -> str:
        """Generate recommendations section based on findings."""
        by_severity = consolidated.get_findings_by_severity()
        recommendations = []

        if by_severity["critical"]:
            recommendations.append(
                "1. **IMMEDIATE ACTION REQUIRED:** Address all critical accessibility barriers blocking keyboard-only and screen reader users before deployment."
            )

        if by_severity["high"]:
            recommendations.append(
                "2. **HIGH PRIORITY:** Fix high-severity accessibility issues within the current sprint to ensure WCAG Level A compliance."
            )

        if by_severity["medium"]:
            recommendations.append(
                "3. **MEDIUM PRIORITY:** Improve medium-severity issues in upcoming releases to achieve WCAG Level AA compliance."
            )

        if by_severity["low"]:
            recommendations.append(
                "4. **LOW PRIORITY:** Address low-severity issues as part of regular maintenance to enhance overall accessibility."
            )

        if not recommendations:
            recommendations.append(
                "No critical accessibility issues found. Continue following WCAG best practices and conduct regular accessibility audits."
            )

        return "## Recommendations\n\n" + "\n".join(recommendations)

    def _generate_expert_analysis_section(
        self, expert_analysis: dict[str, Any]
    ) -> str:
        """Generate expert analysis section.

        Args:
            expert_analysis: Expert LLM validation results

        Returns:
            Markdown string for expert analysis section
        """
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
        """Format validated findings as a table."""
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
        """Format additional concerns identified by expert."""
        if not additional_concerns:
            return "No additional concerns identified."

        sections = []
        for i, concern in enumerate(additional_concerns, 1):
            title = concern.get("title", "Untitled Concern")
            description = concern.get("description", "No description")
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

            sections.append(f"\n**Confidence:** {confidence:.0%}")
            sections.append("")

        return "\n".join(sections)

    def _format_remediation_priorities(
        self, remediation_priorities: list[dict[str, Any]]
    ) -> str:
        """Format remediation priorities."""
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
        """Generate report footer."""
        return """---

*This report was generated automatically by optix-mcp-server a11y_audit tool.
For questions or concerns, please contact your accessibility team.*"""
