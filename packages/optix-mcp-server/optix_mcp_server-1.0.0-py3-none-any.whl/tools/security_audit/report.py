"""Report generator for security audit results."""

from datetime import datetime
from typing import Any, Optional

from tools.workflow.findings import ConsolidatedFindings


class AuditReportGenerator:
    """Generates markdown audit reports from consolidated findings."""

    def __init__(self, project_name: str = "Security Audit"):
        self._project_name = project_name

    def generate(
        self,
        consolidated: ConsolidatedFindings,
        expert_analysis: Optional[dict[str, Any]] = None
    ) -> str:
        """Generate a complete AUDIT.MD markdown report.

        Args:
            consolidated: Aggregated findings from all workflow steps
            expert_analysis: Optional expert LLM analysis results

        Returns:
            Markdown string for AUDIT.MD
        """
        sections = [
            self._generate_header(),
            self._generate_executive_summary(consolidated),
            self._generate_findings_by_severity(consolidated),
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
**Tool:** optix-mcp-server security_audit"""

    def _generate_executive_summary(self, consolidated: ConsolidatedFindings) -> str:
        """Generate executive summary section."""
        summary = consolidated.get_audit_summary()
        severity_counts = summary["severity_counts"]

        risk_level = self._determine_risk_level(severity_counts)

        return f"""## Executive Summary

| Metric | Value |
|--------|-------|
| Total Vulnerabilities | {summary['total_vulnerabilities']} |
| Critical | {severity_counts['critical']} |
| High | {severity_counts['high']} |
| Medium | {severity_counts['medium']} |
| Low | {severity_counts['low']} |
| Info | {severity_counts['info']} |
| Files Examined | {summary['files_examined']} |
| Overall Risk Level | **{risk_level}** |"""

    def _determine_risk_level(self, severity_counts: dict[str, int]) -> str:
        """Determine overall risk level from severity counts."""
        if severity_counts["critical"] > 0:
            return "CRITICAL"
        elif severity_counts["high"] > 0:
            return "HIGH"
        elif severity_counts["medium"] > 0:
            return "MEDIUM"
        elif severity_counts["low"] > 0:
            return "LOW"
        return "NONE"

    def _generate_findings_by_severity(
        self, consolidated: ConsolidatedFindings
    ) -> str:
        """Generate findings grouped by severity."""
        by_severity = consolidated.get_findings_by_severity()
        sections = ["## Findings"]

        for severity in ["critical", "high", "medium", "low", "info"]:
            findings = by_severity[severity]
            if findings:
                sections.append(f"\n### {severity.upper()} Severity\n")
                for i, finding in enumerate(findings, 1):
                    sections.append(self._format_finding(finding, i))

        if not any(by_severity.values()):
            sections.append("\nNo security vulnerabilities found.")

        return "\n".join(sections)

    def _format_finding(self, finding: dict[str, Any], index: int) -> str:
        """Format a single finding for the report."""
        lines = [f"#### {index}. {finding.get('category', 'Unknown Category')}"]

        description = finding.get("description", "No description provided")
        lines.append(f"\n**Description:** {description}")

        affected_files = finding.get("affected_files", [])
        if affected_files:
            files_str = ", ".join(f"`{f}`" for f in affected_files)
            lines.append(f"\n**Affected Files:** {files_str}")

        remediation = finding.get("remediation")
        if remediation:
            lines.append(f"\n**Remediation:** {remediation}")

        cwe_id = finding.get("cwe_id")
        if cwe_id:
            lines.append(f"\n**CWE:** [{cwe_id}](https://cwe.mitre.org/data/definitions/{cwe_id.replace('CWE-', '')}.html)")

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
                "1. **IMMEDIATE ACTION REQUIRED:** Address all critical vulnerabilities before deployment."
            )

        if by_severity["high"]:
            recommendations.append(
                "2. **HIGH PRIORITY:** Schedule remediation of high-severity issues within the current sprint."
            )

        if by_severity["medium"]:
            recommendations.append(
                "3. **MEDIUM PRIORITY:** Plan remediation of medium-severity issues in upcoming releases."
            )

        if by_severity["low"]:
            recommendations.append(
                "4. **LOW PRIORITY:** Address low-severity issues as part of regular maintenance."
            )

        if not recommendations:
            recommendations.append(
                "No critical security issues found. Continue regular security practices."
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
        """Format validated findings as a table.

        Args:
            validated_findings: List of validated finding dictionaries

        Returns:
            Markdown table string
        """
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
        """Format additional concerns identified by expert.

        Args:
            additional_concerns: List of additional concern dictionaries or strings

        Returns:
            Markdown formatted string
        """
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
        """Format remediation priorities.

        Args:
            remediation_priorities: List of prioritized action dictionaries

        Returns:
            Markdown formatted string
        """
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

*This report was generated automatically by optix-mcp-server security_audit tool.
For questions or concerns, please contact your security team.*"""
