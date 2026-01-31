"""PrincipalAuditTool - Multi-step code quality analysis workflow tool."""

from typing import Any, Optional

from tools.principal_audit.finding import (
    ConsolidatedPrincipalFindings,
    PrincipalEngineerFinding,
)
from tools.principal_audit.guidance import TOTAL_STEPS, get_step_guidance
from tools.workflow.base import WorkflowTool
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings
from tools.workflow.guidance import StepGuidance
from tools.workflow.request import WorkflowRequest
from tools.workflow.response import WorkflowResponse
from tools.workflow.state import WorkflowState

PRINCIPAL_AUDIT_STEPS = {
    1: "Complexity Analysis",
    2: "DRY Violation Detection",
    3: "Coupling Analysis",
    4: "Separation of Concerns",
    5: "Maintainability Assessment",
}


class PrincipalAuditTool(WorkflowTool):
    """Principal Engineer audit workflow tool with 5-step guided analysis.

    Guides users through systematic code quality analysis covering:
    1. Complexity Analysis - Cyclomatic complexity detection
    2. DRY Violation Detection - Code duplication analysis
    3. Coupling Analysis - Module dependencies and coupling metrics
    4. Separation of Concerns - Responsibility mixing detection
    5. Maintainability Assessment - General maintainability + report

    LLM API calls are DEFERRED until Step 5 when next_step_required=false,
    following the MCP-Client interaction pattern in CLAUDE.md.
    """

    def __init__(self) -> None:
        super().__init__()
        self._validator = None

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "principal_audit"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return (
            "Perform a guided multi-step Principal Engineer audit analyzing "
            "code quality, maintainability, and architectural soundness. "
            "Analyzes complexity, DRY violations, coupling, separation of "
            "concerns, and maintainability risks."
        )

    @property
    def total_steps(self) -> int:
        """Total number of steps in the Principal Engineer audit workflow."""
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
        if isinstance(consolidated, ConsolidatedPrincipalFindings):
            summary = consolidated.get_audit_summary()
            by_severity = consolidated.get_findings_by_severity()

            return {
                "task": "validate_principal_findings",
                "summary": summary,
                "critical_findings": [f.to_dict() for f in by_severity["critical"]],
                "high_findings": [f.to_dict() for f in by_severity["high"]],
                "files_examined": consolidated.files_analyzed,
                "confidence": consolidated.confidence.value,
            }
        else:
            summary = consolidated.get_audit_summary()
            by_severity = consolidated.get_findings_by_severity()

            return {
                "task": "validate_principal_findings",
                "summary": summary,
                "critical_findings": by_severity["critical"],
                "high_findings": by_severity["high"],
                "files_examined": list(consolidated.files_checked),
                "confidence": consolidated.confidence.value,
            }

    def get_required_actions(
        self, step_number: int, confidence: ConfidenceLevel
    ) -> list[str]:
        """Get Principal-audit-specific required actions for the step.

        Args:
            step_number: Current step number (1-5)
            confidence: Client's current confidence level

        Returns:
            List of required action strings
        """
        try:
            guidance = get_step_guidance(step_number, confidence)
            return guidance.required_actions
        except ValueError:
            return super().get_required_actions(step_number, confidence)

    def execute(self, **kwargs: Any) -> WorkflowResponse:
        """Execute with principal-audit-specific parameter handling.

        Maps principal_audit parameters to workflow request format.

        Args:
            **kwargs: Principal audit request parameters

        Returns:
            WorkflowResponse with audit results
        """
        step_number = kwargs.get("step_number", 1)
        project_root_path = kwargs.get("project_root_path")

        self._log(f"Processing step {step_number}: {PRINCIPAL_AUDIT_STEPS.get(step_number, 'Unknown')}")

        mapped_kwargs = {
            "step": PRINCIPAL_AUDIT_STEPS.get(step_number, f"Step {step_number}"),
            "step_number": step_number,
            "total_steps": TOTAL_STEPS,
            "next_step_required": kwargs.get("next_step_required", True),
            "findings": kwargs.get("findings", ""),
            "confidence": kwargs.get("confidence", "exploring"),
            "files_checked": kwargs.get("files_examined", []),
            "continuation_id": kwargs.get("continuation_id"),
            "principal_findings": kwargs.get("principal_findings", []),
            "principal_assessments": kwargs.get("principal_assessments", {}),
        }

        response = super().execute(**mapped_kwargs)

        if step_number == 1 and project_root_path:
            state = self._state_manager.get(response.continuation_id)
            if state:
                state.project_root_path = project_root_path
                self._state_manager.save(state)
                self._log(f"Stored project_root_path: {project_root_path}")

        return response

    def _generate_guidance(
        self, request: WorkflowRequest, state: WorkflowState
    ) -> StepGuidance:
        """Generate Principal-audit-specific guidance for the next step.

        Args:
            request: Current step request
            state: Current workflow state

        Returns:
            StepGuidance with Principal-audit-specific actions
        """
        missing_context = self._get_missing_context(state)

        try:
            principal_guidance = get_step_guidance(
                request.step_number, request.confidence, missing_context
            )

            suggestions = principal_guidance.focus_areas.copy()
            if principal_guidance.missing_context_hints:
                suggestions.extend(principal_guidance.missing_context_hints)

            return StepGuidance(
                required_actions=principal_guidance.required_actions,
                suggestions=suggestions,
                next_step_focus=principal_guidance.next_step_focus,
                confidence_guidance=principal_guidance.confidence_guidance,
            )
        except ValueError:
            return super()._generate_guidance(request, state)

    def process_step(self, request: WorkflowRequest) -> WorkflowResponse:
        """Process a Principal Engineer audit step.

        Handles Principal-audit-specific processing including:
        - Parsing principal_findings from request
        - Adding findings to consolidated state
        - Step-specific analysis routing

        Args:
            request: The workflow step request

        Returns:
            WorkflowResponse with Principal audit results
        """
        self._log(f"Step {request.step_number}: continuation_id from request = {request.continuation_id}", info=True)

        state, is_new = self._state_manager.get_or_create(
            request.continuation_id, self.name
        )

        self._log(f"Step {request.step_number}: is_new={is_new}, state.continuation_id={state.continuation_id}", info=True)
        self._log(f"Step {request.step_number}: step_history length before super = {len(state.step_history)}", info=True)

        if is_new or not isinstance(state.consolidated, ConsolidatedPrincipalFindings):
            state.consolidated = ConsolidatedPrincipalFindings()
            self._state_manager.save(state)

        request.continuation_id = state.continuation_id
        response = super().process_step(request)

        state = self._state_manager.get(response.continuation_id)
        if state:
            self._log(f"Step {request.step_number}: step_history length after super = {len(state.step_history)}", info=True)
            step_numbers = [s.step_number for s in state.step_history]
            self._log(f"Step {request.step_number}: step_numbers in history = {step_numbers}", info=True)

        if state and state.consolidated and not response.workflow_complete:
            self._process_principal_findings(request, state.consolidated)
            self._state_manager.save(state)
            if isinstance(state.consolidated, ConsolidatedPrincipalFindings):
                findings_count = len(state.consolidated.get_all_findings())
                self._log(f"Step {request.step_number} completed: {findings_count} findings", info=True)

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
        self._log("Workflow completing")

        if state.consolidated is not None:
            self._process_principal_findings(request, state.consolidated)
            self._state_manager.save(state)
            if isinstance(state.consolidated, ConsolidatedPrincipalFindings):
                findings_count = len(state.consolidated.get_all_findings())
                self._log(f"Final step findings processed: {findings_count} total findings", info=True)

        response = super()._handle_completion(state, request)

        summary = self._format_completion_summary(state)
        response.message = f"{summary}\n\n"

        return response

    def _process_principal_findings(
        self, request: WorkflowRequest, consolidated: ConsolidatedFindings
    ) -> None:
        """Process Principal-audit-specific findings from the request.

        Args:
            request: The workflow request with potential findings
            consolidated: Consolidated findings to update
        """
        if not isinstance(consolidated, ConsolidatedPrincipalFindings):
            return

        raw_data = getattr(request, "_raw_data", {})
        principal_findings = raw_data.get("principal_findings", [])

        self._log(f"Processing {len(principal_findings)} principal findings")

        for i, finding_data in enumerate(principal_findings, 1):
            try:
                is_valid, missing = PrincipalEngineerFinding.validate_dict(finding_data)
                if not is_valid:
                    self._log(
                        f"Skipping invalid finding - missing fields: {missing}. "
                        f"Got keys: {list(finding_data.keys())}",
                        error=True
                    )
                    continue

                consolidated.add_issue(finding_data)
                self._log(
                    f"Added finding {i}/{len(principal_findings)}: "
                    f"{finding_data.get('severity', 'unknown')} - "
                    f"{finding_data.get('description', '')[:50]}..."
                )
            except (KeyError, ValueError) as e:
                import json
                self._log(
                    f"Skipping invalid finding {i}/{len(principal_findings)}: {e}",
                    error=True
                )
                self._log(
                    f"Invalid finding data: {json.dumps(finding_data, indent=2)[:500]}",
                    error=True
                )

        files = raw_data.get("files_checked", raw_data.get("files_examined", []))
        consolidated.files_analyzed.extend(f for f in files if f not in consolidated.files_analyzed)

        assessments = raw_data.get("principal_assessments", {})
        if assessments:
            for domain, assessment in assessments.items():
                consolidated.add_context([f"{domain}: {assessment}"])

    def _get_missing_context(self, state: WorkflowState) -> Optional[list[str]]:
        """Get list of missing context files from state.

        Args:
            state: Current workflow state

        Returns:
            List of missing context file paths, or None
        """
        if isinstance(state.consolidated, ConsolidatedPrincipalFindings):
            missing = []
            requested = state.consolidated.requested_context
            provided = state.consolidated.provided_context
            missing.extend(r for r in requested if r not in provided)
            return missing if missing else None
        return None

    def _log(self, message: str, error: bool = False, info: bool = False) -> None:
        """Log message using the logging system.

        Args:
            message: Log message
            error: If True, log as warning level
            info: If True, log as info level (ignored if error=True)
        """
        logger = self._get_logger()
        if error:
            logger.warn(message)
        elif info:
            logger.info(message)
        else:
            logger.debug(message)
