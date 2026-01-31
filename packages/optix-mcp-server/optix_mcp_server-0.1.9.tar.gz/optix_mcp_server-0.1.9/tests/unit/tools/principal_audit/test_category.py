"""Tests for FindingCategory enum."""

import pytest

from tools.principal_audit.category import FindingCategory


class TestFindingCategory:
    """Test suite for FindingCategory enum."""

    def test_has_complexity_category(self):
        """FindingCategory should have COMPLEXITY value."""
        assert FindingCategory.COMPLEXITY.value == "complexity"

    def test_has_dry_violation_category(self):
        """FindingCategory should have DRY_VIOLATION value."""
        assert FindingCategory.DRY_VIOLATION.value == "dry_violation"

    def test_has_coupling_category(self):
        """FindingCategory should have COUPLING value."""
        assert FindingCategory.COUPLING.value == "coupling"

    def test_has_separation_of_concerns_category(self):
        """FindingCategory should have SEPARATION_OF_CONCERNS value."""
        assert FindingCategory.SEPARATION_OF_CONCERNS.value == "separation_of_concerns"

    def test_has_maintainability_risk_category(self):
        """FindingCategory should have MAINTAINABILITY_RISK value."""
        assert FindingCategory.MAINTAINABILITY_RISK.value == "maintainability_risk"

    def test_all_categories_are_unique(self):
        """All category values should be unique."""
        values = [cat.value for cat in FindingCategory]
        assert len(values) == len(set(values))

    def test_from_string_valid(self):
        """Should convert valid strings to FindingCategory."""
        assert FindingCategory("complexity") == FindingCategory.COMPLEXITY
        assert FindingCategory("dry_violation") == FindingCategory.DRY_VIOLATION
        assert FindingCategory("coupling") == FindingCategory.COUPLING
        assert FindingCategory("separation_of_concerns") == FindingCategory.SEPARATION_OF_CONCERNS
        assert FindingCategory("maintainability_risk") == FindingCategory.MAINTAINABILITY_RISK

    def test_from_string_invalid(self):
        """Should raise ValueError for invalid strings."""
        with pytest.raises(ValueError):
            FindingCategory("invalid_category")
