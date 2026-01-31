"""Tests for step guidance generation."""

import pytest

from tools.principal_audit.guidance import (
    TOTAL_STEPS,
    get_step_guidance,
    PrincipalAuditStepGuidance,
)
from tools.workflow.confidence import ConfidenceLevel


class TestStepGuidance:
    """Test suite for step guidance generation."""

    def test_total_steps_is_five(self):
        """Should have 5 total steps in the workflow."""
        assert TOTAL_STEPS == 5

    def test_step_1_returns_complexity_guidance(self):
        """Step 1 should focus on complexity analysis."""
        guidance = get_step_guidance(1, ConfidenceLevel.EXPLORING)
        assert guidance.step_number == 1
        assert "complexity" in guidance.focus_area.lower()
        assert len(guidance.required_actions) > 0

    def test_step_2_returns_dry_guidance(self):
        """Step 2 should focus on DRY violation detection."""
        guidance = get_step_guidance(2, ConfidenceLevel.MEDIUM)
        assert guidance.step_number == 2
        assert "dry" in guidance.focus_area.lower() or "duplication" in guidance.focus_area.lower()

    def test_step_3_returns_coupling_guidance(self):
        """Step 3 should focus on coupling analysis."""
        guidance = get_step_guidance(3, ConfidenceLevel.MEDIUM)
        assert guidance.step_number == 3
        assert "coupling" in guidance.focus_area.lower()

    def test_step_4_returns_separation_guidance(self):
        """Step 4 should focus on separation of concerns."""
        guidance = get_step_guidance(4, ConfidenceLevel.HIGH)
        assert guidance.step_number == 4
        assert "separation" in guidance.focus_area.lower() or "concern" in guidance.focus_area.lower()

    def test_step_5_returns_maintainability_guidance(self):
        """Step 5 should focus on maintainability and report generation."""
        guidance = get_step_guidance(5, ConfidenceLevel.VERY_HIGH)
        assert guidance.step_number == 5
        assert "maintainability" in guidance.focus_area.lower() or "report" in guidance.focus_area.lower()

    def test_guidance_has_required_actions(self):
        """All steps should have required actions."""
        for step in range(1, 6):
            guidance = get_step_guidance(step, ConfidenceLevel.MEDIUM)
            assert len(guidance.required_actions) > 0

    def test_guidance_has_focus_areas(self):
        """All steps should have focus areas."""
        for step in range(1, 6):
            guidance = get_step_guidance(step, ConfidenceLevel.MEDIUM)
            assert len(guidance.focus_areas) > 0

    def test_guidance_has_next_step_focus_except_last(self):
        """Steps 1-4 should have next step focus, step 5 should not."""
        for step in range(1, 5):
            guidance = get_step_guidance(step, ConfidenceLevel.MEDIUM)
            assert guidance.next_step_focus is not None

        guidance = get_step_guidance(5, ConfidenceLevel.MEDIUM)
        assert guidance.next_step_focus is None or "complete" in guidance.next_step_focus.lower() or "report" in guidance.next_step_focus.lower()

    def test_low_confidence_adds_exploration_actions(self):
        """Low confidence should add exploration actions."""
        guidance_low = get_step_guidance(1, ConfidenceLevel.LOW)
        guidance_high = get_step_guidance(1, ConfidenceLevel.HIGH)
        assert guidance_low.confidence_guidance != guidance_high.confidence_guidance

    def test_step_guidance_dataclass_attributes(self):
        """PrincipalAuditStepGuidance should have all expected attributes."""
        guidance = get_step_guidance(1, ConfidenceLevel.MEDIUM)
        assert hasattr(guidance, "step_number")
        assert hasattr(guidance, "focus_area")
        assert hasattr(guidance, "required_actions")
        assert hasattr(guidance, "focus_areas")
        assert hasattr(guidance, "next_step_focus")
        assert hasattr(guidance, "confidence_guidance")
        assert hasattr(guidance, "missing_context_hints")

    def test_invalid_step_raises_error(self):
        """Should raise error for invalid step numbers."""
        with pytest.raises(ValueError):
            get_step_guidance(0, ConfidenceLevel.MEDIUM)

        with pytest.raises(ValueError):
            get_step_guidance(6, ConfidenceLevel.MEDIUM)

    def test_guidance_with_missing_context(self):
        """Should include context hints when missing context is provided."""
        missing = ["test_files", "architecture_docs"]
        guidance = get_step_guidance(1, ConfidenceLevel.MEDIUM, missing_context=missing)
        assert len(guidance.missing_context_hints) > 0

    def test_to_dict_conversion(self):
        """Should convert to dictionary correctly."""
        guidance = get_step_guidance(1, ConfidenceLevel.MEDIUM)
        result = guidance.to_dict()
        assert "step_number" in result
        assert "focus_area" in result
        assert "required_actions" in result
        assert result["step_number"] == 1
