"""Unit tests for WorkflowTool ABC."""

import pytest
from typing import Any

from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.request import WorkflowRequest
from tools.workflow.response import WorkflowResponse
from tools.workflow.state import WorkflowStateManager


class TestWorkflowToolProcessStep:
    """Tests for WorkflowTool.process_step() method - T010."""

    @pytest.fixture(autouse=True)
    def clear_state(self):
        """Clear state manager before each test."""
        manager = WorkflowStateManager()
        manager.clear_all()
        yield
        manager.clear_all()

    def test_process_step_creates_new_workflow_without_continuation_id(self):
        """T010: process_step creates new workflow when no continuation_id."""
        from tools.workflow.base import WorkflowTool

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "Test tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()
        request = WorkflowRequest(
            step="Initial investigation",
            step_number=1,
            total_steps=3,
            next_step_required=True,
            findings="Found something",
        )

        response = tool.process_step(request)

        assert response.continuation_id is not None
        assert response.step_processed == 1
        assert response.workflow_complete is False

    def test_process_step_stores_step_data(self):
        """T010: process_step stores step data in workflow state."""
        from tools.workflow.base import WorkflowTool

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "Test tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()
        request = WorkflowRequest(
            step="Check file A",
            step_number=1,
            total_steps=2,
            next_step_required=True,
            findings="Found issue in file A",
            files_checked=["a.py"],
            relevant_files=["a.py"],
        )

        response = tool.process_step(request)

        manager = WorkflowStateManager()
        state = manager.get(response.continuation_id)
        assert state is not None
        assert len(state.step_history) == 1
        assert state.step_history[0].findings == "Found issue in file A"


class TestWorkflowToolContinuation:
    """Tests for continuation_id handling - T011."""

    @pytest.fixture(autouse=True)
    def clear_state(self):
        """Clear state manager before each test."""
        manager = WorkflowStateManager()
        manager.clear_all()
        yield
        manager.clear_all()

    def test_continuation_id_generated_for_new_workflow(self):
        """T011: New workflow generates UUID continuation_id."""
        from tools.workflow.base import WorkflowTool

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "Test tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()
        request = WorkflowRequest(
            step="Initial step",
            step_number=1,
            total_steps=2,
            next_step_required=True,
            findings="Initial findings",
        )

        response = tool.process_step(request)

        assert len(response.continuation_id) == 36
        assert response.continuation_id.count("-") == 4

    def test_continuation_id_resumes_existing_workflow(self):
        """T011: Existing continuation_id resumes workflow with context."""
        from tools.workflow.base import WorkflowTool

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "Test tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()

        request1 = WorkflowRequest(
            step="Step 1",
            step_number=1,
            total_steps=3,
            next_step_required=True,
            findings="Finding 1",
        )
        response1 = tool.process_step(request1)

        request2 = WorkflowRequest(
            step="Step 2",
            step_number=2,
            total_steps=3,
            next_step_required=True,
            findings="Finding 2",
            continuation_id=response1.continuation_id,
        )
        response2 = tool.process_step(request2)

        assert response2.continuation_id == response1.continuation_id
        assert response2.step_processed == 2

        manager = WorkflowStateManager()
        state = manager.get(response2.continuation_id)
        assert len(state.step_history) == 2

    def test_workflow_completes_when_next_step_not_required(self):
        """T011: Workflow completes when next_step_required=False."""
        from tools.workflow.base import WorkflowTool

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "Test tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()

        request1 = WorkflowRequest(
            step="Step 1",
            step_number=1,
            total_steps=2,
            next_step_required=True,
            findings="Finding 1",
        )
        response1 = tool.process_step(request1)

        request2 = WorkflowRequest(
            step="Final step",
            step_number=2,
            total_steps=2,
            next_step_required=False,
            findings="Final finding",
            continuation_id=response1.continuation_id,
        )
        response2 = tool.process_step(request2)

        assert response2.workflow_complete is True


@pytest.fixture
def enable_expert_analysis(monkeypatch):
    """Enable expert analysis for tests."""
    monkeypatch.setenv("EXPERT_ANALYSIS_ENABLED", "true")
    monkeypatch.setenv("OPTIX_LLM_PROVIDER", "openai")
    yield


class TestExpertAnalysisTrigger:
    """Tests for expert analysis triggering - controlled by EXPERT_ANALYSIS_ENABLED config."""

    @pytest.fixture(autouse=True)
    def clear_state(self):
        """Clear state manager before each test."""
        manager = WorkflowStateManager()
        manager.clear_all()
        yield
        manager.clear_all()

    def test_prepare_expert_analysis_context_returns_context(self):
        """prepare_expert_analysis_context() formats context for API."""
        from tools.workflow.base import WorkflowTool
        from tools.workflow.findings import ConsolidatedFindings

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "Test tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {
                    "files": list(consolidated.relevant_files),
                    "finding_count": len(consolidated.findings),
                }

        tool = TestTool()

        consolidated = ConsolidatedFindings()
        consolidated.relevant_files.update(["a.py", "b.py"])
        consolidated.findings.extend(["Finding 1", "Finding 2"])

        context = tool.prepare_expert_analysis_context(consolidated)

        assert context is not None
        assert "files" in context
        assert set(context["files"]) == {"a.py", "b.py"}
        assert context["finding_count"] == 2

    def test_completion_includes_consolidated_summary(self):
        """T055: Completion response includes consolidated_summary."""
        from tools.workflow.base import WorkflowTool

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "Test tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()

        request1 = WorkflowRequest(
            step="Step 1",
            step_number=1,
            total_steps=2,
            next_step_required=True,
            findings="Finding 1",
            files_checked=["a.py"],
            relevant_files=["a.py"],
        )
        response1 = tool.process_step(request1)

        request2 = WorkflowRequest(
            step="Final step",
            step_number=2,
            total_steps=2,
            next_step_required=False,
            findings="Finding 2",
            files_checked=["b.py"],
            continuation_id=response1.continuation_id,
        )
        response2 = tool.process_step(request2)

        assert response2.consolidated_summary is not None
        assert "files_checked" in response2.consolidated_summary
        assert "findings" in response2.consolidated_summary
