"""Security-specific step guidance for the audit workflow."""

from dataclasses import dataclass, field
from typing import Optional

from tools.security_audit.domains import SecurityStepDomain
from tools.workflow.confidence import ConfidenceLevel


TOTAL_STEPS = 6


@dataclass
class SecurityAuditGuidance:
    """Step-specific guidance for security audit workflow."""

    step_number: int
    domain: SecurityStepDomain
    required_actions: list[str] = field(default_factory=list)
    next_steps: str = ""
    focus_areas: list[str] = field(default_factory=list)


def get_mandatory_pause_instruction(tool_name: str, step_number: int) -> str:
    """Generate the MANDATORY pause instruction for next_steps guidance.

    Args:
        tool_name: Name of the tool
        step_number: Current step number

    Returns:
        Instruction text for client to NOT call tool immediately
    """
    return (
        f"MANDATORY: DO NOT call the {tool_name} tool again immediately. "
        f"You MUST first examine the code files thoroughly using appropriate tools. "
        f"Only call {tool_name} again AFTER completing your security investigation for this step. "
        f"When you call {tool_name} next time, use step_number: {step_number + 1} and report "
        f"specific files examined, vulnerabilities found, and security assessments discovered."
    )


def get_step_guidance(
    step_number: int,
    confidence: ConfidenceLevel,
    tool_name: str = "security_audit",
) -> SecurityAuditGuidance:
    """Get security-specific guidance for a given step.

    Args:
        step_number: Current step (1-6)
        confidence: Client's current confidence level
        tool_name: Name of the tool for guidance messages

    Returns:
        SecurityAuditGuidance with domain-specific actions
    """
    domain = SecurityStepDomain.for_step(step_number)
    guidance_func = _STEP_GUIDANCE_MAP.get(step_number, _get_default_guidance)
    guidance = guidance_func(step_number, confidence, tool_name)
    guidance.domain = domain
    return guidance


def _get_step_1_guidance(
    step_number: int, confidence: ConfidenceLevel, tool_name: str
) -> SecurityAuditGuidance:
    """Step 1: Reconnaissance guidance."""
    return SecurityAuditGuidance(
        step_number=step_number,
        domain=SecurityStepDomain.RECONNAISSANCE,
        required_actions=[
            "Identify the application type and purpose",
            "Map the technology stack (languages, frameworks, databases)",
            "Identify entry points (APIs, web interfaces, file inputs)",
            "Document the security scope and boundaries",
        ],
        next_steps=get_mandatory_pause_instruction(tool_name, step_number),
        focus_areas=[
            "Application architecture",
            "Technology stack",
            "Entry points",
            "Security perimeter",
        ],
    )


def _get_step_2_guidance(
    step_number: int, confidence: ConfidenceLevel, tool_name: str
) -> SecurityAuditGuidance:
    """Step 2: Authentication & Authorization guidance."""
    return SecurityAuditGuidance(
        step_number=step_number,
        domain=SecurityStepDomain.AUTH_AUTHZ,
        required_actions=[
            "Analyze authentication mechanisms (login, session, tokens)",
            "Review session management implementation",
            "Check for authorization bypasses and privilege escalation",
            "Examine password storage and credential handling",
        ],
        next_steps=get_mandatory_pause_instruction(tool_name, step_number),
        focus_areas=[
            "Authentication flows",
            "Session management",
            "Authorization controls",
            "Credential storage",
        ],
    )


def _get_step_3_guidance(
    step_number: int, confidence: ConfidenceLevel, tool_name: str
) -> SecurityAuditGuidance:
    """Step 3: Input Validation & Cryptography guidance."""
    return SecurityAuditGuidance(
        step_number=step_number,
        domain=SecurityStepDomain.INPUT_VALIDATION,
        required_actions=[
            "Examine input validation and sanitization mechanisms",
            "Check for injection vulnerabilities (SQL, XSS, command)",
            "Review cryptographic implementations and key management",
            "Assess data encoding and output encoding practices",
        ],
        next_steps=get_mandatory_pause_instruction(tool_name, step_number),
        focus_areas=[
            "Input validation",
            "Injection points",
            "Cryptography usage",
            "Data encoding",
        ],
    )


def _get_step_4_guidance(
    step_number: int, confidence: ConfidenceLevel, tool_name: str
) -> SecurityAuditGuidance:
    """Step 4: OWASP Top 10 guidance."""
    return SecurityAuditGuidance(
        step_number=step_number,
        domain=SecurityStepDomain.OWASP_TOP_10,
        required_actions=[
            "A01: Check for Broken Access Control vulnerabilities",
            "A02: Review Cryptographic Failures",
            "A03: Look for Injection vulnerabilities",
            "A04-A10: Systematically check remaining OWASP categories",
        ],
        next_steps=get_mandatory_pause_instruction(tool_name, step_number),
        focus_areas=[
            "OWASP A01-A03 (Critical)",
            "OWASP A04-A07 (High)",
            "OWASP A08-A10 (Medium)",
            "Security misconfiguration",
        ],
    )


def _get_step_5_guidance(
    step_number: int, confidence: ConfidenceLevel, tool_name: str
) -> SecurityAuditGuidance:
    """Step 5: Dependencies & Configuration guidance."""
    return SecurityAuditGuidance(
        step_number=step_number,
        domain=SecurityStepDomain.DEPENDENCIES,
        required_actions=[
            "Audit third-party dependencies for known vulnerabilities",
            "Review configuration hardening (CORS, headers, TLS)",
            "Check for secrets in code or configuration files",
            "Assess error handling and information disclosure",
        ],
        next_steps=get_mandatory_pause_instruction(tool_name, step_number),
        focus_areas=[
            "Dependency vulnerabilities",
            "Security headers",
            "Secrets management",
            "Error handling",
        ],
    )


def _get_step_6_guidance(
    step_number: int, confidence: ConfidenceLevel, tool_name: str
) -> SecurityAuditGuidance:
    """Step 6: Compliance & Remediation guidance."""
    return SecurityAuditGuidance(
        step_number=step_number,
        domain=SecurityStepDomain.COMPLIANCE,
        required_actions=[
            "Assess compliance with relevant standards (OWASP ASVS, etc.)",
            "Prioritize findings by severity and exploitability",
            "Document remediation recommendations for each finding",
            "Prepare final security assessment summary",
        ],
        next_steps=(
            "This is the final step. When you have completed your compliance review, "
            f"call {tool_name} with next_step_required: false to complete the audit."
        ),
        focus_areas=[
            "Compliance status",
            "Finding prioritization",
            "Remediation planning",
            "Final assessment",
        ],
    )


def _get_default_guidance(
    step_number: int, confidence: ConfidenceLevel, tool_name: str
) -> SecurityAuditGuidance:
    """Default guidance for unknown steps."""
    return SecurityAuditGuidance(
        step_number=step_number,
        domain=SecurityStepDomain.RECONNAISSANCE,
        required_actions=["Continue security investigation"],
        next_steps=get_mandatory_pause_instruction(tool_name, step_number),
    )


_STEP_GUIDANCE_MAP = {
    1: _get_step_1_guidance,
    2: _get_step_2_guidance,
    3: _get_step_3_guidance,
    4: _get_step_4_guidance,
    5: _get_step_5_guidance,
    6: _get_step_6_guidance,
}
