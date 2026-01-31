"""Severity enum for vulnerability classification."""

from enum import Enum


class Severity(Enum):
    """Vulnerability severity classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum.

        Args:
            value: String representation of severity

        Returns:
            Corresponding Severity enum value

        Raises:
            ValueError: If string doesn't match any valid severity
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = [s.value for s in cls]
            raise ValueError(
                f"Invalid severity: '{value}'. Must be one of: {', '.join(valid_values)}"
            )

    def __lt__(self, other: "Severity") -> bool:
        """Enable comparison - CRITICAL > HIGH > MEDIUM > LOW > INFO."""
        order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(self) < order.index(other)

    def __le__(self, other: "Severity") -> bool:
        """Enable comparison."""
        return self == other or self < other
