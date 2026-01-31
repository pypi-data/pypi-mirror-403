"""DevOps-specific step guidance generation."""

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.devops_audit.domains import DevOpsStepDomain
from tools.workflow.confidence import ConfidenceLevel

TOTAL_STEPS = 4


@dataclass
class MissingContextRequest:
    """Request for missing context files."""

    file_type: str
    suggested_paths: list[str]
    reason: str
    priority: str = "MEDIUM"

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_type": self.file_type,
            "suggested_paths": self.suggested_paths,
            "reason": self.reason,
            "priority": self.priority,
        }


@dataclass
class DevOpsStepGuidance:
    """Domain-specific guidance for a DevOps audit step."""

    domain: DevOpsStepDomain
    required_actions: list[str]
    focus_areas: list[str] = field(default_factory=list)
    next_steps: str = ""
    missing_context_hints: list[str] = field(default_factory=list)
    missing_context_requests: list[MissingContextRequest] = field(default_factory=list)


def get_step_guidance(
    step_number: int,
    confidence: ConfidenceLevel,
    tool_name: str,
    missing_context: Optional[list[str]] = None,
) -> DevOpsStepGuidance:
    """Generate domain-specific guidance for the given step.

    Args:
        step_number: Current step number (1-4)
        confidence: Client's current confidence level
        tool_name: Name of the workflow tool
        missing_context: Optional list of missing context files

    Returns:
        DevOpsStepGuidance with required actions and suggestions
    """
    domain = DevOpsStepDomain.for_step(step_number)
    missing_hints = missing_context or []

    if domain == DevOpsStepDomain.DOCKER_AUDIT:
        return _get_docker_guidance(confidence, missing_hints)
    elif domain == DevOpsStepDomain.CICD_AUDIT:
        return _get_cicd_guidance(confidence, missing_hints)
    elif domain == DevOpsStepDomain.DEPENDENCY_AUDIT:
        return _get_dependency_guidance(confidence, missing_hints)
    else:
        return _get_cross_domain_guidance(confidence, missing_hints)


def _get_docker_guidance(
    confidence: ConfidenceLevel, missing_hints: list[str]
) -> DevOpsStepGuidance:
    """Generate Docker Infrastructure Audit guidance."""
    base_actions = [
        "Check for USER directive (running as root)",
        "Check for secrets in layers (COPY/ADD of .env, credentials)",
        "Check base image source (official vs unverified)",
        "Check for HEALTHCHECK directive",
        "Check for mutable tags (:latest)",
        "Check COPY vs ADD usage",
        "Check for multi-stage build opportunities",
    ]

    focus_areas = []
    if confidence <= ConfidenceLevel.MEDIUM:
        focus_areas = [
            "Focus on P0 rules: USER directive, secrets in layers, HEALTHCHECK",
            "Examine base image pinning and version tags",
        ]

    return DevOpsStepGuidance(
        domain=DevOpsStepDomain.DOCKER_AUDIT,
        required_actions=base_actions,
        focus_areas=focus_areas,
        next_steps="Proceed to CI/CD Pipeline Audit after analyzing Dockerfiles",
        missing_context_hints=missing_hints,
    )


def _get_cicd_guidance(
    confidence: ConfidenceLevel, missing_hints: list[str]
) -> DevOpsStepGuidance:
    """Generate CI/CD Pipeline Audit guidance."""
    base_actions = [
        "Check for hardcoded secrets in workflows",
        "Check for unpinned third-party actions (@main, @master)",
        "Check for unverified action publishers",
        "Check for missing or overly permissive permissions block",
        "Check for secrets at workflow level vs step level",
        "Check for missing environment protection",
        "Check for static credentials vs OIDC",
    ]

    focus_areas = []
    if confidence <= ConfidenceLevel.MEDIUM:
        focus_areas = [
            "Focus on P0 rules: hardcoded secrets, unpinned actions, permissions block",
            "Verify all third-party actions are from trusted sources",
        ]

    return DevOpsStepGuidance(
        domain=DevOpsStepDomain.CICD_AUDIT,
        required_actions=base_actions,
        focus_areas=focus_areas,
        next_steps="Proceed to Dependency Security Audit after analyzing workflows",
        missing_context_hints=missing_hints,
    )


def _get_dependency_guidance(
    confidence: ConfidenceLevel, missing_hints: list[str]
) -> DevOpsStepGuidance:
    """Generate Dependency Security Audit guidance."""
    base_actions = [
        "Check for missing lockfile",
        "Check for wildcard version ranges (*)",
        "Check for unbounded version ranges (>=4.0.0)",
        "Check for major versions behind (2+)",
        "Check for excessive transitive dependencies (>50)",
        "Check for package.json / lockfile divergence",
    ]

    focus_areas = []
    if confidence <= ConfidenceLevel.MEDIUM:
        focus_areas = [
            "Focus on P0 rules: missing lockfile, wildcard versions, unbounded ranges",
            "Request lockfile if missing for comprehensive analysis",
        ]

    lockfile_hints = [
        h for h in missing_hints if "lock" in h.lower() or "package-lock" in h.lower()
    ]
    all_hints = (
        lockfile_hints
        if lockfile_hints
        else ["If lockfile is missing, request it for complete analysis"]
    )

    missing_context_requests = []
    if any("lock" in h.lower() for h in missing_hints):
        missing_context_requests.append(
            MissingContextRequest(
                file_type="lockfile",
                suggested_paths=[
                    "package-lock.json",
                    "yarn.lock",
                    "pnpm-lock.yaml",
                ],
                reason="Lockfile required for transitive dependency analysis and version pinning verification",
                priority="HIGH",
            )
        )

    return DevOpsStepGuidance(
        domain=DevOpsStepDomain.DEPENDENCY_AUDIT,
        required_actions=base_actions,
        focus_areas=focus_areas,
        next_steps="Ready for Cross-Domain Analysis - set next_step_required=false",
        missing_context_hints=all_hints,
        missing_context_requests=missing_context_requests,
    )


def _get_cross_domain_guidance(
    confidence: ConfidenceLevel, missing_hints: list[str]
) -> DevOpsStepGuidance:
    """Generate Cross-Domain Analysis guidance."""
    base_actions = [
        "Aggregate findings from all previous steps",
        "Detect cross-domain compound risks",
        "Identify findings requiring multi-LLM validation",
        "Generate final DevOps audit report",
    ]

    focus_areas = [
        "Compound risk: unpinned versions across Dockerfile, CI/CD, and dependencies",
        "Integration gaps: Docker HEALTHCHECK not tested in CI/CD",
        "Supply chain risks spanning multiple domains",
    ]

    return DevOpsStepGuidance(
        domain=DevOpsStepDomain.CROSS_DOMAIN_ANALYSIS,
        required_actions=base_actions,
        focus_areas=focus_areas,
        next_steps="Workflow complete - audit results ready",
        missing_context_hints=missing_hints,
    )
