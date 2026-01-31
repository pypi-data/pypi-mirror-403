"""WCAG 2.1/2.2 criterion mappings."""

from typing import TypedDict


class WCAGCriterion(TypedDict):
    """WCAG success criterion data."""

    number: str
    name: str
    level: str
    description: str


WCAG_CRITERIA: dict[str, WCAGCriterion] = {
    "1.1.1": {
        "number": "1.1.1",
        "name": "Non-text Content",
        "level": "A",
        "description": "All non-text content has text alternative",
    },
    "1.3.1": {
        "number": "1.3.1",
        "name": "Info and Relationships",
        "level": "A",
        "description": "Information and relationships can be programmatically determined",
    },
    "1.4.1": {
        "number": "1.4.1",
        "name": "Use of Color",
        "level": "A",
        "description": "Color is not the only visual means of conveying information",
    },
    "1.4.3": {
        "number": "1.4.3",
        "name": "Contrast (Minimum)",
        "level": "AA",
        "description": "Text has contrast ratio of at least 4.5:1",
    },
    "1.4.11": {
        "number": "1.4.11",
        "name": "Non-text Contrast",
        "level": "AA",
        "description": "UI components have contrast ratio of at least 3:1",
    },
    "2.1.1": {
        "number": "2.1.1",
        "name": "Keyboard",
        "level": "A",
        "description": "All functionality available from keyboard",
    },
    "2.1.2": {
        "number": "2.1.2",
        "name": "No Keyboard Trap",
        "level": "A",
        "description": "Keyboard focus can be moved away from component",
    },
    "2.4.1": {
        "number": "2.4.1",
        "name": "Bypass Blocks",
        "level": "A",
        "description": "Mechanism available to bypass blocks of repeated content",
    },
    "2.4.3": {
        "number": "2.4.3",
        "name": "Focus Order",
        "level": "A",
        "description": "Focusable components receive focus in logical order",
    },
    "2.4.6": {
        "number": "2.4.6",
        "name": "Headings and Labels",
        "level": "AA",
        "description": "Headings and labels describe topic or purpose",
    },
    "2.4.7": {
        "number": "2.4.7",
        "name": "Focus Visible",
        "level": "AA",
        "description": "Keyboard focus indicator is visible",
    },
    "3.1.1": {
        "number": "3.1.1",
        "name": "Language of Page",
        "level": "A",
        "description": "Default human language of page can be programmatically determined",
    },
    "3.2.1": {
        "number": "3.2.1",
        "name": "On Focus",
        "level": "A",
        "description": "Focus does not trigger unexpected context change",
    },
    "4.1.2": {
        "number": "4.1.2",
        "name": "Name, Role, Value",
        "level": "A",
        "description": "UI components have accessible name and role",
    },
}


def get_criterion(number: str) -> WCAGCriterion | None:
    """Get WCAG criterion by number."""
    return WCAG_CRITERIA.get(number)


def get_criteria_by_level(level: str) -> list[WCAGCriterion]:
    """Get all WCAG criteria for a given level (A, AA, AAA)."""
    return [c for c in WCAG_CRITERIA.values() if c["level"] == level]
