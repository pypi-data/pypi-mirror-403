"""DevOpsAuditTool - Multi-step DevOps infrastructure analysis workflow tool."""

from typing import Any, Optional

from tools.devops_audit.finding import ConsolidatedDevOpsFindings, DevOpsFinding
from tools.devops_audit.guidance import TOTAL_STEPS, get_step_guidance
from tools.workflow.base import WorkflowTool
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings
from tools.workflow.guidance import StepGuidance
from tools.workflow.request import WorkflowRequest
from tools.workflow.response import WorkflowResponse
from tools.workflow.state import WorkflowState

DEVOPS_AUDIT_STEPS = {
    1: "Docker Infrastructure Audit",
    2: "CI/CD Pipeline Audit",
    3: "Dependency Security Audit",
    4: "Cross-Domain Analysis",
}


class DevOpsAuditTool(WorkflowTool):
    """DevOps audit workflow tool with 4-step guided analysis.

    Guides users through systematic infrastructure analysis covering:
    1. Docker Infrastructure - Dockerfile security, base images, USER directive
    2. CI/CD Pipeline - GitHub Actions security, secrets, permissions
    3. Dependency Security - lockfiles, version ranges, supply-chain
    4. Cross-Domain Analysis - compound risks, integration gaps, report

    Expert analysis is handled by the base WorkflowTool class when
    EXPERT_ANALYSIS_ENABLED=true and the workflow completes.
    """

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "devops_audit"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return (
            "Perform a guided multi-step DevOps audit analyzing repository "
            "infrastructure files (Dockerfiles, GitHub Actions workflows, "
            "Node.js dependencies) for security and operational best practices."
        )

    @property
    def total_steps(self) -> int:
        """Total number of steps in the DevOps audit workflow."""
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
        if isinstance(consolidated, ConsolidatedDevOpsFindings):
            summary = consolidated.get_devops_audit_summary()
        else:
            summary = consolidated.get_audit_summary()

        by_severity = consolidated.get_findings_by_severity()

        return {
            "task": "validate_devops_findings",
            "summary": summary,
            "critical_findings": by_severity["critical"],
            "high_findings": by_severity["high"],
            "files_examined": list(consolidated.files_checked),
            "confidence": consolidated.confidence.value,
        }

    def get_required_actions(
        self, step_number: int, confidence: ConfidenceLevel
    ) -> list[str]:
        """Get DevOps-specific required actions for the step.

        Args:
            step_number: Current step number (1-4)
            confidence: Client's current confidence level

        Returns:
            List of required action strings
        """
        guidance = get_step_guidance(step_number, confidence, self.name)
        return guidance.required_actions

    def execute(self, **kwargs: Any) -> WorkflowResponse:
        """Execute with devops-audit-specific parameter handling.

        Maps devops_audit parameters to workflow request format.

        Args:
            **kwargs: DevOps audit request parameters including project_root_path

        Returns:
            WorkflowResponse with audit results
        """
        step_number = kwargs.get("step_number", 1)
        project_root_path = kwargs.get("project_root_path")

        self._log(f"Processing step {step_number}: {DEVOPS_AUDIT_STEPS.get(step_number, 'Unknown')}")

        mapped_kwargs = {
            "step": DEVOPS_AUDIT_STEPS.get(step_number, f"Step {step_number}"),
            "step_number": step_number,
            "total_steps": TOTAL_STEPS,
            "next_step_required": kwargs.get("next_step_required", True),
            "findings": kwargs.get("findings", ""),
            "confidence": kwargs.get("confidence", "exploring"),
            "files_checked": kwargs.get("files_examined", []),
            "continuation_id": kwargs.get("continuation_id"),
            "devops_issues_found": kwargs.get("devops_issues_found", []),
            "devops_assessments": kwargs.get("devops_assessments", {}),
            "artifacts_analyzed": kwargs.get("artifacts_analyzed", {}),
            "missing_context": kwargs.get("missing_context", []),
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
        """Generate DevOps-specific guidance for the next step.

        Args:
            request: Current step request
            state: Current workflow state

        Returns:
            StepGuidance with DevOps-specific actions
        """
        missing_context = self._get_missing_context(state)

        devops_guidance = get_step_guidance(
            request.step_number, request.confidence, self.name, missing_context
        )

        suggestions = devops_guidance.focus_areas.copy()
        if devops_guidance.missing_context_hints:
            suggestions.extend(devops_guidance.missing_context_hints)

        return StepGuidance(
            required_actions=devops_guidance.required_actions,
            suggestions=suggestions,
            next_step_focus=devops_guidance.domain.display_name,
            confidence_guidance=devops_guidance.next_steps,
        )

    def process_step(self, request: WorkflowRequest) -> WorkflowResponse:
        """Process a DevOps audit step.

        Handles DevOps-specific processing including:
        - Parsing devops_issues_found from request
        - Tracking artifacts analyzed/omitted
        - Adding issues to consolidated findings

        Args:
            request: The workflow step request

        Returns:
            WorkflowResponse with DevOps audit results
        """
        state, is_new = self._state_manager.get_or_create(
            request.continuation_id, self.name
        )

        if is_new or not isinstance(state.consolidated, ConsolidatedDevOpsFindings):
            state.consolidated = ConsolidatedDevOpsFindings()
            self._state_manager.save(state)

        request.continuation_id = state.continuation_id
        response = super().process_step(request)

        state = self._state_manager.get(response.continuation_id)
        if state and not isinstance(state.consolidated, ConsolidatedDevOpsFindings):
            state.consolidated = ConsolidatedDevOpsFindings()
            self._state_manager.save(state)

        if not response.workflow_complete:
            state = self._state_manager.get(response.continuation_id)
            if state and state.consolidated:
                self._process_devops_findings(request, state.consolidated)
                self._process_artifact_tracking(request, state.consolidated)
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
        self._log("Workflow completing")

        if state.consolidated is not None:
            self._process_devops_findings(request, state.consolidated)
            self._process_artifact_tracking(request, state.consolidated)
            self._state_manager.save(state)

        response = super()._handle_completion(state, request)

        summary = self._format_completion_summary(state)
        response.message = f"{summary}\n\n"

        return response

    def _process_devops_findings(
        self, request: WorkflowRequest, consolidated: ConsolidatedFindings
    ) -> None:
        """Process DevOps-specific findings from the request.

        Args:
            request: The workflow request with potential findings
            consolidated: Consolidated findings to update
        """
        raw_data = getattr(request, "_raw_data", {})
        devops_issues = raw_data.get("devops_issues_found", [])

        for issue_data in devops_issues:
            try:
                finding = DevOpsFinding.from_dict(issue_data)
                consolidated.add_issue(finding.to_dict())
                self._log(f"Added finding: {finding.severity.value} - {finding.description[:50]}...")
            except (KeyError, ValueError) as e:
                self._log(f"Skipping invalid finding: {e}", error=True)

        assessments = raw_data.get("devops_assessments", {})
        if assessments:
            for domain, assessment in assessments.items():
                consolidated.add_context([f"{domain}: {assessment}"])

    def _process_artifact_tracking(
        self, request: WorkflowRequest, consolidated: ConsolidatedFindings
    ) -> None:
        """Track analyzed and omitted artifacts.

        Args:
            request: The workflow request with artifact data
            consolidated: Consolidated findings to update
        """
        if not isinstance(consolidated, ConsolidatedDevOpsFindings):
            return

        raw_data = getattr(request, "_raw_data", {})
        artifacts = raw_data.get("artifacts_analyzed", {})

        if not isinstance(artifacts, dict):
            return

        if "dockerfiles" in artifacts:
            docker_data = artifacts["dockerfiles"]
            consolidated.dockerfiles_analyzed.extend(docker_data.get("analyzed", []))
            consolidated.dockerfiles_omitted.extend(docker_data.get("omitted", []))

        if "workflows" in artifacts:
            workflow_data = artifacts["workflows"]
            consolidated.workflows_analyzed.extend(workflow_data.get("analyzed", []))
            consolidated.workflows_omitted.extend(workflow_data.get("omitted", []))

        if "package_files" in artifacts:
            package_data = artifacts["package_files"]
            consolidated.package_files_analyzed.extend(package_data.get("analyzed", []))
            consolidated.package_files_omitted.extend(package_data.get("omitted", []))

        missing = raw_data.get("missing_context", [])
        for item in missing:
            if "lock" in item.lower():
                if item not in consolidated.missing_lockfiles:
                    consolidated.missing_lockfiles.append(item)
            else:
                if item not in consolidated.missing_context_requested:
                    consolidated.missing_context_requested.append(item)

    def _get_missing_context(self, state: WorkflowState) -> Optional[list[str]]:
        """Get list of missing context files from state.

        Args:
            state: Current workflow state

        Returns:
            List of missing context file paths, or None
        """
        if isinstance(state.consolidated, ConsolidatedDevOpsFindings):
            missing = []
            missing.extend(state.consolidated.missing_lockfiles)
            missing.extend(state.consolidated.missing_context_requested)
            return missing if missing else None
        return None

    def _log(self, message: str, error: bool = False) -> None:
        """Log message using the logging system.

        Args:
            message: Log message
            error: If True, log as warning level
        """
        logger = self._get_logger()
        if error:
            logger.warn(message)
        else:
            logger.debug(message)
