"""
Multi-LLM Consensus Analyzer

Coordinates multiple LLM providers to validate findings through weighted consensus.
Extracted from DevOps validation for generic use across all audit types.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from config.llm import LLMProviderConfig


VALIDATION_THRESHOLD = 0.70
DISAGREEMENT_MARGIN = 0.20
CONFIDENCE_REDUCTION_ON_DISAGREEMENT = 0.15


@dataclass
class LLMAssessment:
    """Single LLM's assessment of a finding."""

    provider: str
    model: str
    severity: str
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "severity": self.severity,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConsensusResult:
    """Result from multi-LLM consensus validation."""

    original_severity: str
    final_severity: str
    confidence: float
    consensus_reached: bool
    consensus_method: str
    llm_assessments: list[LLMAssessment] = field(default_factory=list)
    providers_used: list[str] = field(default_factory=list)
    providers_failed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_severity": self.original_severity,
            "validated_severity": self.final_severity,
            "confidence": self.confidence,
            "consensus_reached": self.consensus_reached,
            "consensus_method": self.consensus_method,
            "llm_assessments": [a.to_dict() for a in self.llm_assessments],
            "providers_used": self.providers_used,
            "providers_failed": self.providers_failed,
        }


def determine_llm_count(severity: str, confidence: float) -> int:
    """
    Determine number of LLMs needed based on severity and confidence.

    Args:
        severity: Finding severity (critical, high, medium, low)
        confidence: Numeric confidence (0.0-1.0)

    Returns:
        Number of LLMs to use (1-3)
    """
    if severity.lower() == "critical":
        return 3

    if confidence >= 0.85:
        return 1
    elif confidence >= 0.60:
        return 2
    else:
        return 3


def select_llm_models(count: int) -> list[tuple[str, str]]:
    """Select LLM providers to use for consensus."""
    models = [
        ("openai", "gpt-4o"),
        ("openai", "gpt-4o-mini"),
        ("openai", "gpt-4-turbo"),
    ]
    return models[:count]


def calculate_weighted_consensus(
    assessments: list[LLMAssessment]
) -> tuple[str, float, bool, str]:
    """
    Calculate weighted consensus from multiple LLM assessments.

    Args:
        assessments: List of LLM assessments

    Returns:
        Tuple of (winning_severity, avg_confidence, consensus_reached, method)
    """
    if not assessments:
        return "medium", 0.5, False, "no_assessments"

    if len(assessments) == 1:
        return assessments[0].severity, assessments[0].confidence, True, "single_llm"

    # Weight votes by confidence
    severity_votes: dict[str, float] = {}
    for assessment in assessments:
        if assessment.severity not in severity_votes:
            severity_votes[assessment.severity] = 0.0
        severity_votes[assessment.severity] += assessment.confidence

    total_confidence = sum(a.confidence for a in assessments)
    if total_confidence == 0:
        total_confidence = 1.0

    # Find winning severity
    winning_severity = max(severity_votes.items(), key=lambda x: x[1])[0]
    winning_weight = severity_votes[winning_severity]

    # Calculate average confidence of agreeing assessments
    agreeing_assessments = [a for a in assessments if a.severity == winning_severity]
    avg_confidence = sum(a.confidence for a in agreeing_assessments) / len(assessments)

    # Check for disagreement
    losing_weight = total_confidence - winning_weight
    margin = (winning_weight - losing_weight) / total_confidence
    disagreement = margin < DISAGREEMENT_MARGIN

    consensus_method = f"{len(assessments)}_llm_weighted"

    return winning_severity, avg_confidence, not disagreement, consensus_method


def apply_conservative_bias(
    severity: str, confidence: float, assessments: list[LLMAssessment]
) -> tuple[str, float]:
    """
    Apply conservative bias when disagreement exists.

    Args:
        severity: Current winning severity
        confidence: Current confidence
        assessments: All assessments

    Returns:
        Tuple of (adjusted_severity, adjusted_confidence)
    """
    reduced_confidence = max(0.5, confidence - CONFIDENCE_REDUCTION_ON_DISAGREEMENT)

    severity_order = ["critical", "high", "medium", "low", "info"]
    highest_severity = severity

    # Use most severe assessment when disagreement exists
    for assessment in assessments:
        if severity_order.index(assessment.severity.lower()) < severity_order.index(
            highest_severity.lower()
        ):
            highest_severity = assessment.severity

    return highest_severity, reduced_confidence


class ConsensusAnalyzer:
    """
    Orchestrates multi-LLM consensus validation for critical findings.
    """

    def __init__(self, configs: Optional[list[LLMProviderConfig]] = None):
        self._configs: dict[str, LLMProviderConfig] = {}
        if configs:
            for config in configs:
                self._configs[config.provider.lower()] = config

    def add_provider(self, config: LLMProviderConfig) -> None:
        """Add an LLM provider configuration."""
        self._configs[config.provider.lower()] = config

    def has_providers(self) -> bool:
        """Check if any providers are configured."""
        return len(self._configs) > 0

    def available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return list(self._configs.keys())

    async def validate_finding(
        self, finding: dict[str, Any], audit_type: str
    ) -> ConsensusResult:
        """
        Validate a single finding using multi-LLM consensus.

        Args:
            finding: Finding dictionary with severity, description, etc.
            audit_type: Type of audit (security, devops, accessibility)

        Returns:
            ConsensusResult with consensus validation
        """
        severity = finding.get("severity", "medium")
        confidence = finding.get("confidence", 0.6)

        # Determine how many LLMs to use
        llm_count = determine_llm_count(severity, confidence)
        models_to_use = select_llm_models(llm_count)

        assessments: list[LLMAssessment] = []
        providers_used: list[str] = []
        providers_failed: list[str] = []

        # Get assessments from each LLM
        for provider, model in models_to_use:
            if provider not in self._configs:
                providers_failed.append(provider)
                continue

            try:
                assessment = await self._get_llm_assessment(
                    finding, provider, model, audit_type
                )
                if assessment:
                    assessments.append(assessment)
                    providers_used.append(provider)
                else:
                    providers_failed.append(provider)
            except Exception as e:
                self._log(f"Error getting assessment from {provider}: {e}", error=True)
                providers_failed.append(provider)

        # Handle no successful assessments
        if not assessments:
            return ConsensusResult(
                original_severity=severity,
                final_severity=severity,
                confidence=0.5,
                consensus_reached=False,
                consensus_method="fallback_no_providers",
                llm_assessments=[],
                providers_used=[],
                providers_failed=providers_failed,
            )

        # Calculate consensus
        final_severity, final_confidence, consensus, method = (
            calculate_weighted_consensus(assessments)
        )

        # Apply conservative bias if no consensus
        if not consensus:
            final_severity, final_confidence = apply_conservative_bias(
                final_severity, final_confidence, assessments
            )
            method = f"{method}_conservative_bias"

        return ConsensusResult(
            original_severity=severity,
            final_severity=final_severity,
            confidence=final_confidence,
            consensus_reached=consensus,
            consensus_method=method,
            llm_assessments=assessments,
            providers_used=providers_used,
            providers_failed=providers_failed,
        )

    async def validate_findings(
        self, findings: list[dict[str, Any]], audit_type: str
    ) -> list[ConsensusResult]:
        """
        Validate multiple findings using multi-LLM consensus.

        Args:
            findings: List of finding dictionaries
            audit_type: Type of audit

        Returns:
            List of consensus results
        """
        results = []
        for finding in findings:
            result = await self.validate_finding(finding, audit_type)
            results.append(result)
        return results

    async def _get_llm_assessment(
        self, finding: dict[str, Any], provider: str, model: str, audit_type: str
    ) -> Optional[LLMAssessment]:
        """Get assessment from a single LLM provider."""
        config = self._configs.get(provider)
        if not config:
            return None

        client = self._create_client(provider, config)
        if not client:
            return None

        try:
            context = self._build_validation_context(finding, audit_type)
            response = await client.analyze(context)

            validated_severity = response.get(
                "validated_severity", finding.get("severity", "medium")
            )
            confidence = response.get("confidence", 0.7)
            reasoning = response.get("reasoning", "")

            return LLMAssessment(
                provider=provider,
                model=model,
                severity=validated_severity,
                confidence=confidence,
                reasoning=reasoning,
            )
        except Exception as e:
            self._log(f"Error in LLM assessment from {provider}: {e}", error=True)
            return None

    def _create_client(
        self, provider: str, config: LLMProviderConfig
    ) -> Optional[Any]:
        """Create LLM client for the given provider."""
        from tools.security_audit.llm_client import OpenAILLMClient

        clients = {
            "openai": OpenAILLMClient,
        }

        client_class = clients.get(provider)
        if client_class is None:
            return None

        return client_class(config)

    def _build_validation_context(
        self, finding: dict[str, Any], audit_type: str
    ) -> dict[str, Any]:
        """Build context for LLM validation request."""
        return {
            "task": f"validate_{audit_type}_finding",
            "finding": {
                "severity": finding.get("severity", "medium"),
                "category": finding.get("category", "general"),
                "description": finding.get("description", ""),
                "affected_files": finding.get("affected_files", []),
                "remediation": finding.get("remediation", ""),
            },
            "validation_request": (
                f"Please validate this {audit_type} finding. "
                "Assess whether the severity is accurate and provide your confidence level (0.0-1.0). "
                "Return JSON with: validated_severity (critical|high|medium|low|info), confidence (float), reasoning (string)."
            ),
        }

    def _log(self, message: str, error: bool = False) -> None:
        """Log a message."""
        prefix = "ERROR" if error else "INFO"
        print(f"[ConsensusAnalyzer] {prefix}: {message}", file=sys.stderr)
