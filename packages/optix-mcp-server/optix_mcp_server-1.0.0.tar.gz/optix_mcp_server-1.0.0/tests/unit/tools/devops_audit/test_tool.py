"""Unit tests for DevOpsAuditTool."""

import pytest

from tools.devops_audit import DevOpsAuditTool
from tools.workflow.state import WorkflowStateManager


@pytest.fixture(autouse=True)
def clear_workflow_state():
    """Clear workflow state before each test."""
    WorkflowStateManager().clear_all()
    yield
    WorkflowStateManager().clear_all()


@pytest.fixture
def tool():
    """Create DevOpsAuditTool instance."""
    return DevOpsAuditTool()


class TestDevOpsAuditToolProperties:
    def test_name_is_devops_audit(self, tool):
        assert tool.name == "devops_audit"

    def test_description_mentions_devops(self, tool):
        assert "devops" in tool.description.lower()
        assert "audit" in tool.description.lower()

    def test_total_steps_is_four(self, tool):
        assert tool.total_steps == 4


class TestDevOpsAuditStep1:
    def test_step_1_creates_continuation_id(self, tool):
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["Dockerfile"],
            confidence="exploring",
        )
        assert response.continuation_id is not None
        assert len(response.continuation_id) == 36

    def test_step_1_returns_docker_guidance(self, tool):
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["Dockerfile"],
            confidence="exploring",
        )
        assert response.guidance is not None
        assert response.guidance.next_step_focus == "Docker Infrastructure Audit"
        assert any("USER" in action for action in response.guidance.required_actions)

    def test_step_1_stores_project_root_path(self, tool):
        response = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["Dockerfile"],
            confidence="high",
            project_root_path="/tmp/test-project",
        )
        state = WorkflowStateManager().get(response.continuation_id)
        assert state.project_root_path == "/tmp/test-project"


class TestDevOpsAuditFindingsAccumulation:
    def test_findings_accumulate_across_steps(self, tool):
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["Dockerfile"],
            confidence="high",
            devops_issues_found=[
                {
                    "severity": "critical",
                    "category": "dockerfile",
                    "description": "Running as root",
                    "affected_files": ["Dockerfile"],
                }
            ],
        )

        response2 = tool.execute(
            step_number=2,
            next_step_required=True,
            files_examined=[".github/workflows/ci.yml"],
            confidence="high",
            continuation_id=response1.continuation_id,
            devops_issues_found=[
                {
                    "severity": "high",
                    "category": "cicd",
                    "description": "Unpinned action",
                    "affected_files": [".github/workflows/ci.yml"],
                }
            ],
        )

        state = WorkflowStateManager().get(response1.continuation_id)
        assert len(state.consolidated.issues_found) == 2


class TestDevOpsAuditCompletion:
    def test_step_4_completes_workflow(self, tool):
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["Dockerfile"],
            confidence="high",
        )

        response4 = tool.execute(
            step_number=4,
            next_step_required=False,
            files_examined=[],
            confidence="high",
            continuation_id=response1.continuation_id,
        )

        assert response4.workflow_complete is True

    def test_completion_provides_summary(self, tool):
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["Dockerfile"],
            confidence="high",
            project_root_path="/tmp/test",
            devops_issues_found=[
                {
                    "severity": "critical",
                    "category": "dockerfile",
                    "description": "Test finding",
                    "affected_files": ["Dockerfile"],
                }
            ],
        )

        response4 = tool.execute(
            step_number=4,
            next_step_required=False,
            files_examined=[],
            confidence="high",
            continuation_id=response1.continuation_id,
        )

        assert response4.message is not None
        assert "markdown report" in response4.message
        assert response4.consolidated_summary is not None
        issues = response4.consolidated_summary.get("issues_found", [])
        assert len(issues) == 1
        assert issues[0]["severity"] == "critical"

class TestDevOpsAuditMissingContext:
    def test_missing_context_tracked(self, tool):
        response1 = tool.execute(
            step_number=1,
            next_step_required=True,
            files_examined=["Dockerfile"],
            confidence="high",
        )

        tool.execute(
            step_number=3,
            next_step_required=True,
            files_examined=["package.json"],
            confidence="medium",
            continuation_id=response1.continuation_id,
            missing_context=["package-lock.json"],
        )

        state = WorkflowStateManager().get(response1.continuation_id)
        from tools.devops_audit.finding import ConsolidatedDevOpsFindings

        if isinstance(state.consolidated, ConsolidatedDevOpsFindings):
            assert "package-lock.json" in state.consolidated.missing_lockfiles
