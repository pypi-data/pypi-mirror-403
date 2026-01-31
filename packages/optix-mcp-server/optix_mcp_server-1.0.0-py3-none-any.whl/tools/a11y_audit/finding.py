"""Accessibility finding data model."""

import re
from dataclasses import dataclass

from tools.a11y_audit.severity import AccessibilitySeverity


@dataclass
class AccessibilityFinding:
    """Represents a discovered accessibility barrier in the UI."""

    severity: AccessibilitySeverity
    wcag_criterion: str
    category: str
    description: str
    affected_files: list[str]
    affected_elements: list[str]
    remediation: str
    wcag_level: str

    def __post_init__(self) -> None:
        """Validate finding after initialization."""
        if isinstance(self.severity, str):
            self.severity = AccessibilitySeverity(self.severity)

        if not re.match(r"\d+\.\d+\.\d+", self.wcag_criterion):
            raise ValueError(
                f"Invalid WCAG criterion format: {self.wcag_criterion}. "
                "Expected format: X.X.X (e.g., 1.1.1, 2.1.1)"
            )

        valid_categories = ["ARIA", "Keyboard", "Contrast", "Semantic", "Focus"]
        if self.category not in valid_categories:
            raise ValueError(
                f"Invalid category: {self.category}. "
                f"Must be one of: {', '.join(valid_categories)}"
            )

        if self.wcag_level not in ["A", "AA", "AAA"]:
            raise ValueError(
                f"Invalid WCAG level: {self.wcag_level}. Must be A, AA, or AAA"
            )

        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")

        if not self.remediation or not self.remediation.strip():
            raise ValueError("Remediation cannot be empty")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "severity": self.severity.value,
            "wcag_criterion": self.wcag_criterion,
            "category": self.category,
            "description": self.description,
            "affected_files": self.affected_files,
            "affected_elements": self.affected_elements,
            "remediation": self.remediation,
            "wcag_level": self.wcag_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AccessibilityFinding":
        """Create from dictionary."""
        return cls(
            severity=AccessibilitySeverity(data["severity"]),
            wcag_criterion=data["wcag_criterion"],
            category=data["category"],
            description=data["description"],
            affected_files=data.get("affected_files", []),
            affected_elements=data.get("affected_elements", []),
            remediation=data["remediation"],
            wcag_level=data["wcag_level"],
        )
