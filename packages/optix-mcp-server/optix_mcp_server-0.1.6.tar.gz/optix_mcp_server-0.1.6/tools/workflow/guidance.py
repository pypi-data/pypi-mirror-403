"""StepGuidance model for workflow step guidance responses."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StepGuidance:
    """Response structure containing required actions and next steps.

    Provides actionable guidance for the next workflow step based on
    the current step number and confidence level.
    """

    required_actions: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    next_step_focus: Optional[str] = None
    confidence_guidance: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert the step guidance to a dictionary.

        Returns:
            Dictionary representation of the guidance
        """
        return {
            "required_actions": self.required_actions,
            "suggestions": self.suggestions,
            "next_step_focus": self.next_step_focus,
            "confidence_guidance": self.confidence_guidance,
        }
