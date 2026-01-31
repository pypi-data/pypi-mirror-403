"""Report generator for DevOps audit results."""

from datetime import datetime
from typing import Any

from tools.devops_audit.domains import DevOpsCategory
from tools.devops_audit.finding import ConsolidatedDevOpsFindings
from tools.workflow.findings import ConsolidatedFindings


class DevOpsAuditReportGenerator:
    """Generates markdown DevOps audit reports from consolidated findings."""

    def __init__(self, project_name: str = "DevOps Infrastructure Audit"):
        self._project_name = project_name

    def generate(
        self,
        consolidated: ConsolidatedFindings,
        validation_metadata: dict[str, Any] | None = None,
        expert_analysis: dict[str, Any] | None = None
    ) -> str:
        """Generate a complete DEVOPS_AUDIT_REPORT.md markdown report.

        Args:
            consolidated: Aggregated findings from all workflow steps
            validation_metadata: Optional validation summary from multi-LLM validation
            expert_analysis: Optional expert LLM analysis results

        Returns:
            Markdown string for DEVOPS_AUDIT_REPORT.md
        """
        sections = [
            self._generate_header(),
            self._generate_executive_summary(consolidated),
            self._generate_findings_summary(consolidated),
            self._generate_findings_by_severity(consolidated),
        ]

        if isinstance(consolidated, ConsolidatedDevOpsFindings):
            sections.append(self._generate_findings_by_category(consolidated))
            sections.append(self._generate_artifact_coverage(consolidated))
            sections.append(self._generate_missing_context(consolidated))

        if validation_metadata:
            sections.append(self._generate_validation_metadata(validation_metadata))

        if expert_analysis:
            sections.append(self._generate_expert_analysis_section(expert_analysis))

        sections.extend([
            self._generate_files_examined(consolidated),
            self._generate_recommendations(consolidated),
            self._generate_footer(),
        ])

        return "\n\n".join(filter(None, sections))

    def _generate_header(self) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# {self._project_name}

**Generated:** {timestamp}
**Tool:** optix-mcp-server devops_audit"""

    def _generate_executive_summary(self, consolidated: ConsolidatedFindings) -> str:
        """Generate executive summary section."""
        if isinstance(consolidated, ConsolidatedDevOpsFindings):
            summary = consolidated.get_devops_audit_summary()
        else:
            summary = consolidated.get_audit_summary()

        severity_counts = summary.get("severity_counts", summary)
        risk_level = self._determine_risk_level(severity_counts)

        return f"""## Executive Summary

| Metric | Value |
|--------|-------|
| Total Findings | {summary.get('total_findings', len(consolidated.issues_found))} |
| Critical | {severity_counts.get('critical', 0)} |
| High | {severity_counts.get('high', 0)} |
| Medium | {severity_counts.get('medium', 0)} |
| Low | {severity_counts.get('low', 0)} |
| Files Examined | {len(consolidated.files_checked)} |
| Overall Risk Level | **{risk_level}** |"""

    def _determine_risk_level(self, severity_counts: dict[str, int]) -> str:
        """Determine overall risk level from severity counts."""
        if severity_counts.get("critical", 0) > 0:
            return "CRITICAL"
        elif severity_counts.get("high", 0) > 0:
            return "HIGH"
        elif severity_counts.get("medium", 0) > 0:
            return "MEDIUM"
        elif severity_counts.get("low", 0) > 0:
            return "LOW"
        return "NONE"

    def _generate_findings_summary(self, consolidated: ConsolidatedFindings) -> str:
        """Generate summary statistics section."""
        by_severity = consolidated.get_findings_by_severity()

        lines = ["## Findings Summary", ""]
        lines.append("### By Severity")
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = len(by_severity.get(severity, []))
            emoji = self._get_severity_emoji(severity)
            lines.append(f"- {emoji} **{severity.upper()}**: {count}")

        return "\n".join(lines)

    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji indicator for severity level."""
        return {
            "critical": "\u26d4",
            "high": "\u26a0\ufe0f",
            "medium": "\u2139\ufe0f",
            "low": "\u2139\ufe0f",
            "info": "\u2139\ufe0f",
        }.get(severity, "")

    def _generate_findings_by_severity(self, consolidated: ConsolidatedFindings) -> str:
        """Generate findings grouped by severity."""
        by_severity = consolidated.get_findings_by_severity()
        sections = ["## Detailed Findings"]

        for severity in ["critical", "high", "medium", "low", "info"]:
            findings = by_severity.get(severity, [])
            if findings:
                sections.append(f"\n### {severity.upper()} Severity\n")
                for i, finding in enumerate(findings, 1):
                    sections.append(self._format_finding(finding, i))

        if not any(by_severity.values()):
            sections.append("\nNo security or operational issues found.")

        return "\n".join(sections)

    def _generate_findings_by_category(
        self, consolidated: ConsolidatedDevOpsFindings
    ) -> str:
        """Generate findings grouped by DevOps category."""
        by_category = consolidated.get_findings_by_category()
        sections = ["## Findings by Category"]

        for category in DevOpsCategory:
            findings = by_category.get(category, [])
            sections.append(f"\n### {category.display_name}")
            sections.append(f"**Count:** {len(findings)}")

            if findings:
                for i, finding in enumerate(findings, 1):
                    sections.append(f"\n{i}. **{finding.description}**")
                    sections.append(f"   - Severity: {finding.severity.value.upper()}")
                    if finding.affected_files:
                        files_str = ", ".join(f"`{f}`" for f in finding.affected_files)
                        sections.append(f"   - Files: {files_str}")
                    if finding.remediation:
                        sections.append(f"   - Fix: {finding.remediation}")

        return "\n".join(sections)

    def _format_finding(self, finding: dict[str, Any], index: int) -> str:
        """Format a single finding for the report."""
        category = finding.get("category", "Unknown")
        if hasattr(category, "display_name"):
            category = category.display_name
        elif isinstance(category, str):
            category_map = {
                "dockerfile": "Dockerfile Security",
                "cicd": "CI/CD Configuration",
                "dependency": "Dependency Management",
            }
            category = category_map.get(category.lower(), category)

        lines = [f"#### {index}. {category}"]

        description = finding.get("description", "No description provided")
        lines.append(f"\n**Description:** {description}")

        affected_files = finding.get("affected_files", [])
        if affected_files:
            files_str = ", ".join(f"`{f}`" for f in affected_files)
            lines.append(f"\n**Affected Files:** {files_str}")

        line_numbers = finding.get("line_numbers", [])
        if line_numbers:
            lines.append(f"\n**Lines:** {', '.join(map(str, line_numbers))}")

        remediation = finding.get("remediation")
        if remediation:
            lines.append(f"\n**Remediation:** {remediation}")

        confidence = finding.get("confidence")
        if confidence:
            lines.append(f"\n**Confidence:** {confidence}")

        return "\n".join(lines)

    def _generate_artifact_coverage(
        self, consolidated: ConsolidatedDevOpsFindings
    ) -> str:
        """Generate artifact coverage section."""
        coverage = consolidated.get_artifact_coverage_summary()

        lines = ["## Artifact Coverage", ""]

        def format_artifact_section(name: str, data: dict) -> list[str]:
            total = data["analyzed"] + data["omitted"]
            if total == 0:
                return [f"**{name}:** No artifacts found"]
            pct = (data["analyzed"] / total * 100) if total > 0 else 0
            section = [f"**{name}:** {data['analyzed']} / {total} ({pct:.0f}%)"]
            if data.get("files"):
                section.append(f"  - Analyzed: {', '.join(f'`{f}`' for f in data['files'])}")
            if data["omitted"] > 0:
                section.append(f"  - Omitted: {data['omitted']} files (time budget exceeded)")
            return section

        lines.extend(format_artifact_section("Dockerfiles", coverage["dockerfiles"]))
        lines.append("")
        lines.extend(format_artifact_section("Workflows", coverage["workflows"]))
        lines.append("")
        lines.extend(format_artifact_section("Package Files", coverage["package_files"]))

        return "\n".join(lines)

    def _generate_missing_context(
        self, consolidated: ConsolidatedDevOpsFindings
    ) -> str:
        """Generate missing context section."""
        missing = consolidated.get_missing_context_summary()

        if not missing["missing_lockfiles"] and not missing["other_missing_context"]:
            return ""

        lines = ["## Missing Context", ""]
        lines.append("The following files were requested but not provided:")

        if missing["missing_lockfiles"]:
            lines.append("\n**Missing Lockfiles:**")
            for f in missing["missing_lockfiles"]:
                lines.append(f"- `{f}`")
            lines.append("\n*Note: Without lockfiles, transitive dependency analysis is limited.*")

        if missing["other_missing_context"]:
            lines.append("\n**Other Missing Files:**")
            for f in missing["other_missing_context"]:
                lines.append(f"- `{f}`")

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

        if by_severity.get("critical"):
            recommendations.append(
                "1. **IMMEDIATE ACTION REQUIRED:** Address all critical findings "
                "(running as root, hardcoded secrets, missing lockfiles) before deployment."
            )

        if by_severity.get("high"):
            recommendations.append(
                "2. **HIGH PRIORITY:** Fix high-severity issues (unpinned images, "
                "unpinned actions, missing permissions blocks) within current sprint."
            )

        if by_severity.get("medium"):
            recommendations.append(
                "3. **MEDIUM PRIORITY:** Plan remediation of medium-severity issues "
                "in upcoming releases."
            )

        if by_severity.get("low"):
            recommendations.append(
                "4. **LOW PRIORITY:** Address low-severity issues as part of "
                "regular maintenance."
            )

        if not recommendations:
            recommendations.append(
                "No critical infrastructure issues found. Continue regular "
                "DevOps security practices."
            )

        recommendations.append(
            "\n**General Recommendations:**\n"
            "- Implement version pinning across all infrastructure layers\n"
            "- Enable automated dependency updates (Dependabot/Renovate)\n"
            "- Add HEALTHCHECK to all Dockerfiles for long-running services\n"
            "- Use OIDC authentication instead of static credentials in CI/CD"
        )

        return "## Recommendations\n\n" + "\n".join(recommendations)

    def _generate_validation_metadata(self, metadata: dict[str, Any]) -> str:
        """Generate validation metadata section."""
        if not metadata:
            return ""

        lines = ["## Validation Metadata", ""]
        lines.append("**Multi-LLM Consensus Validation**")
        lines.append("")

        total = metadata.get("total_findings", 0)
        validated = metadata.get("validated_with_llm", 0)
        consensus = metadata.get("consensus_reached", 0)
        disagreements = metadata.get("disagreements", 0)
        severity_changes = metadata.get("severity_changes", 0)
        llm_calls = metadata.get("llm_calls_total", 0)

        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Findings | {total} |")
        lines.append(f"| Validated with LLM | {validated} |")
        lines.append(f"| Consensus Reached | {consensus} |")
        lines.append(f"| Disagreements | {disagreements} |")
        lines.append(f"| Severity Changes | {severity_changes} |")
        lines.append(f"| Total LLM Calls | {llm_calls} |")

        calls_by_model = metadata.get("llm_calls_by_model", {})
        if calls_by_model:
            lines.append("")
            lines.append("**Calls by Model:**")
            for model, count in calls_by_model.items():
                lines.append(f"- {model}: {count}")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return """---

*This report was generated automatically by optix-mcp-server devops_audit tool.
For questions or concerns, please contact your DevOps or security team.*"""

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
            additional_concerns: List of additional concern dictionaries

        Returns:
            Markdown formatted string
        """
        if not additional_concerns:
            return "No additional concerns identified."

        sections = []
        for i, concern in enumerate(additional_concerns, 1):
            # Handle case where concern is a string instead of dict
            if isinstance(concern, str):
                sections.append(f"{i}. {concern}")
                sections.append("")
                continue

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
