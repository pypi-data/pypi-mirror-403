"""WorkflowState and StepHistory data models for workflow session management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

from tools.workflow.confidence import ConfidenceLevel

if TYPE_CHECKING:
    from tools.workflow.findings import ConsolidatedFindings


@dataclass
class StepHistory:
    """Record of a single processed step within a workflow.

    Captures the state of the investigation at a specific step,
    including findings, hypothesis, and confidence at that point.
    """

    step_number: int
    step_content: str
    findings: str
    confidence: ConfidenceLevel
    hypothesis: Optional[str] = None
    files_checked: list[str] = field(default_factory=list)
    relevant_files: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert the step history to a dictionary.

        Returns:
            Dictionary representation of the step history
        """
        return {
            "step_number": self.step_number,
            "step_content": self.step_content,
            "findings": self.findings,
            "confidence": self.confidence.value,
            "hypothesis": self.hypothesis,
            "files_checked": self.files_checked,
            "relevant_files": self.relevant_files,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class WorkflowState:
    """In-memory storage for a single workflow session.

    Contains all accumulated data for a workflow keyed by continuation_id.
    """

    continuation_id: str
    tool_name: str
    step_history: list[StepHistory] = field(default_factory=list)
    consolidated: Any = None
    project_root_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_finished: bool = False
    is_cancelled: bool = False

    def add_step(self, step: StepHistory) -> None:
        """Add a step to the workflow history.

        Updates existing step if step_number already exists (handles retries).

        Args:
            step: The step history to add
        """
        existing_index = None
        for i, existing_step in enumerate(self.step_history):
            if existing_step.step_number == step.step_number:
                existing_index = i
                break

        if existing_index is not None:
            self.step_history[existing_index] = step
        else:
            self.step_history.append(step)

        self.updated_at = datetime.now()

        if self.consolidated is not None and existing_index is None:
            self.consolidated.add_step(step)

    def is_complete(self) -> bool:
        """Check if the workflow is complete.

        Returns:
            True if the workflow has no pending steps
        """
        return len(self.step_history) > 0

    def get_latest_confidence(self) -> ConfidenceLevel:
        """Get the confidence level from the most recent step.

        Returns:
            The confidence level from the last step, or EXPLORING if no steps
        """
        if not self.step_history:
            return ConfidenceLevel.EXPLORING
        return self.step_history[-1].confidence

    def to_dict(self) -> dict[str, Any]:
        """Convert the workflow state to a dictionary."""
        consolidated_dict = None
        if self.consolidated and hasattr(self.consolidated, "to_dict"):
            consolidated_dict = self.consolidated.to_dict()

        return {
            "continuation_id": self.continuation_id,
            "tool_name": self.tool_name,
            "step_history": [s.to_dict() for s in self.step_history],
            "consolidated": consolidated_dict,
            "project_root_path": self.project_root_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_finished": self.is_finished,
            "is_cancelled": self.is_cancelled,
        }


class WorkflowStateManager:
    """Singleton manager for workflow state storage.

    Manages in-memory storage of workflow states keyed by continuation_id.
    """

    _instance: Optional["WorkflowStateManager"] = None
    _workflows: dict[str, WorkflowState]

    def __new__(cls) -> "WorkflowStateManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._workflows = {}
        return cls._instance

    def get_or_create(
        self, continuation_id: Optional[str], tool_name: str
    ) -> tuple[WorkflowState, bool]:
        """Get an existing workflow or create a new one.

        Args:
            continuation_id: Optional ID of existing workflow to resume
            tool_name: Name of the workflow tool

        Returns:
            Tuple of (WorkflowState, is_new) where is_new indicates if created
        """
        if continuation_id and continuation_id in self._workflows:
            return self._workflows[continuation_id], False

        from tools.workflow.findings import ConsolidatedFindings

        new_id = str(uuid4()) if not continuation_id else continuation_id
        state = WorkflowState(
            continuation_id=new_id,
            tool_name=tool_name,
            consolidated=ConsolidatedFindings(),
        )
        self._workflows[new_id] = state
        return state, True

    def get(self, continuation_id: str) -> Optional[WorkflowState]:
        """Get an existing workflow state.

        Args:
            continuation_id: ID of the workflow to retrieve

        Returns:
            WorkflowState if found, None otherwise
        """
        return self._workflows.get(continuation_id)

    def save(self, state: WorkflowState) -> None:
        """Save a workflow state.

        Args:
            state: The workflow state to save
        """
        self._workflows[state.continuation_id] = state

    def delete(self, continuation_id: str) -> bool:
        """Delete a workflow state.

        Args:
            continuation_id: ID of the workflow to delete

        Returns:
            True if deleted, False if not found
        """
        if continuation_id in self._workflows:
            del self._workflows[continuation_id]
            return True
        return False

    def cancel(self, continuation_id: str) -> bool:
        """Cancel a workflow.

        Args:
            continuation_id: ID of the workflow to cancel

        Returns:
            True if cancelled, False if not found
        """
        if continuation_id in self._workflows:
            self._workflows[continuation_id].is_cancelled = True
            self._workflows[continuation_id].updated_at = datetime.now()
            return True
        return False

    def clear_all(self) -> None:
        """Clear all workflow states. Used for testing."""
        self._workflows.clear()

    def cleanup_expired(self, ttl_seconds: int) -> int:
        """Remove expired workflow states.

        Args:
            ttl_seconds: Time-to-live in seconds

        Returns:
            Number of states removed
        """
        now = datetime.now()
        expired = [
            cid
            for cid, state in self._workflows.items()
            if (now - state.updated_at).total_seconds() > ttl_seconds
        ]
        for cid in expired:
            del self._workflows[cid]
        return len(expired)
