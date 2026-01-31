"""WorkflowResponse data model for workflow step outputs."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FileWriteInstructions:
    """Structured instructions for client to write audit report file.

    Contains the target file path, content, and configuration for how the client
    should handle file creation and conflicts.
    """

    target_path: str
    content: str
    create_directory: bool = True
    overwrite_strategy: str = "overwrite"

    def to_dict(self) -> dict[str, Any]:
        """Convert the file write instructions to a dictionary.

        Returns:
            Dictionary representation of the file write instructions
        """
        return {
            "target_path": self.target_path,
            "content": self.content,
            "create_directory": self.create_directory,
            "overwrite_strategy": self.overwrite_strategy,
        }


@dataclass
class WorkflowResponse:
    """Output from processing a workflow step.

    Contains the continuation ID for resuming the workflow, status information,
    and either guidance for the next step or final analysis results.
    """

    continuation_id: str
    step_processed: int
    workflow_complete: bool
    guidance: Optional[Any] = None
    expert_analysis: Optional[dict[str, Any]] = None
    consolidated_summary: Optional[dict[str, Any]] = None
    report_content: Optional[str] = None
    report_path: Optional[str] = None
    file_write_instructions: Optional[FileWriteInstructions] = None
    message: Optional[str] = None
    cancelled: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert the response to a dictionary.

        Returns:
            Dictionary representation of the response
        """
        result: dict[str, Any] = {
            "continuation_id": self.continuation_id,
            "step_processed": self.step_processed,
            "workflow_complete": self.workflow_complete,
        }

        if self.guidance is not None:
            if hasattr(self.guidance, "to_dict"):
                result["guidance"] = self.guidance.to_dict()
            else:
                result["guidance"] = self.guidance

        if self.expert_analysis is not None:
            result["expert_analysis"] = self.expert_analysis

        if self.consolidated_summary is not None:
            result["consolidated_summary"] = self.consolidated_summary

        if self.report_content is not None:
            result["report_content"] = self.report_content

        if self.report_path is not None:
            result["report_path"] = self.report_path

        if self.file_write_instructions is not None:
            result["file_write_instructions"] = self.file_write_instructions.to_dict()

        if self.message is not None:
            result["message"] = self.message

        if self.cancelled:
            result["cancelled"] = True
            result["status"] = "CANCELLED_BY_USER"

        return result
