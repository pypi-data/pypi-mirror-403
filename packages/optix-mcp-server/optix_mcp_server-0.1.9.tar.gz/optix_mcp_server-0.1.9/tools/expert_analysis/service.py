"""
Expert Analysis Service

Provides LLM-based validation and enhancement of audit findings.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from config.llm import LLMProviderConfig
from tools.expert_analysis.consensus import ConsensusAnalyzer
from tools.expert_analysis.prompt_templates import build_analysis_prompt

logger = logging.getLogger(__name__)


@dataclass
class ExpertAnalysisMetadata:
    """Metadata about the expert analysis execution."""
    provider: str
    model: str
    timestamp: str
    execution_time_seconds: float
    findings_analyzed: int
    multi_llm_enabled: bool = False
    providers_used: Optional[list[str]] = None


@dataclass
class ValidatedFinding:
    """Expert's assessment of a single audit finding."""
    original_id: str
    original_severity: str
    confirmed: bool
    adjusted_severity: Optional[str]
    confidence: float
    reasoning: str


@dataclass
class AdditionalConcern:
    """New issue identified by expert analysis."""
    id: str
    title: str
    description: str
    severity: str
    category: str
    affected_files: list[str]
    remediation: str
    confidence: float


@dataclass
class RemediationPriority:
    """Prioritized action item for addressing findings."""
    priority: int
    action: str
    rationale: str
    estimated_effort: str
    related_findings: list[str]


@dataclass
class ExpertAnalysisResult:
    """Complete result from expert analysis."""
    validated_findings: list[dict[str, Any]]
    additional_concerns: list[dict[str, Any]]
    remediation_priorities: list[dict[str, Any]]
    overall_assessment: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON transport."""
        return {
            "validated_findings": self.validated_findings,
            "additional_concerns": self.additional_concerns,
            "remediation_priorities": self.remediation_priorities,
            "overall_assessment": self.overall_assessment,
            "metadata": self.metadata,
        }


class ExpertAnalysisService:
    """
    Service for LLM-based expert analysis of audit findings.

    Orchestrates single or multi-LLM validation and enhancement of findings.
    """

    def __init__(self, config: LLMProviderConfig, enable_multi_llm: bool = False):
        """
        Initialize expert analysis service.

        Args:
            config: LLM provider configuration
            enable_multi_llm: Whether to use multi-LLM consensus for critical findings
        """
        self.config = config
        self.enable_multi_llm = enable_multi_llm
        self.client = None
        self.consensus_analyzer = None

        # Lazy initialization of clients
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize LLM client based on configuration."""
        from tools.security_audit.llm_client import create_llm_client

        try:
            self.client = create_llm_client(self.config)
            if self.enable_multi_llm:
                self.consensus_analyzer = ConsensusAnalyzer([self.config])
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise

    async def analyze_findings(
        self, consolidated: Any, audit_type: str
    ) -> Optional[ExpertAnalysisResult]:
        """
        Analyze consolidated findings using LLM expert analysis.

        Args:
            consolidated: ConsolidatedFindings object with accumulated findings
            audit_type: Type of audit (security, devops, accessibility)

        Returns:
            ExpertAnalysisResult on success, None on failure (graceful degradation)
        """
        logger.debug(f"Starting expert analysis for {audit_type} audit")

        try:
            # Check if there are findings to analyze
            if not hasattr(consolidated, "issues_found") or not consolidated.issues_found:
                logger.info("No findings to analyze - skipping expert analysis")
                return None

            findings = consolidated.issues_found
            logger.debug(f"Analyzing {len(findings)} findings for {audit_type} audit")

            # Limit findings to configured maximum
            max_findings = 50  # Default, should come from config
            if len(findings) > max_findings:
                logger.warning(
                    f"Limiting analysis to {max_findings} findings (total: {len(findings)})"
                )
                findings = findings[:max_findings]

            # Check if critical findings exist for multi-LLM consensus
            has_critical = self._has_critical_findings(findings)
            logger.debug(f"Critical findings detected: {has_critical}")

            start_time = datetime.now()

            # Execute analysis
            if has_critical and self.enable_multi_llm and self.consensus_analyzer:
                logger.info("Using multi-LLM consensus for critical findings")
                response = await self._execute_multi_llm_consensus(
                    findings, audit_type, consolidated
                )
            else:
                logger.info("Using single LLM analysis")
                response = await self._execute_single_llm_analysis(
                    findings, audit_type, consolidated
                )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Expert analysis completed in {execution_time:.2f}s")

            # Parse and return result
            result = self._parse_llm_response(
                response, audit_type, execution_time, len(findings)
            )
            logger.debug(f"Expert analysis result: {len(result.validated_findings)} validated, "
                        f"{len(result.additional_concerns)} additional concerns")
            return result

        except asyncio.TimeoutError:
            logger.error("Expert analysis timed out")
            return None
        except Exception as e:
            logger.error(f"Expert analysis failed: {e}", exc_info=True)
            return None

    def _build_analysis_prompt(
        self, findings: list[dict], audit_type: str, consolidated: Any
    ) -> str:
        """
        Build LLM prompt from findings.

        Args:
            findings: List of findings to analyze
            audit_type: Type of audit
            consolidated: ConsolidatedFindings object

        Returns:
            Formatted prompt string
        """
        return build_analysis_prompt(findings, audit_type, consolidated)

    async def _execute_single_llm_analysis(
        self, findings: list[dict], audit_type: str, consolidated: Any
    ) -> dict[str, Any]:
        """
        Execute analysis with single configured LLM.

        Args:
            findings: Findings to analyze
            audit_type: Type of audit
            consolidated: ConsolidatedFindings object

        Returns:
            Parsed LLM response as dict
        """
        if not self.client:
            raise RuntimeError("LLM client not initialized")

        # Build prompt
        prompt = self._build_analysis_prompt(findings, audit_type, consolidated)

        # Build context for LLM
        context = {
            "task": "validate_and_enhance",
            "audit_type": audit_type,
            "prompt": prompt,
            "findings": findings,
            "files_examined": list(
                consolidated.files_checked if hasattr(consolidated, "files_checked") else []
            ),
            "confidence": str(
                consolidated.confidence if hasattr(consolidated, "confidence") else "medium"
            ),
        }

        # Call LLM
        response = await self.client.analyze(context)
        return response

    async def _execute_multi_llm_consensus(
        self, findings: list[dict], audit_type: str, consolidated: Any
    ) -> dict[str, Any]:
        """
        Execute multi-LLM consensus for high-severity findings.

        Args:
            findings: Findings to validate
            audit_type: Type of audit
            consolidated: ConsolidatedFindings object

        Returns:
            Consensus result with aggregated assessments
        """
        if not self.consensus_analyzer:
            # Fallback to single LLM
            return await self._execute_single_llm_analysis(findings, audit_type, consolidated)

        # Validate critical findings with consensus
        consensus_results = await self.consensus_analyzer.validate_findings(
            findings, audit_type
        )

        # Build response from consensus results
        validated_findings = []
        for result in consensus_results:
            validated_findings.append({
                "original_severity": result.original_severity,
                "validated_severity": result.final_severity,
                "confidence": result.confidence,
                "consensus_reached": result.consensus_reached,
                "reasoning": result.llm_assessments[0].reasoning if result.llm_assessments else "",
            })

        # Execute single LLM for additional concerns and priorities
        single_response = await self._execute_single_llm_analysis(
            findings, audit_type, consolidated
        )

        # Merge consensus validation with single LLM response
        single_response["validated_findings"] = validated_findings
        return single_response

    def _parse_llm_response(
        self,
        response: dict[str, Any],
        audit_type: str,
        execution_time: float,
        findings_count: int,
    ) -> ExpertAnalysisResult:
        """
        Parse LLM response into structured result.

        Args:
            response: Raw LLM API response
            audit_type: Context for validation
            execution_time: Seconds taken for analysis
            findings_count: Number of findings analyzed

        Returns:
            Structured ExpertAnalysisResult
        """
        # Extract components with defaults
        validated_findings = response.get("validated_findings", [])
        additional_concerns = response.get("additional_concerns", [])
        remediation_priorities = response.get("remediation_priorities", [])
        overall_assessment = response.get(
            "overall_assessment", "Expert analysis completed."
        )

        # Build metadata
        metadata = {
            "provider": self.config.provider,
            "model": self.client.model_name if hasattr(self.client, "model_name") else "unknown",
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": execution_time,
            "findings_analyzed": findings_count,
            "multi_llm_enabled": self.enable_multi_llm,
        }

        return ExpertAnalysisResult(
            validated_findings=validated_findings,
            additional_concerns=additional_concerns,
            remediation_priorities=remediation_priorities,
            overall_assessment=overall_assessment,
            metadata=metadata,
        )

    def _has_critical_findings(self, findings: list[dict]) -> bool:
        """
        Check if any findings are critical severity.

        Args:
            findings: List of findings

        Returns:
            True if critical findings exist
        """
        for finding in findings:
            severity = finding.get("severity", "").lower()
            if severity == "critical":
                return True
        return False
