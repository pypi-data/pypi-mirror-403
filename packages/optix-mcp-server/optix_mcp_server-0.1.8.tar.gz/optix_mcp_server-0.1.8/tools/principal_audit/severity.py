"""Severity enum for code quality findings."""

from enum import Enum


class Severity(Enum):
    """Severity levels for code quality findings.

    Levels indicate the impact and urgency of addressing a finding:
    - CRITICAL: Immediate attention required, high risk to maintainability
    - HIGH: Significant impact, should be addressed soon
    - MEDIUM: Moderate concern, schedule for refactoring
    - LOW: Minor issue, improvement opportunity
    - INFO: Informational finding, positive pattern or observation
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def numeric_value(self) -> float:
        """Get numeric value for severity comparison and weighted calculations.

        Returns:
            Float value from 0.0 (INFO) to 1.0 (CRITICAL)
        """
        severity_values = {
            Severity.CRITICAL: 1.0,
            Severity.HIGH: 0.75,
            Severity.MEDIUM: 0.5,
            Severity.LOW: 0.25,
            Severity.INFO: 0.0,
        }
        return severity_values[self]

    def __lt__(self, other: "Severity") -> bool:
        """Enable comparison between severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_value() < other.numeric_value()

    def __le__(self, other: "Severity") -> bool:
        """Enable comparison between severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_value() <= other.numeric_value()

    def __gt__(self, other: "Severity") -> bool:
        """Enable comparison between severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_value() > other.numeric_value()

    def __ge__(self, other: "Severity") -> bool:
        """Enable comparison between severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_value() >= other.numeric_value()
