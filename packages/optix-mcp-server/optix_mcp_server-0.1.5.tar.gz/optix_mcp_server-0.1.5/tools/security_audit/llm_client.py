"""LLM client for expert security analysis at workflow completion."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from config.llm import LLMProviderConfig

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM provider clients."""

    def __init__(self, config: LLMProviderConfig):
        self._config = config

    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Send context for expert analysis.

        Args:
            context: Dictionary containing findings, files, and analysis request

        Returns:
            Dictionary with analysis results including validation and remediation
        """
        ...

    def _build_system_prompt(self) -> str:
        """Build the system prompt for security analysis."""
        return """You are a senior security engineer performing expert analysis on
security audit findings. Your task is to:
1. Validate the severity assessments of the findings
2. Provide detailed remediation recommendations
3. Identify any additional security concerns based on the context
4. Prioritize findings by exploitability and impact

Respond with structured JSON containing:
- validated_findings: List of findings with confirmed/adjusted severity
- additional_concerns: Any additional security issues identified
- remediation_plan: Prioritized list of remediation steps
- overall_assessment: Summary assessment of the security posture"""

    def _build_user_prompt(self, context: dict[str, Any]) -> str:
        """Build the user prompt with audit context."""
        summary = context.get("summary", {})
        critical = context.get("critical_findings", [])
        high = context.get("high_findings", [])
        files = context.get("files_examined", [])

        if isinstance(summary, dict):
            total = summary.get("total_vulnerabilities") or summary.get("total_findings", 0)
        else:
            total = len(critical) + len(high)

        prompt_parts = [
            "Please analyze the following security audit findings:",
            "",
            f"Total findings: {total}",
            f"Files examined: {len(files)}",
            "",
            "Critical findings:",
        ]

        for finding in critical:
            if isinstance(finding, dict):
                prompt_parts.append(f"- {finding.get('category', 'unknown')}: {finding.get('description', '')}")
            else:
                prompt_parts.append(f"- {finding}")

        prompt_parts.append("")
        prompt_parts.append("High severity findings:")
        for finding in high:
            if isinstance(finding, dict):
                prompt_parts.append(f"- {finding.get('category', 'unknown')}: {finding.get('description', '')}")
            else:
                prompt_parts.append(f"- {finding}")

        prompt_parts.extend([
            "",
            "Please validate these findings and provide remediation recommendations.",
        ])

        return "\n".join(prompt_parts)


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return mock analysis results."""
        critical = context.get("critical_findings", [])
        high = context.get("high_findings", [])

        validated = []
        for finding in critical + high:
            validated.append({
                "category": finding.get("category"),
                "original_severity": finding.get("severity"),
                "validated_severity": finding.get("severity"),
                "confirmed": True,
            })

        return {
            "validated_findings": validated,
            "additional_concerns": [],
            "remediation_plan": [
                "1. Address critical findings immediately",
                "2. Plan high-severity remediation within sprint",
            ],
            "overall_assessment": "Security audit identified significant issues requiring attention.",
        }


class OpenAILLMClient(LLMClient):
    """OpenAI-based LLM client."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Call OpenAI API for expert analysis.

        Note: Actual implementation would use openai library.
        This is a placeholder that returns the expected structure.
        """
        try:
            import openai

            client = openai.OpenAI(api_key=self._config.api_key)
            response = client.chat.completions.create(
                model=self._config.default_model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": self._build_user_prompt(context)},
                ],
                max_tokens=self._config.max_tokens,
                response_format={"type": "json_object"},
            )
            import json
            return json.loads(response.choices[0].message.content)
        except ImportError:
            logger.warning(
                "openai library not installed. Expert analysis unavailable. "
                "Install with: pip install optix-mcp-server[openai]"
            )
            return self._fallback_response(context)
        except Exception as e:
            logger.warning(f"OpenAI analysis failed: {e}")
            return {
                "error": str(e),
                "validated_findings": [],
                "additional_concerns": [],
                "remediation_plan": [],
                "overall_assessment": f"Analysis failed: {e}",
            }

    def _fallback_response(self, context: dict[str, Any]) -> dict[str, Any]:
        """Provide fallback response when OpenAI is unavailable."""
        return {
            "validated_findings": context.get("critical_findings", []) + context.get("high_findings", []),
            "additional_concerns": [],
            "remediation_plan": ["Review and address findings based on severity"],
            "overall_assessment": "Manual review recommended - LLM analysis unavailable",
        }


def create_llm_client(config: Optional[LLMProviderConfig]) -> Optional[LLMClient]:
    """Factory function to create appropriate LLM client.

    Args:
        config: LLM provider configuration

    Returns:
        LLMClient instance or None if config is None
    """
    if config is None:
        return None

    provider = config.provider.lower()
    clients = {
        "openai": OpenAILLMClient,
    }

    client_class = clients.get(provider)
    if client_class is None:
        return None

    return client_class(config)
