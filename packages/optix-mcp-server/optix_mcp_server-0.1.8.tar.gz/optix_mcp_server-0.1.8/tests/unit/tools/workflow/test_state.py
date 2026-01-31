"""Unit tests for WorkflowState and WorkflowStateManager."""

import pytest

from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.state import StepHistory, WorkflowState, WorkflowStateManager


class TestWorkflowStateManager:
    """Tests for WorkflowStateManager singleton."""

    @pytest.fixture(autouse=True)
    def clear_state(self):
        """Clear state manager before each test."""
        manager = WorkflowStateManager()
        manager.clear_all()
        yield
        manager.clear_all()

    def test_get_or_create_generates_new_id_when_none_provided(self):
        """T009: get_or_create generates UUID for new workflows."""
        manager = WorkflowStateManager()
        state, is_new = manager.get_or_create(None, "test_tool")

        assert is_new is True
        assert state.continuation_id is not None
        assert len(state.continuation_id) == 36
        assert state.tool_name == "test_tool"

    def test_get_or_create_returns_existing_state_with_id(self):
        """T009: get_or_create returns existing state when ID provided."""
        manager = WorkflowStateManager()
        state1, _ = manager.get_or_create(None, "test_tool")
        state2, is_new = manager.get_or_create(state1.continuation_id, "test_tool")

        assert is_new is False
        assert state2.continuation_id == state1.continuation_id

    def test_get_returns_none_for_nonexistent_id(self):
        """T009: get returns None for unknown continuation_id."""
        manager = WorkflowStateManager()
        state = manager.get("nonexistent-id")

        assert state is None

    def test_save_persists_state(self):
        """T009: save persists workflow state."""
        manager = WorkflowStateManager()
        state, _ = manager.get_or_create(None, "test_tool")

        step = StepHistory(
            step_number=1,
            step_content="Test step",
            findings="Found something",
            confidence=ConfidenceLevel.EXPLORING,
        )
        state.add_step(step)
        manager.save(state)

        retrieved = manager.get(state.continuation_id)
        assert retrieved is not None
        assert len(retrieved.step_history) == 1

    def test_delete_removes_state(self):
        """T009: delete removes workflow state."""
        manager = WorkflowStateManager()
        state, _ = manager.get_or_create(None, "test_tool")
        continuation_id = state.continuation_id

        result = manager.delete(continuation_id)
        assert result is True

        state = manager.get(continuation_id)
        assert state is None

    def test_delete_returns_false_for_nonexistent(self):
        """T009: delete returns False for unknown ID."""
        manager = WorkflowStateManager()
        result = manager.delete("nonexistent-id")
        assert result is False

    def test_workflow_state_manager_persistence_of_project_root_path(self):
        """T010: WorkflowStateManager persists project_root_path across get/save operations."""
        manager = WorkflowStateManager()

        state, created = manager.get_or_create(
            continuation_id="test-persist-123", tool_name="security_audit"
        )
        assert created is True
        assert state.project_root_path is None

        state.project_root_path = "/path/to/project"
        manager.save(state)

        retrieved_state = manager.get("test-persist-123")
        assert retrieved_state is not None
        assert retrieved_state.project_root_path == "/path/to/project"
        assert retrieved_state.continuation_id == "test-persist-123"


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_workflow_state_instantiation_with_project_root_path(self):
        """T008: WorkflowState can be created with project_root_path."""
        state = WorkflowState(
            continuation_id="test-123",
            tool_name="security_audit",
            project_root_path="/Users/dev/test-project",
        )
        assert state.project_root_path == "/Users/dev/test-project"
        assert state.continuation_id == "test-123"
        assert state.tool_name == "security_audit"

    def test_workflow_state_default_project_root_path_none(self):
        """T009: WorkflowState defaults project_root_path to None."""
        state = WorkflowState(
            continuation_id="test-456",
            tool_name="security_audit",
        )
        assert state.project_root_path is None
        assert state.continuation_id == "test-456"

    def test_add_step_appends_to_history(self):
        """WorkflowState.add_step appends steps to history."""
        state = WorkflowState(
            continuation_id="test-id",
            tool_name="test_tool",
        )
        step = StepHistory(
            step_number=1,
            step_content="Test step",
            findings="Found something",
            confidence=ConfidenceLevel.EXPLORING,
        )

        state.add_step(step)

        assert len(state.step_history) == 1
        assert state.step_history[0].step_number == 1

    def test_get_latest_confidence_returns_last_step_confidence(self):
        """WorkflowState.get_latest_confidence returns confidence from last step."""
        state = WorkflowState(
            continuation_id="test-id",
            tool_name="test_tool",
        )
        state.add_step(StepHistory(
            step_number=1,
            step_content="Step 1",
            findings="Initial",
            confidence=ConfidenceLevel.EXPLORING,
        ))
        state.add_step(StepHistory(
            step_number=2,
            step_content="Step 2",
            findings="More findings",
            confidence=ConfidenceLevel.HIGH,
        ))

        assert state.get_latest_confidence() == ConfidenceLevel.HIGH

    def test_get_latest_confidence_returns_exploring_when_empty(self):
        """WorkflowState.get_latest_confidence returns EXPLORING when no steps."""
        state = WorkflowState(
            continuation_id="test-id",
            tool_name="test_tool",
        )

        assert state.get_latest_confidence() == ConfidenceLevel.EXPLORING


class TestStepHistory:
    """Tests for StepHistory dataclass."""

    def test_step_history_creation(self):
        """StepHistory can be created with required fields."""
        step = StepHistory(
            step_number=1,
            step_content="Test step content",
            findings="Test findings",
            confidence=ConfidenceLevel.MEDIUM,
        )

        assert step.step_number == 1
        assert step.step_content == "Test step content"
        assert step.findings == "Test findings"
        assert step.confidence == ConfidenceLevel.MEDIUM
        assert step.hypothesis is None
        assert step.files_checked == []
        assert step.relevant_files == []

    def test_step_history_to_dict(self):
        """StepHistory.to_dict returns dictionary representation."""
        step = StepHistory(
            step_number=2,
            step_content="Analysis",
            findings="Found bug",
            confidence=ConfidenceLevel.HIGH,
            hypothesis="Memory leak",
            files_checked=["a.py", "b.py"],
            relevant_files=["a.py"],
        )

        result = step.to_dict()

        assert result["step_number"] == 2
        assert result["confidence"] == "high"
        assert result["hypothesis"] == "Memory leak"
        assert result["files_checked"] == ["a.py", "b.py"]
