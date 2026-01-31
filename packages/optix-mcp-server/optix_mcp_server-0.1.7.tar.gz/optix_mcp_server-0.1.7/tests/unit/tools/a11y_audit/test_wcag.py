"""Unit tests for WCAG criterion mappings."""

import pytest

from tools.a11y_audit.wcag import (
    WCAG_CRITERIA,
    get_criteria_by_level,
    get_criterion,
)


def test_wcag_criteria_structure():
    """Test that WCAG_CRITERIA has expected structure."""
    assert isinstance(WCAG_CRITERIA, dict)
    assert len(WCAG_CRITERIA) > 0

    for number, criterion in WCAG_CRITERIA.items():
        assert "number" in criterion
        assert "name" in criterion
        assert "level" in criterion
        assert "description" in criterion
        assert criterion["number"] == number
        assert criterion["level"] in ["A", "AA", "AAA"]


def test_specific_criteria():
    """Test specific WCAG criteria are present."""
    assert "1.1.1" in WCAG_CRITERIA
    assert WCAG_CRITERIA["1.1.1"]["name"] == "Non-text Content"
    assert WCAG_CRITERIA["1.1.1"]["level"] == "A"

    assert "1.4.3" in WCAG_CRITERIA
    assert WCAG_CRITERIA["1.4.3"]["name"] == "Contrast (Minimum)"
    assert WCAG_CRITERIA["1.4.3"]["level"] == "AA"

    assert "2.1.1" in WCAG_CRITERIA
    assert WCAG_CRITERIA["2.1.1"]["name"] == "Keyboard"
    assert WCAG_CRITERIA["2.1.1"]["level"] == "A"

    assert "4.1.2" in WCAG_CRITERIA
    assert WCAG_CRITERIA["4.1.2"]["name"] == "Name, Role, Value"
    assert WCAG_CRITERIA["4.1.2"]["level"] == "A"


def test_get_criterion():
    """Test get_criterion function."""
    criterion = get_criterion("1.1.1")
    assert criterion is not None
    assert criterion["name"] == "Non-text Content"

    assert get_criterion("999.999.999") is None


def test_get_criteria_by_level():
    """Test get_criteria_by_level function."""
    level_a = get_criteria_by_level("A")
    assert len(level_a) > 0
    assert all(c["level"] == "A" for c in level_a)

    level_aa = get_criteria_by_level("AA")
    assert len(level_aa) > 0
    assert all(c["level"] == "AA" for c in level_aa)

    level_aaa = get_criteria_by_level("AAA")
    assert isinstance(level_aaa, list)


def test_common_criteria_present():
    """Test that common WCAG criteria used in audits are present."""
    common_criteria = [
        "1.1.1",  # Non-text Content
        "1.3.1",  # Info and Relationships
        "1.4.3",  # Contrast (Minimum)
        "2.1.1",  # Keyboard
        "2.4.3",  # Focus Order
        "2.4.7",  # Focus Visible
        "4.1.2",  # Name, Role, Value
    ]

    for number in common_criteria:
        assert number in WCAG_CRITERIA, f"Missing common criterion: {number}"
