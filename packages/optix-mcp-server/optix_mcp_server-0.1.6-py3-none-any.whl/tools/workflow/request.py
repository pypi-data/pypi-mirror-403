"""WorkflowRequest data model for workflow step requests."""

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.workflow.confidence import ConfidenceLevel


@dataclass
class WorkflowRequest:
    """Data model defining standard parameters for workflow step requests.

    This dataclass captures all the information needed to process a single
    step in a multi-step workflow, including step metadata, findings,
    hypothesis, confidence, and file references.
    """

    step: str
    step_number: int
    total_steps: int
    next_step_required: bool
    findings: str
    confidence: ConfidenceLevel = ConfidenceLevel.EXPLORING
    hypothesis: Optional[str] = None
    files_checked: list[str] = field(default_factory=list)
    relevant_files: list[str] = field(default_factory=list)
    relevant_context: list[str] = field(default_factory=list)
    issues_found: list[dict[str, Any]] = field(default_factory=list)
    continuation_id: Optional[str] = None
    _raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowRequest":
        """Create a WorkflowRequest from a dictionary.

        Args:
            data: Dictionary containing request fields

        Returns:
            WorkflowRequest instance
        """
        confidence = data.get("confidence", "exploring")
        if isinstance(confidence, str):
            confidence = ConfidenceLevel.from_string(confidence)

        files_examined = data.get("files_examined", data.get("files_checked", []))

        request = cls(
            step=data.get("step", f"Step {data.get('step_number', 1)}"),
            step_number=data.get("step_number", 1),
            total_steps=data.get("total_steps", 6),
            next_step_required=data.get("next_step_required", True),
            findings=data.get("findings", ""),
            confidence=confidence,
            hypothesis=data.get("hypothesis"),
            files_checked=files_examined,
            relevant_files=data.get("relevant_files", []),
            relevant_context=data.get("relevant_context", []),
            issues_found=data.get("issues_found", []),
            continuation_id=data.get("continuation_id"),
        )
        request._raw_data = data
        return request

    def to_dict(self) -> dict[str, Any]:
        """Convert the request to a dictionary.

        Returns:
            Dictionary representation of the request
        """
        return {
            "step": self.step,
            "step_number": self.step_number,
            "total_steps": self.total_steps,
            "next_step_required": self.next_step_required,
            "findings": self.findings,
            "confidence": self.confidence.value,
            "hypothesis": self.hypothesis,
            "files_checked": self.files_checked,
            "relevant_files": self.relevant_files,
            "relevant_context": self.relevant_context,
            "issues_found": self.issues_found,
            "continuation_id": self.continuation_id,
        }
