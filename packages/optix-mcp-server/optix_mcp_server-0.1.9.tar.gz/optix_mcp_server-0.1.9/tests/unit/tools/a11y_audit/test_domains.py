"""Unit tests for AccessibilityStepDomain enum."""

import pytest

from tools.a11y_audit.domains import AccessibilityStepDomain


def test_domain_values():
    """Test that all domains have correct values."""
    assert AccessibilityStepDomain.STRUCTURE.value == "structure"
    assert AccessibilityStepDomain.ARIA_LABELS.value == "aria_labels"
    assert AccessibilityStepDomain.KEYBOARD_NAV.value == "keyboard_nav"
    assert AccessibilityStepDomain.FOCUS_MANAGEMENT.value == "focus_management"
    assert AccessibilityStepDomain.COLOR_CONTRAST.value == "color_contrast"
    assert AccessibilityStepDomain.SEMANTIC_HTML.value == "semantic_html"


def test_from_step_number():
    """Test mapping from step number to domain."""
    assert (
        AccessibilityStepDomain.from_step_number(1)
        == AccessibilityStepDomain.STRUCTURE
    )
    assert (
        AccessibilityStepDomain.from_step_number(2)
        == AccessibilityStepDomain.ARIA_LABELS
    )
    assert (
        AccessibilityStepDomain.from_step_number(3)
        == AccessibilityStepDomain.KEYBOARD_NAV
    )
    assert (
        AccessibilityStepDomain.from_step_number(4)
        == AccessibilityStepDomain.FOCUS_MANAGEMENT
    )
    assert (
        AccessibilityStepDomain.from_step_number(5)
        == AccessibilityStepDomain.COLOR_CONTRAST
    )
    assert (
        AccessibilityStepDomain.from_step_number(6)
        == AccessibilityStepDomain.SEMANTIC_HTML
    )


def test_from_step_number_invalid():
    """Test invalid step numbers default to STRUCTURE."""
    assert (
        AccessibilityStepDomain.from_step_number(0)
        == AccessibilityStepDomain.STRUCTURE
    )
    assert (
        AccessibilityStepDomain.from_step_number(7)
        == AccessibilityStepDomain.STRUCTURE
    )
    assert (
        AccessibilityStepDomain.from_step_number(999)
        == AccessibilityStepDomain.STRUCTURE
    )


def test_domain_descriptions():
    """Test that all domains have descriptions."""
    assert "UI framework" in AccessibilityStepDomain.STRUCTURE.description()
    assert "ARIA labels" in AccessibilityStepDomain.ARIA_LABELS.description()
    assert "keyboard" in AccessibilityStepDomain.KEYBOARD_NAV.description()
    assert "focus" in AccessibilityStepDomain.FOCUS_MANAGEMENT.description()
    assert "contrast" in AccessibilityStepDomain.COLOR_CONTRAST.description()
    assert "semantic" in AccessibilityStepDomain.SEMANTIC_HTML.description()
