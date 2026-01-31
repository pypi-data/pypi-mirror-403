"""Unit tests for SecurityAuditTool."""

import os
import pytest

from tools.security_audit.tool import SecurityAuditTool
from tools.workflow.state import WorkflowStateManager


@pytest.fixture(autouse=True)
def clear_workflow_state():
    """Clear workflow state before each test."""
    WorkflowStateManager().clear_all()
    yield
    WorkflowStateManager().clear_all()


@pytest.fixture
def enable_expert_analysis(monkeypatch):
    """Enable expert analysis for tests that need it."""
    monkeypatch.setenv("EXPERT_ANALYSIS_ENABLED", "true")
    monkeypatch.setenv("OPTIX_LLM_PROVIDER", "openai")
    yield


@pytest.fixture
def disable_expert_analysis(monkeypatch):
    """Disable expert analysis for tests that need it disabled."""
    monkeypatch.setenv("EXPERT_ANALYSIS_ENABLED", "false")
    yield


class TestSecurityAuditToolInit:
    """Tests for SecurityAuditTool initialization (T010)."""

    def test_tool_has_name(self):
        """Tool must have a name property."""
        tool = SecurityAuditTool()
        assert tool.name == "security_audit"

    def test_tool_has_description(self):
        """Tool must have a description property."""
        tool = SecurityAuditTool()
        assert "security" in tool.description.lower()
        assert len(tool.description) > 10

    def test_tool_total_steps_is_six(self):
        """Tool must have 6 total steps."""
        tool = SecurityAuditTool()
        assert tool.total_steps == 6


class TestStep1Processing:
    """Tests for step 1 processing - new audit (T011)."""

    def test_step1_returns_pause_status(self):
        """Step 1 should return pause_for_secaudit status."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        assert response.workflow_complete is False

    def test_step1_returns_continuation_id(self):
        """Step 1 should return a continuation_id."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        assert response.continuation_id is not None
        assert len(response.continuation_id) > 0

    def test_step1_returns_guidance(self):
        """Step 1 should return guidance with required_actions."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        assert response.guidance is not None
        assert len(response.guidance.required_actions) > 0


class TestContinuationIdGeneration:
    """Tests for continuation_id generation (T012)."""

    def test_continuation_id_is_uuid_format(self):
        """Continuation ID should be a valid UUID format."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        parts = response.continuation_id.split("-")
        assert len(parts) == 5

    def test_new_audit_generates_new_continuation_id(self):
        """Each new audit should get a unique continuation_id."""
        tool = SecurityAuditTool()
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        WorkflowStateManager().clear_all()
        response2 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        assert response1.continuation_id != response2.continuation_id

    def test_provided_continuation_id_is_used(self):
        """If continuation_id is provided, it should be used."""
        tool = SecurityAuditTool()
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        response2 = tool.execute(
            step_number=2,
            continuation_id=response1.continuation_id,
            next_step_required=True,
            files_examined=["test.py"],
            confidence="low",
        )
        assert response2.continuation_id == response1.continuation_id


class TestStepProgression:
    """Tests for multi-step progression (T019)."""

    def test_step_progression_2_to_6(self):
        """Steps should progress from 2 through 6 correctly."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        for step in range(2, 7):
            response = tool.execute(
                step_number=step,
                continuation_id=continuation_id,
                next_step_required=(step < 6),
                files_examined=[f"file_{step}.py"],
                confidence="medium",
            )
            assert response.step_processed == step
            assert response.continuation_id == continuation_id

    def test_final_step_completes_workflow(self):
        """Step 6 with next_step_required=False should complete workflow."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        for step in range(2, 6):
            tool.execute(
                step_number=step,
                continuation_id=continuation_id,
                next_step_required=True,
                files_examined=[f"file_{step}.py"],
                confidence="medium",
            )

        response = tool.execute(
            step_number=6,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["final.py"],
            confidence="high",
        )
        assert response.workflow_complete is True


class TestFindingsAccumulation:
    """Tests for findings accumulation across steps (T020)."""

    def test_files_accumulate_across_steps(self):
        """Files from all steps should be accumulated."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["app.py", "main.py"],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["auth.py", "session.py"],
            confidence="low",
        )

        tool.execute(
            step_number=3,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["input.py"],
            confidence="medium",
        )

        state = WorkflowStateManager().get(continuation_id)
        assert state is not None
        assert state.consolidated is not None
        all_files = state.consolidated.files_checked
        assert "app.py" in all_files
        assert "main.py" in all_files
        assert "auth.py" in all_files
        assert "session.py" in all_files
        assert "input.py" in all_files

    def test_vulnerabilities_accumulate_across_steps(self):
        """Vulnerabilities from all steps should be accumulated."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
            vulnerabilities_found=[],
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["auth.py"],
            confidence="low",
            vulnerabilities_found=[
                {
                    "severity": "high",
                    "category": "authentication",
                    "description": "Weak password policy",
                    "affected_files": ["auth.py"],
                }
            ],
        )

        tool.execute(
            step_number=3,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["input.py"],
            confidence="medium",
            vulnerabilities_found=[
                {
                    "severity": "critical",
                    "category": "injection",
                    "description": "SQL injection in query",
                    "affected_files": ["input.py"],
                }
            ],
        )

        state = WorkflowStateManager().get(continuation_id)
        assert state is not None
        assert state.consolidated is not None
        issues = state.consolidated.issues_found
        assert len(issues) == 2

    def test_security_assessments_accumulate(self):
        """Security assessments should be accumulated as context."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["auth.py"],
            confidence="medium",
            security_assessments={
                "authentication": "Uses bcrypt for password hashing",
                "session": "JWT with 1-hour expiry",
            },
        )

        state = WorkflowStateManager().get(continuation_id)
        assert state is not None
        assert state.consolidated is not None
        context = state.consolidated.relevant_context
        assert any("authentication" in c for c in context)
        assert any("session" in c for c in context)


class TestContinuationIdValidation:
    """Tests for continuation_id validation (T021)."""

    def test_invalid_continuation_id_creates_new_workflow(self):
        """Invalid continuation_id should create a new workflow."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=2,
            continuation_id="non-existent-id",
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        assert response.continuation_id == "non-existent-id"

    def test_resuming_with_valid_continuation_id(self):
        """Valid continuation_id should resume existing workflow."""
        tool = SecurityAuditTool()
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["first.py"],
            confidence="exploring",
        )
        continuation_id = response1.continuation_id

        response2 = tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["second.py"],
            confidence="low",
        )

        state = WorkflowStateManager().get(continuation_id)
        assert state is not None
        assert len(state.step_history) == 2


class TestResponsePayload:
    """Tests for response payload (T022-T024)."""

    def test_response_contains_required_fields(self):
        """Response should contain all required fields."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        assert hasattr(response, "continuation_id")
        assert hasattr(response, "step_processed")
        assert hasattr(response, "workflow_complete")
        assert hasattr(response, "guidance")

    def test_response_to_dict_format(self):
        """Response.to_dict() should return properly formatted dict."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        response_dict = response.to_dict()
        assert "continuation_id" in response_dict
        assert "step_processed" in response_dict
        assert "workflow_complete" in response_dict

    def test_guidance_contains_next_steps(self):
        """Guidance should contain next_steps with MANDATORY instruction."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        assert response.guidance is not None
        assert response.guidance.confidence_guidance is not None
        assert "MANDATORY" in response.guidance.confidence_guidance

    def test_completion_response_has_summary(self):
        """Completed workflow should have consolidated summary."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["app.py"],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        response = tool.execute(
            step_number=6,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["final.py"],
            confidence="high",
        )
        assert response.workflow_complete is True
        assert response.consolidated_summary is not None


class TestExpertAnalysisConditions:
    """Tests for expert analysis trigger conditions (T025-T027)."""

    def test_no_expert_analysis_when_certain(self, disable_expert_analysis):
        """Expert analysis should NOT be triggered when EXPERT_ANALYSIS_ENABLED=false."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["auth.py"],
            confidence="medium",
            vulnerabilities_found=[
                {
                    "severity": "critical",
                    "category": "authentication",
                    "description": "No password validation",
                    "affected_files": ["auth.py"],
                }
            ],
        )

        response = tool.execute(
            step_number=6,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["final.py"],
            confidence="certain",
        )
        assert response.workflow_complete is True
        assert response.expert_analysis is None

    def test_no_expert_analysis_when_config_disabled(self, disable_expert_analysis):
        """Expert analysis should NOT be triggered when EXPERT_ANALYSIS_ENABLED=false."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["auth.py"],
            confidence="medium",
            vulnerabilities_found=[
                {
                    "severity": "low",
                    "category": "style",
                    "description": "Inconsistent naming",
                    "affected_files": ["auth.py"],
                }
            ],
        )

        response = tool.execute(
            step_number=6,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["final.py"],
            confidence="high",
        )
        assert response.workflow_complete is True
        assert response.expert_analysis is None


class TestWorkflowCompletion:
    """Tests for workflow completion and summary."""

    def test_completion_provides_summary(self):
        """Completing workflow should provide consolidated summary and message."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["app.py"],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        response = tool.execute(
            step_number=6,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["final.py"],
            confidence="high",
        )
        assert response.workflow_complete is True
        assert response.message is not None
        assert "markdown report" in response.message
        assert response.consolidated_summary is not None

    def test_summary_contains_findings(self):
        """Summary should contain vulnerabilities found."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["auth.py"],
            confidence="medium",
            vulnerabilities_found=[
                {
                    "severity": "critical",
                    "category": "SQL Injection",
                    "description": "Direct SQL concatenation",
                    "affected_files": ["auth.py"],
                }
            ],
        )

        response = tool.execute(
            step_number=6,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["final.py"],
            confidence="high",
        )
        assert response.consolidated_summary is not None
        issues = response.consolidated_summary.get("issues_found", [])
        assert len(issues) == 1
        assert issues[0]["category"] == "SQL Injection"
        assert issues[0]["severity"] == "critical"

    def test_summary_in_response_dict(self):
        """Summary should be included in to_dict() output."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        response = tool.execute(
            step_number=6,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=[],
            confidence="high",
        )
        response_dict = response.to_dict()
        assert "consolidated_summary" in response_dict
        assert response_dict["consolidated_summary"] is not None
        assert "message" in response_dict
        assert "markdown report" in response_dict["message"]
