"""Confidence level enumeration for workflow progress tracking."""

from enum import Enum


class ConfidenceLevel(Enum):
    """Enumeration of confidence levels for workflow progress tracking.

    These levels indicate how confident the investigation is in its current
    hypothesis and findings. Higher confidence typically means more focused
    guidance toward verification rather than exploration.
    """

    EXPLORING = "exploring"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    ALMOST_CERTAIN = "almost_certain"
    CERTAIN = "certain"

    @classmethod
    def from_string(cls, value: str) -> "ConfidenceLevel":
        """Convert a string to a ConfidenceLevel enum value.

        Args:
            value: String representation of confidence level

        Returns:
            Corresponding ConfidenceLevel enum value

        Raises:
            ValueError: If the string doesn't match any valid confidence level
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = [level.value for level in cls]
            raise ValueError(
                f"Invalid confidence level: '{value}'. "
                f"Must be one of: {', '.join(valid_values)}"
            )

    def __lt__(self, other: "ConfidenceLevel") -> bool:
        """Enable comparison between confidence levels."""
        order = list(ConfidenceLevel)
        return order.index(self) < order.index(other)

    def __le__(self, other: "ConfidenceLevel") -> bool:
        """Enable comparison between confidence levels."""
        return self == other or self < other
