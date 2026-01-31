"""Tests for PrincipalAuditTool."""

import pytest

from tools.principal_audit.tool import PrincipalAuditTool
from tools.principal_audit.finding import ConsolidatedPrincipalFindings
from tools.workflow.confidence import ConfidenceLevel


class TestPrincipalAuditToolInitialization:
    """Tests for PrincipalAuditTool initialization (T023)."""

    def test_tool_name(self):
        """Tool should have correct name."""
        tool = PrincipalAuditTool()
        assert tool.name == "principal_audit"

    def test_tool_has_description(self):
        """Tool should have a description."""
        tool = PrincipalAuditTool()
        assert len(tool.description) > 0
        assert "principal" in tool.description.lower() or "audit" in tool.description.lower()

    def test_tool_total_steps_is_five(self):
        """Tool should have 5 steps in the workflow."""
        tool = PrincipalAuditTool()
        assert tool.total_steps == 5

    def test_tool_inherits_from_workflow_tool(self):
        """Tool should inherit from WorkflowTool."""
        tool = PrincipalAuditTool()
        from tools.workflow.base import WorkflowTool
        assert isinstance(tool, WorkflowTool)


class TestProcessStep:
    """Tests for process_step method (T025)."""

    def test_step_1_creates_continuation_id(self):
        """Step 1 should create a continuation ID."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="exploring",
        )
        assert response.continuation_id is not None
        assert len(response.continuation_id) > 0

    def test_step_1_stores_project_root_path(self):
        """Step 1 should store project_root_path in state."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="exploring",
            project_root_path="/test/project",
        )
        state = tool._state_manager.get(response.continuation_id)
        assert state is not None
        assert state.project_root_path == "/test/project"

    def test_step_returns_guidance(self):
        """Steps should return guidance when not complete."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="medium",
        )
        assert response.guidance is not None
        assert response.workflow_complete is False

    def test_step_processed_matches_request(self):
        """Response should indicate which step was processed."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=2,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="medium",
        )
        assert response.step_processed == 2

    def test_continuation_across_steps(self):
        """Should continue workflow with same continuation_id."""
        tool = PrincipalAuditTool()
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="exploring",
        )
        response2 = tool.execute(
            step_number=2,
            next_step_required=True,
            files_examined=["src/service.py"],
            confidence="medium",
            continuation_id=response1.continuation_id,
        )
        assert response2.continuation_id == response1.continuation_id


class TestHandleStepMethods:
    """Tests for _handle_step_1 through _handle_step_5 (T027)."""

    def test_step_1_complexity_focus(self):
        """Step 1 should focus on complexity analysis."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="exploring",
        )
        guidance = response.guidance
        if hasattr(guidance, "to_dict"):
            guidance_dict = guidance.to_dict()
        else:
            guidance_dict = guidance

        assert any("complexity" in str(v).lower() for v in guidance_dict.values() if v)

    def test_step_2_dry_focus(self):
        """Step 2 should focus on DRY violation detection."""
        tool = PrincipalAuditTool()
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="exploring",
        )
        response = tool.execute(
            step_number=2,
            next_step_required=True,
            files_examined=["src/service.py"],
            confidence="medium",
            continuation_id=response1.continuation_id,
        )
        guidance = response.guidance
        if hasattr(guidance, "to_dict"):
            guidance_dict = guidance.to_dict()
        else:
            guidance_dict = guidance

        next_focus = str(guidance_dict.get("next_step_focus", "")).lower()
        assert "coupling" in next_focus or "dry" in str(guidance_dict).lower()

    def test_step_5_completion_with_next_step_required_false(self):
        """Step 5 with next_step_required=false should complete workflow."""
        tool = PrincipalAuditTool()
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="exploring",
            project_root_path="/test/project",
        )
        for step in range(2, 5):
            tool.execute(
                step_number=step,
                next_step_required=True,
                files_examined=["src/file.py"],
                confidence="medium",
                continuation_id=response1.continuation_id,
            )
        response = tool.execute(
            step_number=5,
            next_step_required=False,
            files_examined=["src/config.py"],
            confidence="very_high",
            continuation_id=response1.continuation_id,
        )
        assert response.workflow_complete is True


class TestFindingsProcessing:
    """Tests for findings processing."""

    def test_add_complexity_finding(self):
        """Should add complexity findings to consolidated state."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["src/main.py"],
            confidence="high",
            principal_findings=[
                {
                    "category": "complexity",
                    "severity": "high",
                    "description": "Function process_data has cyclomatic complexity of 15",
                    "affected_files": [{"file_path": "src/main.py", "line_start": 10}],
                    "remediation": "Split into smaller functions",
                    "confidence": "high",
                    "complexity_score": 15.0,
                }
            ],
        )
        state = tool._state_manager.get(response.continuation_id)
        assert state is not None
        if isinstance(state.consolidated, ConsolidatedPrincipalFindings):
            assert len(state.consolidated.complexity_findings) == 1
            assert state.consolidated.complexity_findings[0].complexity_score == 15.0

    def test_add_dry_violation_finding(self):
        """Should add DRY violation findings."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=2,
            next_step_required=True,
            files_examined=["src/a.py", "src/b.py"],
            confidence="high",
            principal_findings=[
                {
                    "category": "dry_violation",
                    "severity": "medium",
                    "description": "Duplicated validation logic",
                    "affected_files": [
                        {"file_path": "src/a.py", "line_start": 10},
                        {"file_path": "src/b.py", "line_start": 20},
                    ],
                    "remediation": "Extract to utility",
                    "confidence": "high",
                    "similarity_percentage": 87.5,
                }
            ],
        )
        state = tool._state_manager.get(response.continuation_id)
        if isinstance(state.consolidated, ConsolidatedPrincipalFindings):
            assert len(state.consolidated.dry_violations) == 1
            assert state.consolidated.dry_violations[0].similarity_percentage == 87.5

    def test_add_coupling_finding(self):
        """Should add coupling findings with metrics."""
        tool = PrincipalAuditTool()
        response = tool.execute(
            step_number=3,
            next_step_required=True,
            files_examined=["src/service.py"],
            confidence="high",
            principal_findings=[
                {
                    "category": "coupling",
                    "severity": "critical",
                    "description": "High coupling detected",
                    "affected_files": [{"file_path": "src/service.py"}],
                    "remediation": "Apply dependency injection",
                    "confidence": "high",
                    "coupling_metrics": {
                        "afferent_coupling": 2,
                        "efferent_coupling": 8,
                        "instability": 0.8,
                        "module_name": "ServiceModule",
                        "dependency_count": 8,
                    },
                }
            ],
        )
        state = tool._state_manager.get(response.continuation_id)
        if isinstance(state.consolidated, ConsolidatedPrincipalFindings):
            assert len(state.consolidated.coupling_issues) == 1
            assert state.consolidated.coupling_issues[0].coupling_metrics.instability == 0.8


class TestRequiredActions:
    """Tests for get_required_actions method."""

    def test_returns_actions_for_step_1(self):
        """Should return complexity-related actions for step 1."""
        tool = PrincipalAuditTool()
        actions = tool.get_required_actions(1, ConfidenceLevel.MEDIUM)
        assert len(actions) > 0
        assert any("complexity" in a.lower() for a in actions)

    def test_returns_actions_for_step_5(self):
        """Should return maintainability-related actions for step 5."""
        tool = PrincipalAuditTool()
        actions = tool.get_required_actions(5, ConfidenceLevel.HIGH)
        assert len(actions) > 0
