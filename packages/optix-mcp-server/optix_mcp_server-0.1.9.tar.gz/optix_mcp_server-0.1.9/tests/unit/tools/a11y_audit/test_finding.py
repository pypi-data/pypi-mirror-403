"""Unit tests for AccessibilityFinding dataclass."""

import pytest

from tools.a11y_audit.finding import AccessibilityFinding
from tools.a11y_audit.severity import AccessibilitySeverity


def test_finding_creation():
    """Test creating a valid accessibility finding."""
    finding = AccessibilityFinding(
        severity=AccessibilitySeverity.CRITICAL,
        wcag_criterion="2.1.1",
        category="Keyboard",
        description="Button not keyboard accessible",
        affected_files=["src/components/Button.tsx"],
        affected_elements=[".submit-button"],
        remediation="Replace div with button element",
        wcag_level="A",
    )

    assert finding.severity == AccessibilitySeverity.CRITICAL
    assert finding.wcag_criterion == "2.1.1"
    assert finding.category == "Keyboard"
    assert finding.wcag_level == "A"


def test_finding_from_string_severity():
    """Test creating finding with string severity (auto-converts to enum)."""
    finding = AccessibilityFinding(
        severity="high",
        wcag_criterion="1.4.3",
        category="Contrast",
        description="Low contrast text",
        affected_files=["src/styles.css"],
        affected_elements=[".body-text"],
        remediation="Use darker text color",
        wcag_level="AA",
    )

    assert finding.severity == AccessibilitySeverity.HIGH


def test_finding_invalid_wcag_criterion():
    """Test that invalid WCAG criterion format raises error."""
    with pytest.raises(ValueError, match="Invalid WCAG criterion format"):
        AccessibilityFinding(
            severity=AccessibilitySeverity.HIGH,
            wcag_criterion="1.1",  # Invalid: should be X.X.X
            category="ARIA",
            description="Test",
            affected_files=[],
            affected_elements=[],
            remediation="Test",
            wcag_level="A",
        )


def test_finding_invalid_category():
    """Test that invalid category raises error."""
    with pytest.raises(ValueError, match="Invalid category"):
        AccessibilityFinding(
            severity=AccessibilitySeverity.HIGH,
            wcag_criterion="1.1.1",
            category="InvalidCategory",
            description="Test",
            affected_files=[],
            affected_elements=[],
            remediation="Test",
            wcag_level="A",
        )


def test_finding_invalid_wcag_level():
    """Test that invalid WCAG level raises error."""
    with pytest.raises(ValueError, match="Invalid WCAG level"):
        AccessibilityFinding(
            severity=AccessibilitySeverity.HIGH,
            wcag_criterion="1.1.1",
            category="ARIA",
            description="Test",
            affected_files=[],
            affected_elements=[],
            remediation="Test",
            wcag_level="B",  # Invalid: should be A, AA, or AAA
        )


def test_finding_empty_description():
    """Test that empty description raises error."""
    with pytest.raises(ValueError, match="Description cannot be empty"):
        AccessibilityFinding(
            severity=AccessibilitySeverity.HIGH,
            wcag_criterion="1.1.1",
            category="ARIA",
            description="",
            affected_files=[],
            affected_elements=[],
            remediation="Test",
            wcag_level="A",
        )


def test_finding_empty_remediation():
    """Test that empty remediation raises error."""
    with pytest.raises(ValueError, match="Remediation cannot be empty"):
        AccessibilityFinding(
            severity=AccessibilitySeverity.HIGH,
            wcag_criterion="1.1.1",
            category="ARIA",
            description="Test",
            affected_files=[],
            affected_elements=[],
            remediation="",
            wcag_level="A",
        )


def test_finding_to_dict():
    """Test converting finding to dictionary."""
    finding = AccessibilityFinding(
        severity=AccessibilitySeverity.CRITICAL,
        wcag_criterion="2.1.1",
        category="Keyboard",
        description="Button not keyboard accessible",
        affected_files=["src/components/Button.tsx"],
        affected_elements=[".submit-button"],
        remediation="Replace div with button element",
        wcag_level="A",
    )

    data = finding.to_dict()

    assert data["severity"] == "critical"
    assert data["wcag_criterion"] == "2.1.1"
    assert data["category"] == "Keyboard"
    assert data["description"] == "Button not keyboard accessible"
    assert data["affected_files"] == ["src/components/Button.tsx"]
    assert data["affected_elements"] == [".submit-button"]
    assert data["remediation"] == "Replace div with button element"
    assert data["wcag_level"] == "A"


def test_finding_from_dict():
    """Test creating finding from dictionary."""
    data = {
        "severity": "high",
        "wcag_criterion": "1.4.3",
        "category": "Contrast",
        "description": "Low contrast text",
        "affected_files": ["src/styles.css"],
        "affected_elements": [".body-text"],
        "remediation": "Use darker text color",
        "wcag_level": "AA",
    }

    finding = AccessibilityFinding.from_dict(data)

    assert finding.severity == AccessibilitySeverity.HIGH
    assert finding.wcag_criterion == "1.4.3"
    assert finding.category == "Contrast"
    assert finding.wcag_level == "AA"


def test_finding_round_trip():
    """Test that to_dict/from_dict round-trip preserves data."""
    original = AccessibilityFinding(
        severity=AccessibilitySeverity.MEDIUM,
        wcag_criterion="1.3.1",
        category="Semantic",
        description="Missing semantic HTML",
        affected_files=["src/Layout.tsx"],
        affected_elements=["#page-wrapper"],
        remediation="Use semantic elements",
        wcag_level="A",
    )

    data = original.to_dict()
    restored = AccessibilityFinding.from_dict(data)

    assert restored.severity == original.severity
    assert restored.wcag_criterion == original.wcag_criterion
    assert restored.category == original.category
    assert restored.description == original.description
    assert restored.wcag_level == original.wcag_level
