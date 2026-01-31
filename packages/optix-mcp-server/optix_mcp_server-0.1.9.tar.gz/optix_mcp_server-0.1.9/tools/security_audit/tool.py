"""SecurityAuditTool - Multi-step security analysis workflow tool."""

from typing import Any

from tools.security_audit.finding import SecurityFinding
from tools.security_audit.guidance import TOTAL_STEPS, get_step_guidance
from tools.workflow.base import WorkflowTool
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings
from tools.workflow.guidance import StepGuidance
from tools.workflow.request import WorkflowRequest
from tools.workflow.response import WorkflowResponse
from tools.workflow.state import WorkflowState

SECURITY_AUDIT_STEPS = {
    1: "Reconnaissance",
    2: "Auth/AuthZ",
    3: "Input Validation",
    4: "OWASP Top 10",
    5: "Dependencies",
    6: "Compliance",
}


class SecurityAuditTool(WorkflowTool):
    """Security audit workflow tool with 6-step guided analysis.

    Guides users through systematic security analysis covering:
    1. Reconnaissance - app type, tech stack, entry points
    2. Auth/AuthZ - authentication, session, authorization
    3. Input Validation - sanitization, injection, crypto
    4. OWASP Top 10 - systematic vulnerability check
    5. Dependencies - third-party, config, secrets
    6. Compliance - standards, remediation, final assessment
    """

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "security_audit"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return (
            "Perform a guided multi-step security audit of a codebase. "
            "Returns step-specific guidance and accumulates findings across steps."
        )

    @property
    def total_steps(self) -> int:
        """Total number of steps in the audit workflow."""
        return TOTAL_STEPS

    def prepare_expert_analysis_context(
        self, consolidated: ConsolidatedFindings
    ) -> dict[str, Any]:
        """Prepare context for expert LLM analysis.

        Args:
            consolidated: Accumulated findings from all steps

        Returns:
            Context dictionary for LLM analysis
        """
        summary = consolidated.get_audit_summary()
        by_severity = consolidated.get_findings_by_severity()

        return {
            "task": "validate_and_remediate",
            "summary": summary,
            "critical_findings": by_severity["critical"],
            "high_findings": by_severity["high"],
            "files_examined": list(consolidated.files_checked),
            "confidence": consolidated.confidence.value,
        }

    def get_required_actions(
        self, step_number: int, confidence: ConfidenceLevel
    ) -> list[str]:
        """Get security-specific required actions for the step.

        Args:
            step_number: Current step number (1-6)
            confidence: Client's current confidence level

        Returns:
            List of required action strings
        """
        guidance = get_step_guidance(step_number, confidence, self.name)
        return guidance.required_actions

    def execute(self, **kwargs: Any) -> WorkflowResponse:
        """Execute with security-audit-specific parameter handling.

        Maps security_audit parameters to workflow request format.

        Args:
            **kwargs: Security audit request parameters including project_root_path

        Returns:
            WorkflowResponse with audit results
        """
        step_number = kwargs.get("step_number", 1)
        project_root_path = kwargs.get("project_root_path")

        mapped_kwargs = {
            "step": SECURITY_AUDIT_STEPS.get(step_number, f"Step {step_number}"),
            "step_number": step_number,
            "total_steps": TOTAL_STEPS,
            "next_step_required": kwargs.get("next_step_required", True),
            "findings": kwargs.get("findings", ""),
            "confidence": kwargs.get("confidence", "exploring"),
            "files_checked": kwargs.get("files_examined", []),
            "continuation_id": kwargs.get("continuation_id"),
            "vulnerabilities_found": kwargs.get("vulnerabilities_found", []),
            "security_assessments": kwargs.get("security_assessments", {}),
        }

        response = super().execute(**mapped_kwargs)

        if step_number == 1 and project_root_path:
            state = self._state_manager.get(response.continuation_id)
            if state:
                state.project_root_path = project_root_path
                self._state_manager.save(state)

        return response

    def _generate_guidance(
        self, request: WorkflowRequest, state: WorkflowState
    ) -> StepGuidance:
        """Generate security-specific guidance for the next step.

        Args:
            request: Current step request
            state: Current workflow state

        Returns:
            StepGuidance with security-specific actions
        """
        sec_guidance = get_step_guidance(
            request.step_number, request.confidence, self.name
        )

        return StepGuidance(
            required_actions=sec_guidance.required_actions,
            suggestions=sec_guidance.focus_areas,
            next_step_focus=sec_guidance.domain.display_name,
            confidence_guidance=sec_guidance.next_steps,
        )

    def process_step(self, request: WorkflowRequest) -> WorkflowResponse:
        """Process a security audit step.

        Handles security-specific processing including:
        - Parsing vulnerabilities_found from request
        - Storing security_assessments
        - Adding issues to consolidated findings

        Args:
            request: The workflow step request

        Returns:
            WorkflowResponse with security audit results
        """
        response = super().process_step(request)

        state = self._state_manager.get(response.continuation_id)
        if state and state.consolidated and not response.workflow_complete:
            self._process_security_findings(request, state.consolidated)
            self._state_manager.save(state)

        return response

    def _handle_completion(
        self, state: WorkflowState, request: WorkflowRequest
    ) -> WorkflowResponse:
        """Handle workflow completion.

        Args:
            state: Current workflow state
            request: The final step request

        Returns:
            WorkflowResponse with audit summary
        """
        logger = self._get_logger()

        if state.consolidated is not None:
            self._process_security_findings(request, state.consolidated)
            self._state_manager.save(state)
            findings_count = len(state.consolidated.issues_found)
            logger.info(f"Final step findings processed: {findings_count} total findings")

        response = super()._handle_completion(state, request)

        summary = self._format_completion_summary(state)
        response.message = f"{summary}\n\n"

        return response

    def _process_security_findings(
        self, request: WorkflowRequest, consolidated: ConsolidatedFindings
    ) -> None:
        """Process security-specific findings from the request.

        Args:
            request: The workflow request with potential findings
            consolidated: Consolidated findings to update
        """
        logger = self._get_logger()
        raw_data = getattr(request, "_raw_data", {})
        vulnerabilities = raw_data.get("vulnerabilities_found", [])

        for vuln_data in vulnerabilities:
            finding = SecurityFinding.from_dict(vuln_data)
            logger.debug(f"Found {finding.severity.value} vulnerability: {finding.category}")
            consolidated.add_issue(finding.to_dict())

        assessments = raw_data.get("security_assessments", {})
        if assessments:
            for domain, assessment in assessments.items():
                consolidated.add_context([f"{domain}: {assessment}"])
