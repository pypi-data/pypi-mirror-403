"""Accessibility audit step domains."""

from enum import Enum


class AccessibilityStepDomain(Enum):
    """Represents the 6 accessibility audit domains aligned with WCAG principles."""

    STRUCTURE = "structure"
    ARIA_LABELS = "aria_labels"
    KEYBOARD_NAV = "keyboard_nav"
    FOCUS_MANAGEMENT = "focus_management"
    COLOR_CONTRAST = "color_contrast"
    SEMANTIC_HTML = "semantic_html"

    @classmethod
    def from_step_number(cls, step: int) -> "AccessibilityStepDomain":
        """Get domain for a given step number (1-6)."""
        mapping = {
            1: cls.STRUCTURE,
            2: cls.ARIA_LABELS,
            3: cls.KEYBOARD_NAV,
            4: cls.FOCUS_MANAGEMENT,
            5: cls.COLOR_CONTRAST,
            6: cls.SEMANTIC_HTML,
        }
        return mapping.get(step, cls.STRUCTURE)

    def description(self) -> str:
        """Return human-readable description of this domain."""
        descriptions = {
            self.STRUCTURE: "Identify UI framework, component structure, and interactive elements",
            self.ARIA_LABELS: "Check ARIA labels, roles, states, and landmark regions",
            self.KEYBOARD_NAV: "Verify keyboard accessibility, tab order, and keyboard traps",
            self.FOCUS_MANAGEMENT: "Validate focus handling, visible indicators, and focus restoration",
            self.COLOR_CONTRAST: "Check text/background contrast ratios and color accessibility",
            self.SEMANTIC_HTML: "Verify semantic HTML5 elements, headings, and WCAG compliance",
        }
        return descriptions[self]
