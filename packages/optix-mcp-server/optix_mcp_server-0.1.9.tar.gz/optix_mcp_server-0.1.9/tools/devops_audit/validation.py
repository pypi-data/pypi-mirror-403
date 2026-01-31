"""Multi-LLM validation for DevOps audit findings."""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from config.llm import LLMProviderConfig
from tools.devops_audit.finding import DevOpsFinding
from tools.devops_audit.severity import Severity
from tools.workflow.confidence import ConfidenceLevel


VALIDATION_THRESHOLD = 0.70
DISAGREEMENT_MARGIN = 0.20
CONFIDENCE_REDUCTION_ON_DISAGREEMENT = 0.15
MAX_LLM_CALLS_PER_FINDING = 5


CONFIDENCE_NUMERIC_MAP = {
    ConfidenceLevel.EXPLORING: 0.20,
    ConfidenceLevel.LOW: 0.40,
    ConfidenceLevel.MEDIUM: 0.60,
    ConfidenceLevel.HIGH: 0.75,
    ConfidenceLevel.VERY_HIGH: 0.85,
    ConfidenceLevel.ALMOST_CERTAIN: 0.95,
    ConfidenceLevel.CERTAIN: 1.00,
}


def confidence_to_numeric(confidence: ConfidenceLevel) -> float:
    return CONFIDENCE_NUMERIC_MAP.get(confidence, 0.50)


def numeric_to_confidence(value: float) -> ConfidenceLevel:
    if value >= 1.00:
        return ConfidenceLevel.CERTAIN
    elif value >= 0.95:
        return ConfidenceLevel.ALMOST_CERTAIN
    elif value >= 0.85:
        return ConfidenceLevel.VERY_HIGH
    elif value >= 0.75:
        return ConfidenceLevel.HIGH
    elif value >= 0.60:
        return ConfidenceLevel.MEDIUM
    elif value >= 0.40:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.EXPLORING


@dataclass
class LLMAssessment:
    """Single LLM's assessment of a finding."""

    provider: str
    model: str
    severity: Severity
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMAssessment":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            provider=data["provider"],
            model=data["model"],
            severity=Severity.from_string(data["severity"]) if isinstance(data["severity"], str) else data["severity"],
            confidence=data.get("confidence", 0.5),
            reasoning=data.get("reasoning", ""),
            timestamp=timestamp,
        )


@dataclass
class MultiLLMValidationResult:
    """Result from multi-LLM consensus validation."""

    original_finding: DevOpsFinding
    final_severity: Severity
    confidence_level: ConfidenceLevel
    consensus_reached: bool
    llm_assessments: list[LLMAssessment] = field(default_factory=list)
    validation_timestamp: datetime = field(default_factory=datetime.now)
    providers_used: list[str] = field(default_factory=list)
    providers_failed: list[str] = field(default_factory=list)
    consensus_method: str = "single_llm"

    def to_finding(self) -> DevOpsFinding:
        return DevOpsFinding(
            severity=self.final_severity,
            category=self.original_finding.category,
            description=self.original_finding.description,
            affected_files=self.original_finding.affected_files,
            remediation=self.original_finding.remediation,
            line_numbers=self.original_finding.line_numbers,
            confidence=self.confidence_level,
            llm_assessments=[a.to_dict() for a in self.llm_assessments],
            validation_timestamp=self.validation_timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_severity": self.original_finding.severity.value,
            "validated_severity": self.final_severity.value,
            "confidence": confidence_to_numeric(self.confidence_level),
            "confidence_level": self.confidence_level.value,
            "consensus_reached": self.consensus_reached,
            "consensus_method": self.consensus_method,
            "llm_assessments": [a.to_dict() for a in self.llm_assessments],
            "providers_used": self.providers_used,
            "providers_failed": self.providers_failed,
            "validation_timestamp": self.validation_timestamp.isoformat(),
        }


def requires_validation(finding: DevOpsFinding) -> bool:
    confidence = finding.confidence or ConfidenceLevel.MEDIUM
    numeric_conf = confidence_to_numeric(confidence)

    if finding.severity == Severity.CRITICAL:
        return True

    return numeric_conf < VALIDATION_THRESHOLD


def determine_llm_count(finding: DevOpsFinding) -> int:
    if finding.severity == Severity.CRITICAL:
        return 3

    confidence = finding.confidence or ConfidenceLevel.MEDIUM
    numeric_conf = confidence_to_numeric(confidence)

    if numeric_conf >= 0.85:
        return 1
    elif numeric_conf >= 0.60:
        return 2
    else:
        return 3


def select_llm_models(count: int) -> list[tuple[str, str]]:
    models = [
        ("openai", "gpt-4o"),
        ("openai", "gpt-4o-mini"),
        ("openai", "gpt-4-turbo"),
    ]
    return models[:count]


def calculate_weighted_consensus(assessments: list[LLMAssessment]) -> tuple[Severity, float, bool, str]:
    if not assessments:
        return Severity.MEDIUM, 0.5, False, "no_assessments"

    if len(assessments) == 1:
        return assessments[0].severity, assessments[0].confidence, True, "single_llm"

    severity_votes: dict[Severity, float] = {}
    for assessment in assessments:
        if assessment.severity not in severity_votes:
            severity_votes[assessment.severity] = 0.0
        severity_votes[assessment.severity] += assessment.confidence

    total_confidence = sum(a.confidence for a in assessments)
    if total_confidence == 0:
        total_confidence = 1.0

    winning_severity = max(severity_votes.items(), key=lambda x: x[1])[0]
    winning_weight = severity_votes[winning_severity]

    agreeing_assessments = [a for a in assessments if a.severity == winning_severity]
    avg_confidence = sum(a.confidence for a in agreeing_assessments) / len(assessments)

    losing_weight = total_confidence - winning_weight
    margin = (winning_weight - losing_weight) / total_confidence
    disagreement = margin < DISAGREEMENT_MARGIN

    consensus_method = f"{len(assessments)}_llm_weighted"

    return winning_severity, avg_confidence, not disagreement, consensus_method


def apply_conservative_bias(
    severity: Severity, confidence: float, assessments: list[LLMAssessment]
) -> tuple[Severity, float]:
    reduced_confidence = max(0.5, confidence - CONFIDENCE_REDUCTION_ON_DISAGREEMENT)

    severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
    highest_severity = severity
    for assessment in assessments:
        if severity_order.index(assessment.severity) < severity_order.index(highest_severity):
            highest_severity = assessment.severity

    return highest_severity, reduced_confidence


class MultiLLMValidator:
    """Validator that uses multiple LLM providers to validate findings."""

    def __init__(self, configs: Optional[list[LLMProviderConfig]] = None):
        self._configs: dict[str, LLMProviderConfig] = {}
        if configs:
            for config in configs:
                self._configs[config.provider.lower()] = config

    def add_provider(self, config: LLMProviderConfig) -> None:
        self._configs[config.provider.lower()] = config

    def has_providers(self) -> bool:
        return len(self._configs) > 0

    def available_providers(self) -> list[str]:
        return list(self._configs.keys())

    async def validate_finding(self, finding: DevOpsFinding) -> MultiLLMValidationResult:
        if not requires_validation(finding):
            return MultiLLMValidationResult(
                original_finding=finding,
                final_severity=finding.severity,
                confidence_level=finding.confidence or ConfidenceLevel.HIGH,
                consensus_reached=True,
                consensus_method="no_validation_needed",
                providers_used=[],
                providers_failed=[],
            )

        llm_count = determine_llm_count(finding)
        models_to_use = select_llm_models(llm_count)

        assessments: list[LLMAssessment] = []
        providers_used: list[str] = []
        providers_failed: list[str] = []

        for provider, model in models_to_use:
            if provider not in self._configs:
                providers_failed.append(provider)
                continue

            try:
                assessment = await self._get_llm_assessment(finding, provider, model)
                if assessment:
                    assessments.append(assessment)
                    providers_used.append(provider)
                else:
                    providers_failed.append(provider)
            except Exception as e:
                self._log(f"Error getting assessment from {provider}: {e}", error=True)
                providers_failed.append(provider)

        if not assessments:
            return MultiLLMValidationResult(
                original_finding=finding,
                final_severity=finding.severity,
                confidence_level=ConfidenceLevel.LOW,
                consensus_reached=False,
                consensus_method="fallback_no_providers",
                providers_used=[],
                providers_failed=providers_failed,
                llm_assessments=[],
            )

        severity, confidence, consensus, method = calculate_weighted_consensus(assessments)

        if not consensus:
            severity, confidence = apply_conservative_bias(severity, confidence, assessments)
            method = f"{method}_conservative_bias"

        return MultiLLMValidationResult(
            original_finding=finding,
            final_severity=severity,
            confidence_level=numeric_to_confidence(confidence),
            consensus_reached=consensus,
            consensus_method=method,
            llm_assessments=assessments,
            providers_used=providers_used,
            providers_failed=providers_failed,
        )

    async def validate_findings(
        self, findings: list[DevOpsFinding]
    ) -> list[MultiLLMValidationResult]:
        results = []
        for finding in findings:
            result = await self.validate_finding(finding)
            results.append(result)
        return results

    async def _get_llm_assessment(
        self, finding: DevOpsFinding, provider: str, model: str
    ) -> Optional[LLMAssessment]:
        config = self._configs.get(provider)
        if not config:
            return None

        client = self._create_client(provider, config)
        if not client:
            return None

        try:
            context = self._build_validation_context(finding)
            response = await client.analyze(context)

            validated_severity = response.get("validated_severity", finding.severity.value)
            confidence = response.get("confidence", 0.7)
            reasoning = response.get("reasoning", "")

            return LLMAssessment(
                provider=provider,
                model=model,
                severity=Severity.from_string(validated_severity) if isinstance(validated_severity, str) else validated_severity,
                confidence=confidence,
                reasoning=reasoning,
            )
        except Exception as e:
            self._log(f"Error in LLM assessment from {provider}: {e}", error=True)
            return None

    def _create_client(self, provider: str, config: LLMProviderConfig) -> Optional[Any]:
        from tools.security_audit.llm_client import OpenAILLMClient

        clients = {
            "openai": OpenAILLMClient,
        }

        client_class = clients.get(provider)
        if client_class is None:
            return None

        return client_class(config)

    def _build_validation_context(self, finding: DevOpsFinding) -> dict[str, Any]:
        return {
            "task": "validate_devops_finding",
            "finding": {
                "severity": finding.severity.value,
                "category": finding.category.value,
                "description": finding.description,
                "affected_files": finding.affected_files,
                "remediation": finding.remediation,
            },
            "validation_request": (
                "Please validate this DevOps security finding. "
                "Assess whether the severity is accurate and provide your confidence level (0.0-1.0). "
                "Return JSON with: validated_severity (CRITICAL/HIGH/MEDIUM/LOW), confidence (float), reasoning (string)."
            ),
        }

    def _log(self, message: str, error: bool = False) -> None:
        prefix = "ERROR" if error else "INFO"
        print(f"[MultiLLMValidator] {prefix}: {message}", file=sys.stderr)


def get_validation_summary(results: list[MultiLLMValidationResult]) -> dict[str, Any]:
    total = len(results)
    validated = sum(1 for r in results if r.providers_used)
    consensus = sum(1 for r in results if r.consensus_reached)

    llm_calls_by_model: dict[str, int] = {}
    for result in results:
        for assessment in result.llm_assessments:
            key = f"{assessment.provider}:{assessment.model}"
            llm_calls_by_model[key] = llm_calls_by_model.get(key, 0) + 1

    severity_changes = sum(
        1 for r in results
        if r.original_finding.severity != r.final_severity
    )

    return {
        "total_findings": total,
        "validated_with_llm": validated,
        "consensus_reached": consensus,
        "disagreements": total - consensus,
        "severity_changes": severity_changes,
        "llm_calls_total": sum(len(r.llm_assessments) for r in results),
        "llm_calls_by_model": llm_calls_by_model,
    }
