"""Unit tests for resuming interrupted security audits."""

import pytest

from tools.security_audit.tool import SecurityAuditTool
from tools.workflow.state import WorkflowStateManager


@pytest.fixture(autouse=True)
def clear_workflow_state():
    """Clear workflow state before each test."""
    WorkflowStateManager().clear_all()
    yield
    WorkflowStateManager().clear_all()


class TestResumeWorkflow:
    """Tests for resuming interrupted audits (T055-T057)."""

    def test_resume_preserves_files_examined(self):
        """Resuming should preserve previously examined files."""
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
            files_examined=["auth.py"],
            confidence="low",
        )

        response = tool.execute(
            step_number=3,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=["input.py"],
            confidence="medium",
        )

        state = WorkflowStateManager().get(continuation_id)
        assert state is not None
        all_files = state.consolidated.files_checked
        assert "app.py" in all_files
        assert "main.py" in all_files
        assert "auth.py" in all_files
        assert "input.py" in all_files

    def test_resume_preserves_vulnerabilities(self):
        """Resuming should preserve previously found vulnerabilities."""
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
            next_step_required=True,
            files_examined=["input.py"],
            confidence="medium",
            vulnerabilities_found=[
                {
                    "severity": "critical",
                    "category": "injection",
                    "description": "SQL injection",
                    "affected_files": ["input.py"],
                }
            ],
        )

        state = WorkflowStateManager().get(continuation_id)
        issues = state.consolidated.issues_found
        assert len(issues) == 2
        categories = [i["category"] for i in issues]
        assert "authentication" in categories
        assert "injection" in categories

    def test_resume_preserves_step_history(self):
        """Resuming should preserve step history."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["step1.py"],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["step2.py"],
            confidence="low",
        )

        tool.execute(
            step_number=3,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["step3.py"],
            confidence="medium",
        )

        state = WorkflowStateManager().get(continuation_id)
        assert len(state.step_history) == 3
        assert state.step_history[0].step_number == 1
        assert state.step_history[1].step_number == 2
        assert state.step_history[2].step_number == 3


class TestResumeFromAnyStep:
    """Tests for resuming from any step (T058)."""

    def test_resume_from_step_3(self):
        """Should be able to resume from step 3."""
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
            files_examined=[],
            confidence="low",
        )

        response = tool.execute(
            step_number=3,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=[],
            confidence="medium",
        )

        assert response.step_processed == 3
        assert response.continuation_id == continuation_id

    def test_resume_can_skip_to_completion(self):
        """Should be able to complete from any step."""
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

        assert response.workflow_complete is True


class TestResumeWithContextAccumulation:
    """Tests for context accumulation on resume (T059)."""

    def test_assessments_accumulate_on_resume(self):
        """Security assessments should accumulate when resuming."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
            security_assessments={"reconnaissance": "Web application with REST API"},
        )
        continuation_id = response.continuation_id

        tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=False,
            files_examined=[],
            confidence="medium",
            security_assessments={"auth": "JWT-based authentication"},
        )

        state = WorkflowStateManager().get(continuation_id)
        context = state.consolidated.relevant_context
        assert any("reconnaissance" in c for c in context)
        assert any("auth" in c for c in context)


class TestResumeValidation:
    """Tests for resume validation (T060)."""

    def test_invalid_continuation_id_creates_new_workflow(self):
        """Invalid continuation_id should create new workflow."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=3,
            continuation_id="invalid-uuid-that-does-not-exist",
            next_step_required=True,
            files_examined=[],
            confidence="medium",
        )

        assert response.continuation_id == "invalid-uuid-that-does-not-exist"

    def test_resume_returns_correct_guidance(self):
        """Resuming should return guidance appropriate for the step."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=[],
            confidence="exploring",
        )
        continuation_id = response.continuation_id

        response = tool.execute(
            step_number=2,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=[],
            confidence="low",
        )

        assert response.guidance is not None
        assert len(response.guidance.required_actions) > 0


class TestReportOnResumedCompletion:
    """Tests for summary after resumed workflow completion."""

    def test_summary_includes_all_resumed_findings(self):
        """Summary should include findings from all resumed steps."""
        tool = SecurityAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["app.py"],
            confidence="exploring",
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
                    "category": "Weak Authentication",
                    "description": "No MFA support",
                    "affected_files": ["auth.py"],
                }
            ],
        )

        tool.execute(
            step_number=3,
            continuation_id=continuation_id,
            next_step_required=True,
            files_examined=["input.py"],
            confidence="medium",
            vulnerabilities_found=[
                {
                    "severity": "critical",
                    "category": "SQL Injection",
                    "description": "Direct query concatenation",
                    "affected_files": ["input.py"],
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
        assert len(issues) == 2
        categories = [i["category"] for i in issues]
        assert "Weak Authentication" in categories
        assert "SQL Injection" in categories
        affected_files = [f for i in issues for f in i.get("affected_files", [])]
        assert "auth.py" in affected_files
        assert "input.py" in affected_files
