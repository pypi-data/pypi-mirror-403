"""Comment formatting logic for PR comments.

Provides functions to format audit findings into GitHub PR comment markdown.
"""

from typing import Any

from tools.pr_comment.models import FormattedFinding

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def truncate_description(description: str, max_words: int = 5) -> str:
    """Truncate description to max words.

    Args:
        description: Original description text
        max_words: Maximum number of words allowed

    Returns:
        Truncated description with ellipsis if needed
    """
    words = description.split()
    if len(words) <= max_words:
        return description
    return " ".join(words[:max_words]) + "..."


def format_file_reference(file_path: str, line_number: int | None, file_link: str | None = None) -> str:
    """Format file path with optional line number and link.

    Args:
        file_path: Path to the file
        line_number: Optional line number
        file_link: Optional GitHub permalink

    Returns:
        Formatted file reference string
    """
    if line_number:
        location = f"`{file_path}:{line_number}`"
    else:
        location = f"`{file_path}`"

    if file_link:
        return f"[{location}]({file_link})"
    return location


def format_finding(finding: FormattedFinding) -> str:
    """Format a single finding for the PR comment table.

    Args:
        finding: The formatted finding to render

    Returns:
        Formatted table row string
    """
    file_ref = format_file_reference(finding.file_path, finding.line_number, finding.file_link)
    short_desc = truncate_description(finding.description)
    return f"| {file_ref} | {short_desc} |"


def format_severity_section(severity: str, findings: list[FormattedFinding]) -> str:
    """Format a severity section with table of findings.

    Args:
        severity: Severity level name
        findings: List of findings for this severity

    Returns:
        Markdown section with table
    """
    if not findings:
        return ""

    lines = [
        f"### {severity.capitalize()} ({len(findings)})",
        "",
        "| File | Description |",
        "|------|-------------|",
    ]

    for finding in findings:
        lines.append(format_finding(finding))

    return "\n".join(lines)


def parse_issue_to_finding(issue: dict[str, Any], file_link_builder: Any = None) -> FormattedFinding:
    """Parse an issue dict into a FormattedFinding.

    Args:
        issue: Dictionary with issue data from workflow
        file_link_builder: Optional callable to build file links

    Returns:
        FormattedFinding instance
    """
    file_path = ""
    line_number = None
    affected_files = issue.get("affected_files", [])
    location = issue.get("location", "")

    if affected_files and len(affected_files) > 0:
        file_entry = affected_files[0]
        if isinstance(file_entry, dict):
            file_path = file_entry.get("file", file_entry.get("path", ""))
            line_number = file_entry.get("line") or file_entry.get("line_number")
        elif isinstance(file_entry, str):
            if ":" in file_entry:
                parts = file_entry.rsplit(":", 1)
                file_path = parts[0]
                try:
                    line_number = int(parts[1])
                except ValueError:
                    file_path = file_entry
            else:
                file_path = file_entry
    elif location:
        if ":" in location:
            parts = location.rsplit(":", 1)
            file_path = parts[0]
            try:
                line_number = int(parts[1])
            except ValueError:
                file_path = location
        else:
            file_path = location

    if not file_path:
        file_path = issue.get("file", issue.get("path", "unknown"))

    if not line_number:
        line_number = issue.get("line") or issue.get("line_number")

    description = issue.get("description", issue.get("title", "No description"))
    severity = issue.get("severity", "medium").lower()

    file_link = None
    if file_link_builder and file_path and file_path != "unknown":
        file_link = file_link_builder(file_path, line_number)

    return FormattedFinding(
        file_path=file_path,
        line_number=line_number,
        description=description,
        severity=severity,
        file_link=file_link,
    )


def group_findings_by_severity(findings: list[FormattedFinding]) -> dict[str, list[FormattedFinding]]:
    """Group findings by severity level.

    Args:
        findings: List of formatted findings

    Returns:
        Dictionary mapping severity to list of findings
    """
    grouped: dict[str, list[FormattedFinding]] = {s: [] for s in SEVERITY_ORDER}

    for finding in findings:
        severity = finding.severity.lower()
        if severity in grouped:
            grouped[severity].append(finding)
        else:
            grouped["medium"].append(finding)

    return grouped


def format_comment(findings: list[FormattedFinding], lens_name: str = "Audit") -> str:
    """Build full markdown comment with severity sections.

    Args:
        findings: List of formatted findings
        lens_name: Name of the audit lens (e.g., "Security", "A11Y")

    Returns:
        Complete markdown comment body
    """
    if not findings:
        return f"## {lens_name} Audit Findings\n\nNo findings to report."

    grouped = group_findings_by_severity(findings)
    total = len(findings)

    lines = [
        f"## {lens_name} Audit Findings",
        "",
        f"**Total Findings:** {total}",
        "",
    ]

    for severity in SEVERITY_ORDER:
        section = format_severity_section(severity, grouped[severity])
        if section:
            lines.append(section)
            lines.append("")

    lines.append("---")
    lines.append("*Generated by optix-mcp-server*")

    return "\n".join(lines)
