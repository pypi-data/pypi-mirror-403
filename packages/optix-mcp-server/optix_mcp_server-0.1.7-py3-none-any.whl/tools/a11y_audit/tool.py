"""AccessibilityAuditTool - Multi-step accessibility analysis workflow tool."""

from typing import Any
from tools.a11y_audit.finding import AccessibilityFinding
from tools.a11y_audit.guidance import TOTAL_STEPS, get_step_guidance
from tools.workflow.base import WorkflowTool
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings
from tools.workflow.guidance import StepGuidance
from tools.workflow.request import WorkflowRequest
from tools.workflow.response import WorkflowResponse
from tools.workflow.state import WorkflowState

A11Y_AUDIT_STEPS = {
    1: "Structural Analysis & Discovery",
    2: "ARIA Labels & Attributes",
    3: "Keyboard Navigation",
    4: "Focus Management",
    5: "Visual Accessibility & Color Contrast",
    6: "Semantic HTML & WCAG Compliance",
}


class AccessibilityAuditTool(WorkflowTool):
    """Accessibility audit workflow tool with 6-step guided analysis.

    Guides users through systematic accessibility analysis covering:
    1. Structural Analysis - framework, component detection
    2. ARIA Labels - aria-label, roles, landmarks
    3. Keyboard Navigation - tab order, keyboard traps, handlers
    4. Focus Management - focus indicators, restoration, dynamic content
    5. Color Contrast - text/background ratios, Tailwind warnings
    6. Semantic HTML - semantic elements, heading hierarchy, WCAG compliance
    """

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "a11y_audit"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return (
            "Perform a guided multi-step UI accessibility audit. "
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
            "task": "validate_accessibility_findings",
            "summary": summary,
            "critical_findings": by_severity["critical"],
            "high_findings": by_severity["high"],
            "files_examined": list(consolidated.files_checked),
            "confidence": consolidated.confidence.value,
        }

    def get_required_actions(
        self, step_number: int, confidence: ConfidenceLevel
    ) -> list[str]:
        """Get accessibility-specific required actions for the step.

        Delegates to get_step_guidance for domain-specific guidance.

        Args:
            step_number: Current step number (1-6)
            confidence: Current confidence level

        Returns:
            List of required actions for this step
        """
        guidance = get_step_guidance(step_number)
        return guidance.required_actions

    def _generate_guidance(
        self, request: WorkflowRequest, state: Any
    ) -> StepGuidance:
        """Generate guidance for the next step.

        Overrides base class to use accessibility-specific step guidance.

        Args:
            request: Current step request
            state: Current workflow state

        Returns:
            StepGuidance with accessibility-specific actions
        """
        return get_step_guidance(request.step_number)

    def execute(self, **kwargs: Any) -> WorkflowResponse:
        """Execute with a11y-audit-specific parameter handling.

        Maps accessibility_audit parameters to workflow request format.

        Args:
            **kwargs: Accessibility audit request parameters including project_root_path

        Returns:
            WorkflowResponse with audit results
        """
        step_number = kwargs.get("step_number", 1)
        project_root_path = kwargs.get("project_root_path")

        mapped_kwargs = {
            "step": A11Y_AUDIT_STEPS.get(step_number, f"Step {step_number}"),
            "step_number": step_number,
            "total_steps": TOTAL_STEPS,
            "next_step_required": kwargs.get("next_step_required", True),
            "findings": kwargs.get("findings", ""),
            "confidence": kwargs.get("confidence", "exploring"),
            "files_checked": kwargs.get("files_examined", []),
            "continuation_id": kwargs.get("continuation_id"),
            "accessibility_findings": kwargs.get("accessibility_findings", []),
            "accessibility_assessments": kwargs.get("accessibility_assessments", {}),
        }

        response = super().execute(**mapped_kwargs)

        if step_number == 1 and project_root_path:
            state = self._state_manager.get(response.continuation_id)
            if state:
                state.project_root_path = project_root_path
                self._state_manager.save(state)

        return response

    def process_step(self, request: WorkflowRequest) -> WorkflowResponse:
        """Process an accessibility audit step.

        Handles accessibility-specific processing including:
        - Parsing accessibility_findings from request
        - Adding findings to consolidated findings

        Args:
            request: The workflow step request

        Returns:
            WorkflowResponse with accessibility audit results
        """
        response = super().process_step(request)

        state = self._state_manager.get(response.continuation_id)
        if state and state.consolidated:
            self._process_accessibility_findings(request, state.consolidated)
            self._state_manager.save(state)

        return response

    def _process_accessibility_findings(
        self, request: WorkflowRequest, consolidated: ConsolidatedFindings
    ) -> None:
        """Process accessibility-specific findings from the request.

        Args:
            request: The workflow request with potential findings
            consolidated: Consolidated findings to update
        """
        logger = self._get_logger()
        raw_data = getattr(request, "_raw_data", {})
        findings = raw_data.get("accessibility_findings", [])

        for finding_data in findings:
            finding = AccessibilityFinding.from_dict(finding_data)
            logger.debug(f"Found {finding.wcag_level} issue: {finding.wcag_criterion}")
            consolidated.add_issue(finding.to_dict())

        assessments = raw_data.get("accessibility_assessments", {})
        if assessments:
            for domain, assessment in assessments.items():
                consolidated.add_context([f"{domain}: {assessment}"])

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
        logger.debug("Workflow completing")

        if state.consolidated is not None:
            self._process_accessibility_findings(request, state.consolidated)
            self._state_manager.save(state)

        response = super()._handle_completion(state, request)

        summary = self._format_completion_summary(state)
        response.message = f"{summary}\n\n"

        return response
