"""Step guidance generation for Principal Engineer Audit Tool."""

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.workflow.confidence import ConfidenceLevel

TOTAL_STEPS = 5

STEP_DEFINITIONS = {
    1: {
        "name": "Complexity Analysis",
        "focus_area": "Cyclomatic Complexity Analysis",
        "next_step": "DRY Violation Detection",
        "required_actions": [
            "Analyze source files for cyclomatic complexity",
            "Identify functions exceeding baseline threshold (>10)",
            "Flag high-risk functions (complexity >20)",
            "Document affected functions with line numbers",
        ],
        "focus_areas": [
            "McCabe cyclomatic complexity calculation",
            "Control flow analysis (if/while/for/switch)",
            "Nested conditional detection",
            "Function length analysis",
        ],
    },
    2: {
        "name": "DRY Violation Detection",
        "focus_area": "Code Duplication Analysis",
        "next_step": "Coupling Analysis",
        "required_actions": [
            "Detect syntactic code duplication using token matching",
            "Identify semantic duplicates via AST comparison",
            "Flag code blocks with >80% similarity",
            "Document duplicate locations with file paths and lines",
        ],
        "focus_areas": [
            "Token sequence hashing for exact duplicates",
            "AST structural similarity comparison",
            "Cross-file duplication detection",
            "Similarity percentage calculation",
        ],
    },
    3: {
        "name": "Coupling Analysis",
        "focus_area": "Architectural Coupling Assessment",
        "next_step": "Separation of Concerns",
        "required_actions": [
            "Build module dependency graph from imports",
            "Calculate afferent/efferent coupling metrics",
            "Detect circular dependencies using DFS",
            "Identify modules with >5 dependencies",
        ],
        "focus_areas": [
            "Dependency graph construction",
            "Instability metric calculation (I = Ce / (Ca + Ce))",
            "Circular dependency detection",
            "God object identification (>10 methods or >500 lines)",
        ],
    },
    4: {
        "name": "Separation of Concerns",
        "focus_area": "Separation of Concerns Assessment",
        "next_step": "Maintainability Assessment",
        "required_actions": [
            "Identify mixed responsibilities in modules",
            "Detect SRP violations (business + presentation + data)",
            "Analyze layer boundary violations",
            "Document responsibility mixing patterns",
        ],
        "focus_areas": [
            "Layer boundary analysis",
            "Business logic location verification",
            "Presentation concern isolation",
            "Data access pattern assessment",
        ],
    },
    5: {
        "name": "Maintainability Assessment",
        "focus_area": "Maintainability Risk Indicators",
        "next_step": None,
        "required_actions": [
            "Detect excessive file length (>500/1000 lines)",
            "Identify deep nesting (>4 levels)",
            "Flag long parameter lists (>5 parameters)",
            "Find magic numbers and hardcoded constants",
        ],
        "focus_areas": [
            "File length analysis",
            "Nesting depth calculation",
            "Parameter count validation",
            "Constant extraction opportunities",
        ],
    },
}

CONFIDENCE_GUIDANCE = {
    ConfidenceLevel.EXPLORING: "Identify files and patterns requiring deeper analysis",
    ConfidenceLevel.LOW: "Gather more evidence to support initial findings",
    ConfidenceLevel.MEDIUM: "Validate findings with additional code examination",
    ConfidenceLevel.HIGH: "Verify findings and check for edge cases",
    ConfidenceLevel.VERY_HIGH: "Document findings and prepare recommendations",
    ConfidenceLevel.ALMOST_CERTAIN: "Final verification before completing step",
    ConfidenceLevel.CERTAIN: "Ready to proceed to next step",
}


@dataclass
class PrincipalAuditStepGuidance:
    """Guidance for a specific workflow step.

    Attributes:
        step_number: Current step (1-5)
        focus_area: Primary focus of this step
        required_actions: Actions required to complete the step
        focus_areas: Specific areas to analyze
        next_step_focus: Focus of the next step (None for step 5)
        confidence_guidance: Guidance for improving confidence
        missing_context_hints: Hints for missing context files
    """

    step_number: int
    focus_area: str
    required_actions: list[str]
    focus_areas: list[str]
    next_step_focus: Optional[str]
    confidence_guidance: str
    missing_context_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "step_number": self.step_number,
            "focus_area": self.focus_area,
            "required_actions": self.required_actions,
            "focus_areas": self.focus_areas,
            "next_step_focus": self.next_step_focus,
            "confidence_guidance": self.confidence_guidance,
            "missing_context_hints": self.missing_context_hints,
        }


def get_step_guidance(
    step_number: int,
    confidence: ConfidenceLevel,
    missing_context: Optional[list[str]] = None,
) -> PrincipalAuditStepGuidance:
    """Get guidance for a specific workflow step.

    Args:
        step_number: Current step (1-5)
        confidence: Client's current confidence level
        missing_context: Optional list of missing context files

    Returns:
        PrincipalAuditStepGuidance with step-specific guidance

    Raises:
        ValueError: If step_number is not 1-5
    """
    if step_number < 1 or step_number > TOTAL_STEPS:
        raise ValueError(f"Invalid step number: {step_number}. Must be 1-{TOTAL_STEPS}.")

    step_def = STEP_DEFINITIONS[step_number]

    missing_hints = []
    if missing_context:
        missing_hints = [f"Consider providing: {ctx}" for ctx in missing_context]

    return PrincipalAuditStepGuidance(
        step_number=step_number,
        focus_area=step_def["focus_area"],
        required_actions=step_def["required_actions"].copy(),
        focus_areas=step_def["focus_areas"].copy(),
        next_step_focus=step_def["next_step"],
        confidence_guidance=CONFIDENCE_GUIDANCE.get(confidence, "Continue analysis"),
        missing_context_hints=missing_hints,
    )
