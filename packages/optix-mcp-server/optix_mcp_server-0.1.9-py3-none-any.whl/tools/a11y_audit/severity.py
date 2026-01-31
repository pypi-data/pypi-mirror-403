"""Accessibility severity classification."""

from enum import Enum


class AccessibilitySeverity(Enum):
    """Classification of accessibility barrier impact on users."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def user_impact(self) -> str:
        """Return user impact description for this severity level."""
        impacts = {
            AccessibilitySeverity.CRITICAL: "Prevents users from accessing core functionality",
            AccessibilitySeverity.HIGH: "Creates significant barriers to access",
            AccessibilitySeverity.MEDIUM: "Causes moderate difficulty",
            AccessibilitySeverity.LOW: "Minor usability concern",
            AccessibilitySeverity.INFO: "Improvement opportunity",
        }
        return impacts[self]

    def __lt__(self, other: "AccessibilitySeverity") -> bool:
        """Enable sorting by severity (CRITICAL > HIGH > MEDIUM > LOW > INFO)."""
        if not isinstance(other, AccessibilitySeverity):
            return NotImplemented
        order = [
            AccessibilitySeverity.CRITICAL,
            AccessibilitySeverity.HIGH,
            AccessibilitySeverity.MEDIUM,
            AccessibilitySeverity.LOW,
            AccessibilitySeverity.INFO,
        ]
        return order.index(self) < order.index(other)
