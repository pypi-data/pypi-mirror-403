"""Unit tests for workflow request validation."""

import pytest

from tools.workflow.confidence import ConfidenceLevel


class TestRequiredFieldValidation:
    """Tests for required field validation - T037."""

    def test_missing_step_raises_error(self):
        """T037: Missing step field raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step_number": 1,
                "total_steps": 3,
                "next_step_required": True,
                "findings": "Some findings",
            })

        assert "step" in str(exc_info.value).lower()

    def test_missing_step_number_raises_error(self):
        """T037: Missing step_number field raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "total_steps": 3,
                "next_step_required": True,
                "findings": "Some findings",
            })

        assert "step_number" in str(exc_info.value).lower()

    def test_missing_total_steps_raises_error(self):
        """T037: Missing total_steps field raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": 1,
                "next_step_required": True,
                "findings": "Some findings",
            })

        assert "total_steps" in str(exc_info.value).lower()

    def test_missing_next_step_required_raises_error(self):
        """T037: Missing next_step_required field raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": 1,
                "total_steps": 3,
                "findings": "Some findings",
            })

        assert "next_step_required" in str(exc_info.value).lower()

    def test_missing_findings_raises_error(self):
        """T037: Missing findings field raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": 1,
                "total_steps": 3,
                "next_step_required": True,
            })

        assert "findings" in str(exc_info.value).lower()


class TestStepNumberValidation:
    """Tests for step_number validation - T038."""

    def test_step_number_zero_raises_error(self):
        """T038: step_number=0 raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": 0,
                "total_steps": 3,
                "next_step_required": True,
                "findings": "Some findings",
            })

        assert "step_number" in str(exc_info.value).lower()
        assert "1" in str(exc_info.value)

    def test_step_number_negative_raises_error(self):
        """T038: Negative step_number raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": -1,
                "total_steps": 3,
                "next_step_required": True,
                "findings": "Some findings",
            })

        assert "step_number" in str(exc_info.value).lower()

    def test_total_steps_zero_raises_error(self):
        """T038: total_steps=0 raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": 1,
                "total_steps": 0,
                "next_step_required": True,
                "findings": "Some findings",
            })

        assert "total_steps" in str(exc_info.value).lower()

    def test_step_number_exceeds_total_steps_raises_error(self):
        """T038: step_number > total_steps raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": 5,
                "total_steps": 3,
                "next_step_required": True,
                "findings": "Some findings",
            })

        assert "step_number" in str(exc_info.value).lower()
        assert "total_steps" in str(exc_info.value).lower()


class TestConfidenceLevelValidation:
    """Tests for confidence level validation - T039."""

    def test_invalid_confidence_string_raises_error(self):
        """T039: Invalid confidence string raises ValidationError."""
        from tools.workflow.validation import ValidationError, validate_request

        with pytest.raises(ValidationError) as exc_info:
            validate_request({
                "step": "Investigation step",
                "step_number": 1,
                "total_steps": 3,
                "next_step_required": True,
                "findings": "Some findings",
                "confidence": "invalid_confidence",
            })

        assert "confidence" in str(exc_info.value).lower()

    def test_valid_confidence_enum_accepted(self):
        """T039: Valid ConfidenceLevel enum is accepted."""
        from tools.workflow.validation import validate_request

        result = validate_request({
            "step": "Investigation step",
            "step_number": 1,
            "total_steps": 3,
            "next_step_required": True,
            "findings": "Some findings",
            "confidence": ConfidenceLevel.HIGH,
        })

        assert result is True

    def test_valid_confidence_string_accepted(self):
        """T039: Valid confidence string is accepted."""
        from tools.workflow.validation import validate_request

        result = validate_request({
            "step": "Investigation step",
            "step_number": 1,
            "total_steps": 3,
            "next_step_required": True,
            "findings": "Some findings",
            "confidence": "high",
        })

        assert result is True


class TestValidRequestAcceptance:
    """Tests for valid request acceptance - T040."""

    def test_minimal_valid_request_accepted(self):
        """T040: Minimal valid request is accepted."""
        from tools.workflow.validation import validate_request

        result = validate_request({
            "step": "Investigation step",
            "step_number": 1,
            "total_steps": 3,
            "next_step_required": True,
            "findings": "Some findings",
        })

        assert result is True

    def test_complete_valid_request_accepted(self):
        """T040: Complete valid request with all optional fields is accepted."""
        from tools.workflow.validation import validate_request

        result = validate_request({
            "step": "Investigation step",
            "step_number": 2,
            "total_steps": 5,
            "next_step_required": True,
            "findings": "Found authentication issue",
            "confidence": "medium",
            "hypothesis": "Authentication bypass possible",
            "files_checked": ["/src/auth.py", "/src/login.py"],
            "relevant_files": ["/src/auth.py"],
            "relevant_context": ["authenticate()", "validate_token()"],
            "continuation_id": "abc-123",
        })

        assert result is True

    def test_final_step_valid_request_accepted(self):
        """T040: Final step request with next_step_required=false is accepted."""
        from tools.workflow.validation import validate_request

        result = validate_request({
            "step": "Final investigation step",
            "step_number": 3,
            "total_steps": 3,
            "next_step_required": False,
            "findings": "Root cause identified",
            "confidence": "certain",
        })

        assert result is True
