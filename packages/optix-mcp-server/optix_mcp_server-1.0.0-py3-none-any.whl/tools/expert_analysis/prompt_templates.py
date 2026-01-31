"""
LLM Prompt Templates for Expert Analysis

Generic prompt templates that work across all audit types.
"""

from typing import Any

EXPERT_ANALYSIS_PROMPT = """
You are a senior {audit_type} expert reviewing findings from an automated audit.

## Audit Context
- Audit Type: {audit_type}
- Files Examined: {file_count}
- Findings Count: {finding_count}
- Confidence Level: {confidence}
{category_guidance}

## Findings Summary
{findings_summary}

## Your Tasks
1. **Validate each finding**: Confirm severity, identify false positives
2. **Identify additional concerns**: Issues the automated audit may have missed
3. **Prioritize remediation**: Order actions by impact and effort
4. **Provide overall assessment**: Summary of current {audit_type} posture

## Response Format
Return JSON with:
{{
    "validated_findings": [
        {{
            "original_id": "string",
            "confirmed": boolean,
            "adjusted_severity": "critical|high|medium|low|info",
            "reasoning": "string"
        }}
    ],
    "additional_concerns": [
        {{
            "title": "string",
            "description": "string",
            "severity": "critical|high|medium|low",{category_field}
            "affected_files": ["string"],
            "remediation": "string"
        }}
    ],
    "remediation_priorities": [
        {{
            "priority": number,
            "action": "string",
            "rationale": "string",
            "estimated_effort": "low|medium|high"
        }}
    ],
    "overall_assessment": "string"
}}
"""

CONSENSUS_VALIDATION_PROMPT = """
You are validating a {severity} severity finding from an automated {audit_type} audit.

## Finding Details
{finding_json}

## Context
- Files: {affected_files}
- Category: {category}
- Initial Confidence: {confidence}

## Your Task
Assess whether this finding is:
1. **Confirmed**: True positive requiring action
2. **False Positive**: Not actually a {audit_type} issue
3. **Severity Adjustment**: True positive but different severity

Return JSON:
{{
    "assessment": "confirmed|false_positive|severity_adjustment",
    "adjusted_severity": "critical|high|medium|low|info|none",
    "confidence": 0.0-1.0,
    "reasoning": "string"
}}
"""


def build_analysis_prompt(
    findings: list[dict],
    audit_type: str,
    consolidated: Any
) -> str:
    """
    Build LLM prompt from consolidated findings.

    Args:
        findings: List of findings to analyze
        audit_type: Type of audit (security, devops, accessibility, principal_audit)
        consolidated: ConsolidatedFindings object

    Returns:
        Formatted prompt string for LLM
    """
    # Customize context based on audit type
    audit_context = _get_audit_context(audit_type)

    # Build findings summary
    findings_summary = _format_findings_summary(findings)

    # Get confidence level
    confidence = "unknown"
    if hasattr(consolidated, "confidence"):
        confidence = str(consolidated.confidence.value if hasattr(consolidated.confidence, "value") else consolidated.confidence)

    # Format file count
    file_count = len(consolidated.files_checked) if hasattr(consolidated, "files_checked") else 0

    # Build category guidance if valid_categories are specified
    category_guidance = ""
    category_field = ""
    if "valid_categories" in audit_context:
        valid_cats = audit_context["valid_categories"]
        category_guidance = f"\n- Valid Categories: {', '.join(valid_cats)}"
        category_field = f'\n            "category": "{" | ".join(valid_cats)}",'

    # Build prompt
    return EXPERT_ANALYSIS_PROMPT.format(
        audit_type=audit_context["domain"],
        file_count=file_count,
        finding_count=len(findings),
        confidence=confidence,
        findings_summary=findings_summary,
        category_guidance=category_guidance,
        category_field=category_field,
    )


def _get_audit_context(audit_type: str) -> dict[str, str]:
    """
    Get audit-specific context for prompt customization.

    Args:
        audit_type: Type of audit

    Returns:
        Dictionary with domain and focus areas
    """
    contexts = {
        "security": {
            "domain": "security",
            "focus": "vulnerabilities, attack vectors, data exposure",
        },
        "devops": {
            "domain": "DevOps",
            "focus": "infrastructure risks, CI/CD issues, deployment security",
        },
        "accessibility": {
            "domain": "accessibility",
            "focus": "WCAG compliance, usability barriers, assistive technology support",
        },
        "principal_audit": {
            "domain": "code quality and architecture",
            "focus": "complexity, duplication, coupling, maintainability",
            "valid_categories": [
                "complexity",
                "dry_violation",
                "coupling",
                "separation_of_concerns",
                "maintainability_risk"
            ]
        },
    }
    return contexts.get(audit_type.lower(), {"domain": audit_type, "focus": "general issues"})


def _format_findings_summary(findings: list[dict]) -> str:
    """
    Format findings list for prompt inclusion.

    Args:
        findings: List of finding dictionaries

    Returns:
        Formatted markdown string
    """
    if not findings:
        return "No findings to analyze."

    lines = []
    for i, finding in enumerate(findings, 1):
        severity = finding.get("severity", "unknown")
        category = finding.get("category", "general")
        description = finding.get("description", "No description")

        lines.append(f"### Finding {i}: {category.upper()}")
        lines.append(f"**Severity**: {severity}")
        lines.append(f"**Description**: {description}")

        if "affected_files" in finding and finding["affected_files"]:
            files = ", ".join(finding["affected_files"][:3])
            if len(finding["affected_files"]) > 3:
                files += f" (+{len(finding['affected_files']) - 3} more)"
            lines.append(f"**Affected Files**: {files}")

        lines.append("")  # Blank line between findings

    return "\n".join(lines)
