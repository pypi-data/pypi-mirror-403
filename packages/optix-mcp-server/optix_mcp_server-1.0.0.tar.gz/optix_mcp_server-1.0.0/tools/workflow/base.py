"""WorkflowTool abstract base class for multi-step workflow tools."""

import asyncio
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from logging_utils import get_tool_logger
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.guidance import StepGuidance
from tools.workflow.request import WorkflowRequest
from tools.workflow.response import WorkflowResponse
from tools.workflow.state import StepHistory, WorkflowState, WorkflowStateManager
from tools.workflow.validation import validate_request

logger = logging.getLogger(__name__)


class WorkflowTool(ABC):
    """Abstract base class for multi-step workflow tools.

    Provides infrastructure for:
    - Step processing and context accumulation
    - Continuation ID generation and resumption
    - Workflow completion detection
    - Deferred API execution pattern

    Subclasses must implement:
    - name: Tool identifier
    - description: Tool description
    - should_call_expert_analysis: Whether to call external API at completion
    - prepare_expert_analysis_context: Format context for external API
    """

    def __init__(self) -> None:
        """Initialize the workflow tool."""
        self._state_manager = WorkflowStateManager()
        self._expert_service: Optional[Any] = None
        self._logger = None

    def _get_logger(self):
        """Get or create logger for this tool."""
        if self._logger is None:
            self._logger = get_tool_logger(self.name)
        return self._logger

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool.

        Returns:
            Tool name (lowercase, alphanumeric with underscores)
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description.

        Returns:
            Description string for MCP schema and documentation
        """
        ...

    @abstractmethod
    def prepare_expert_analysis_context(self, consolidated: Any) -> dict[str, Any]:
        """Prepare context for expert analysis API call.

        Called only when should_call_expert_analysis returns True.
        Formats accumulated workflow context for the external API.

        Args:
            consolidated: ConsolidatedFindings from the workflow

        Returns:
            Dictionary of context for API call
        """
        ...

    def execute(self, **kwargs: Any) -> WorkflowResponse:
        """Execute the workflow tool with given arguments.

        Validates the request and delegates to process_step.

        Args:
            **kwargs: Workflow request parameters

        Returns:
            WorkflowResponse with results

        Raises:
            ValidationError: If request validation fails
        """
        validate_request(kwargs)
        request = WorkflowRequest.from_dict(kwargs)
        return self.process_step(request)

    def process_step(self, request: WorkflowRequest) -> WorkflowResponse:
        """Process a single workflow step.

        Handles:
        - Creating new workflows or resuming existing ones
        - Storing step data in workflow state
        - Detecting workflow completion
        - Triggering final analysis when appropriate

        Args:
            request: The workflow step request

        Returns:
            WorkflowResponse with continuation ID and status
        """
        logger = self._get_logger()
        logger.debug(f"Step {request.step_number}: Starting {request.step}")

        state, is_new = self._state_manager.get_or_create(
            request.continuation_id, self.name
        )

        if state.is_cancelled:
            logger.info(f"Workflow {state.continuation_id} was cancelled, returning early")
            return WorkflowResponse(
                continuation_id=state.continuation_id,
                step_processed=request.step_number,
                workflow_complete=True,
                cancelled=True,
                guidance=StepGuidance(
                    required_actions=[
                        "STOP: This audit has been cancelled by the user via the dashboard",
                        "DO NOT continue this audit or call this tool again",
                        "Inform the user that the audit was stopped as requested",
                    ],
                    suggestions=[],
                    next_step_focus=None,
                    confidence_guidance="CANCELLED - Do not proceed",
                ),
                message=(
                    "AUDIT CANCELLED: The user has stopped this audit via the Optix dashboard. "
                    "Do NOT continue or retry this audit. Inform the user that the audit was "
                    "stopped as requested. If they want to run another audit, they should "
                    "start a new one."
                ),
            )

        if is_new:
            logger.debug(f"Step {request.step_number}: Created new workflow {state.continuation_id}")
        else:
            logger.debug(f"Step {request.step_number}: Resuming workflow {state.continuation_id}")

        files_count = len(request.files_checked) if request.files_checked else 0
        if files_count > 0:
            logger.debug(f"Step {request.step_number}: Examining {files_count} files")

        step = StepHistory(
            step_number=request.step_number,
            step_content=request.step,
            findings=request.findings,
            confidence=request.confidence,
            hypothesis=request.hypothesis,
            files_checked=request.files_checked,
            relevant_files=request.relevant_files,
        )
        state.add_step(step)
        self._state_manager.save(state)

        if not request.next_step_required:
            logger.info(f"Step {request.step_number} completed: workflow finishing")
            return self._handle_completion(state, request)

        findings_count = len(state.consolidated.issues_found) if state.consolidated else 0
        logger.info(f"Step {request.step_number} completed: {findings_count} findings")

        guidance = self._generate_guidance(request, state)

        return WorkflowResponse(
            continuation_id=state.continuation_id,
            step_processed=request.step_number,
            workflow_complete=False,
            guidance=guidance,
        )

    def _handle_completion(
        self, state: WorkflowState, request: WorkflowRequest
    ) -> WorkflowResponse:
        """Handle workflow completion.

        Called when next_step_required is False.
        Checks if expert analysis should be triggered and prepares response.

        Args:
            state: Current workflow state
            request: The final step request

        Returns:
            WorkflowResponse with completion data
        """
        logger = self._get_logger()
        state.is_finished = True
        self._state_manager.save(state)
        consolidated = state.consolidated
        expert_analysis = None
        expert_result = None

        # Check if expert analysis should run
        from config.defaults import ServerConfiguration

        config = ServerConfiguration.from_env()

        total_findings = len(consolidated.issues_found) if consolidated else 0
        logger.debug(
            f"Expert analysis check: enabled={config.expert_analysis_enabled}, "
            f"consolidated={'present' if consolidated else 'None'}, "
            f"findings={total_findings}"
        )

        if config.expert_analysis_enabled and consolidated is not None:
            if total_findings == 0:
                logger.info("Skipping expert analysis: no findings to analyze")
            else:
                logger.info(f"Starting expert analysis for {total_findings} findings")
                # Run expert analysis in a separate thread to avoid event loop conflicts
                def _run_in_thread():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(
                            self._run_expert_analysis(consolidated)
                        )
                    finally:
                        loop.close()

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_run_in_thread)
                    expert_result = future.result()

                if expert_result:
                    expert_analysis = expert_result.to_dict()
                    logger.info("Expert analysis completed successfully")
                else:
                    logger.warn("Expert analysis returned None")
        elif not config.expert_analysis_enabled:
            logger.debug("Expert analysis disabled in configuration")
        elif consolidated is None:
            logger.warn("Expert analysis skipped: consolidated findings is None")

        consolidated_summary = None
        if consolidated is not None and hasattr(consolidated, "to_dict"):
            consolidated_summary = consolidated.to_dict()

        logger.info(f"Workflow completed: {total_findings} total findings")

        return WorkflowResponse(
            continuation_id=state.continuation_id,
            step_processed=request.step_number,
            workflow_complete=True,
            expert_analysis=expert_analysis,
            consolidated_summary=consolidated_summary,
        )

    async def _run_expert_analysis(self, consolidated: Any) -> Optional[Any]:
        """
        Execute expert analysis on consolidated findings.

        Args:
            consolidated: ConsolidatedFindings object

        Returns:
            ExpertAnalysisResult on success, None on failure/disabled
        """
        from config.defaults import ServerConfiguration
        from tools.expert_analysis.service import ExpertAnalysisService

        try:
            # Lazy-init expert service
            if not self._expert_service:
                config = ServerConfiguration.from_env()

                # Get LLM provider config
                if not config.api_keys:
                    logger.warning(
                        "Expert analysis enabled but API keys not configured"
                    )
                    return None

                llm_config = config.api_keys.get_llm_provider_config()
                if not llm_config or not llm_config.api_key:
                    logger.warning(
                        "Expert analysis enabled but LLM provider not configured"
                    )
                    return None

                self._expert_service = ExpertAnalysisService(llm_config)

            # Execute with timeout
            timeout = ServerConfiguration.from_env().expert_analysis_timeout
            return await asyncio.wait_for(
                self._expert_service.analyze_findings(consolidated, self.name),
                timeout=timeout,
            )

        except asyncio.TimeoutError:
            logger.error("Expert analysis timed out")
            return None
        except Exception as e:
            logger.error(f"Expert analysis failed: {e}", exc_info=True)
            return None

    def _generate_guidance(
        self, request: WorkflowRequest, state: WorkflowState
    ) -> StepGuidance:
        """Generate guidance for the next step.

        Default implementation provides basic guidance based on
        step number and confidence level. Subclasses can override
        get_required_actions() for domain-specific guidance.

        Args:
            request: Current step request
            state: Current workflow state

        Returns:
            StepGuidance with actions for next step
        """
        actions = self.get_required_actions(request.step_number, request.confidence)

        return StepGuidance(
            required_actions=actions,
            suggestions=[],
            next_step_focus=None,
            confidence_guidance=self._get_confidence_guidance(request.confidence),
        )

    def get_required_actions(
        self, step_number: int, confidence: ConfidenceLevel
    ) -> list[str]:
        """Get required actions for the next step.

        Default implementation provides generic guidance. Subclasses
        should override this for domain-specific actions.

        Args:
            step_number: Current step number
            confidence: Current confidence level

        Returns:
            List of action strings
        """
        if confidence <= ConfidenceLevel.LOW:
            return [
                "Broaden investigation scope",
                "Gather more evidence",
                "Form initial hypothesis",
            ]
        elif confidence <= ConfidenceLevel.MEDIUM:
            return [
                "Focus on promising leads",
                "Verify findings",
                "Refine hypothesis",
            ]
        elif confidence <= ConfidenceLevel.HIGH:
            return [
                "Validate hypothesis with additional evidence",
                "Check for edge cases",
                "Document findings",
            ]
        else:
            return [
                "Final verification",
                "Prepare conclusion",
                "Document root cause",
            ]

    def _get_confidence_guidance(self, confidence: ConfidenceLevel) -> str:
        """Get guidance on how to increase confidence.

        Args:
            confidence: Current confidence level

        Returns:
            Guidance string
        """
        guidance_map = {
            ConfidenceLevel.EXPLORING: "Identify key areas to investigate",
            ConfidenceLevel.LOW: "Gather supporting evidence for hypothesis",
            ConfidenceLevel.MEDIUM: "Test hypothesis against additional cases",
            ConfidenceLevel.HIGH: "Verify findings and check edge cases",
            ConfidenceLevel.VERY_HIGH: "Document and prepare final conclusion",
            ConfidenceLevel.ALMOST_CERTAIN: "Final verification before concluding",
            ConfidenceLevel.CERTAIN: "Ready to complete - no further investigation needed",
        }
        return guidance_map.get(confidence, "Continue investigation")

    def _format_completion_summary(self, state: WorkflowState) -> str:
        """Format a user-friendly audit completion summary.

        Args:
            state: Current workflow state with consolidated findings

        Returns:
            Formatted markdown summary string
        """
        consolidated = state.consolidated
        if consolidated is None:
            return "## Audit Complete\n\nNo findings collected during audit."

        by_severity = consolidated.get_findings_by_severity()
        severity_counts = {k: len(v) for k, v in by_severity.items() if isinstance(v, list)}

        total = sum(severity_counts.values())
        files_count = len(getattr(consolidated, 'files_checked', set()))

        lines = [
            "## Audit Complete",
            "",
            f"**Total Findings:** {total}",
            f"**Files Examined:** {files_count}",
            "",
            "### Findings by Severity:",
        ]

        for severity in ["critical", "high", "medium", "low", "info"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                lines.append(f"- **{severity.upper()}**: {count}")

        if total == 0:
            lines.append("- No issues found")

        lines.append("")
        lines.append("Inform the user about the possible markdown report they can generate from the audit findings.")

        return "\n".join(lines)
