"""
Expert Analysis Module

Provides generic expert analysis functionality for audit findings using LLM providers.
Extracted from DevOps-specific implementation to work with all audit types.
"""

from tools.expert_analysis.service import (
    ExpertAnalysisService,
    ExpertAnalysisResult,
    ValidatedFinding,
    AdditionalConcern,
    RemediationPriority,
    ExpertAnalysisMetadata,
)
from tools.expert_analysis.consensus import ConsensusAnalyzer
from tools.expert_analysis.prompt_templates import (
    build_analysis_prompt,
    EXPERT_ANALYSIS_PROMPT,
    CONSENSUS_VALIDATION_PROMPT,
)

__all__ = [
    "ExpertAnalysisService",
    "ExpertAnalysisResult",
    "ValidatedFinding",
    "AdditionalConcern",
    "RemediationPriority",
    "ExpertAnalysisMetadata",
    "ConsensusAnalyzer",
    "build_analysis_prompt",
    "EXPERT_ANALYSIS_PROMPT",
    "CONSENSUS_VALIDATION_PROMPT",
]
