"""Tests for Severity enum."""

import pytest

from tools.principal_audit.severity import Severity


class TestSeverity:
    """Test suite for Severity enum."""

    def test_has_critical_severity(self):
        """Severity should have CRITICAL value."""
        assert Severity.CRITICAL.value == "critical"

    def test_has_high_severity(self):
        """Severity should have HIGH value."""
        assert Severity.HIGH.value == "high"

    def test_has_medium_severity(self):
        """Severity should have MEDIUM value."""
        assert Severity.MEDIUM.value == "medium"

    def test_has_low_severity(self):
        """Severity should have LOW value."""
        assert Severity.LOW.value == "low"

    def test_has_info_severity(self):
        """Severity should have INFO value."""
        assert Severity.INFO.value == "info"

    def test_numeric_value_critical(self):
        """CRITICAL severity should have highest numeric value (1.0)."""
        assert Severity.CRITICAL.numeric_value() == 1.0

    def test_numeric_value_high(self):
        """HIGH severity should have numeric value 0.75."""
        assert Severity.HIGH.numeric_value() == 0.75

    def test_numeric_value_medium(self):
        """MEDIUM severity should have numeric value 0.5."""
        assert Severity.MEDIUM.numeric_value() == 0.5

    def test_numeric_value_low(self):
        """LOW severity should have numeric value 0.25."""
        assert Severity.LOW.numeric_value() == 0.25

    def test_numeric_value_info(self):
        """INFO severity should have numeric value 0.0."""
        assert Severity.INFO.numeric_value() == 0.0

    def test_numeric_values_are_ordered(self):
        """Numeric values should be ordered from highest to lowest severity."""
        assert Severity.CRITICAL.numeric_value() > Severity.HIGH.numeric_value()
        assert Severity.HIGH.numeric_value() > Severity.MEDIUM.numeric_value()
        assert Severity.MEDIUM.numeric_value() > Severity.LOW.numeric_value()
        assert Severity.LOW.numeric_value() > Severity.INFO.numeric_value()

    def test_from_string_valid(self):
        """Should convert valid strings to Severity."""
        assert Severity("critical") == Severity.CRITICAL
        assert Severity("high") == Severity.HIGH
        assert Severity("medium") == Severity.MEDIUM
        assert Severity("low") == Severity.LOW
        assert Severity("info") == Severity.INFO

    def test_from_string_invalid(self):
        """Should raise ValueError for invalid strings."""
        with pytest.raises(ValueError):
            Severity("invalid_severity")

    def test_comparison_critical_greater_than_high(self):
        """CRITICAL should be greater than HIGH in comparisons."""
        assert Severity.CRITICAL > Severity.HIGH

    def test_comparison_high_greater_than_medium(self):
        """HIGH should be greater than MEDIUM in comparisons."""
        assert Severity.HIGH > Severity.MEDIUM

    def test_comparison_medium_greater_than_low(self):
        """MEDIUM should be greater than LOW in comparisons."""
        assert Severity.MEDIUM > Severity.LOW

    def test_comparison_equality(self):
        """Same severity should be equal."""
        assert Severity.CRITICAL == Severity.CRITICAL
        assert Severity.HIGH == Severity.HIGH

    def test_comparison_less_than(self):
        """LOW should be less than all others."""
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.LOW < Severity.HIGH
        assert Severity.LOW < Severity.CRITICAL

    def test_comparison_info_less_than_all(self):
        """INFO should be less than all other severities."""
        assert Severity.INFO < Severity.LOW
        assert Severity.INFO < Severity.MEDIUM
        assert Severity.INFO < Severity.HIGH
        assert Severity.INFO < Severity.CRITICAL
