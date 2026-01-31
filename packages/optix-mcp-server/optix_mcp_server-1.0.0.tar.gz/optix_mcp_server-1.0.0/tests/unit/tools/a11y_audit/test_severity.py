"""Unit tests for AccessibilitySeverity enum."""

import pytest

from tools.a11y_audit.severity import AccessibilitySeverity


def test_severity_values():
    """Test that all severity levels have correct values."""
    assert AccessibilitySeverity.CRITICAL.value == "critical"
    assert AccessibilitySeverity.HIGH.value == "high"
    assert AccessibilitySeverity.MEDIUM.value == "medium"
    assert AccessibilitySeverity.LOW.value == "low"
    assert AccessibilitySeverity.INFO.value == "info"


def test_user_impact():
    """Test user impact descriptions."""
    assert (
        AccessibilitySeverity.CRITICAL.user_impact()
        == "Prevents users from accessing core functionality"
    )
    assert (
        AccessibilitySeverity.HIGH.user_impact()
        == "Creates significant barriers to access"
    )
    assert AccessibilitySeverity.MEDIUM.user_impact() == "Causes moderate difficulty"
    assert AccessibilitySeverity.LOW.user_impact() == "Minor usability concern"
    assert AccessibilitySeverity.INFO.user_impact() == "Improvement opportunity"


def test_severity_ordering():
    """Test severity comparison (CRITICAL > HIGH > MEDIUM > LOW > INFO)."""
    assert AccessibilitySeverity.CRITICAL < AccessibilitySeverity.HIGH
    assert AccessibilitySeverity.HIGH < AccessibilitySeverity.MEDIUM
    assert AccessibilitySeverity.MEDIUM < AccessibilitySeverity.LOW
    assert AccessibilitySeverity.LOW < AccessibilitySeverity.INFO


def test_severity_sorting():
    """Test that severities can be sorted correctly."""
    unsorted = [
        AccessibilitySeverity.INFO,
        AccessibilitySeverity.CRITICAL,
        AccessibilitySeverity.MEDIUM,
        AccessibilitySeverity.HIGH,
        AccessibilitySeverity.LOW,
    ]
    sorted_severities = sorted(unsorted)
    expected = [
        AccessibilitySeverity.CRITICAL,
        AccessibilitySeverity.HIGH,
        AccessibilitySeverity.MEDIUM,
        AccessibilitySeverity.LOW,
        AccessibilitySeverity.INFO,
    ]
    assert sorted_severities == expected
