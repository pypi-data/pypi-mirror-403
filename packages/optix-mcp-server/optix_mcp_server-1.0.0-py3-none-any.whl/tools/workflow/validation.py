"""Validation utilities for workflow requests."""

from typing import Any

from tools.workflow.confidence import ConfidenceLevel


class ValidationError(Exception):
    """Raised when workflow request validation fails."""

    pass


REQUIRED_FIELDS = ["step", "step_number", "total_steps", "next_step_required", "findings"]


def validate_request(data: dict[str, Any]) -> bool:
    """Validate a workflow request dictionary.

    Args:
        data: The request data to validate

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails with descriptive message
    """
    _validate_required_fields(data)
    _validate_step_ranges(data)
    _validate_confidence(data)

    return True


def _validate_required_fields(data: dict[str, Any]) -> None:
    """Validate that all required fields are present.

    Args:
        data: The request data to validate

    Raises:
        ValidationError: If a required field is missing
    """
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")


def _validate_step_ranges(data: dict[str, Any]) -> None:
    """Validate step_number and total_steps ranges.

    Args:
        data: The request data to validate

    Raises:
        ValidationError: If step ranges are invalid
    """
    step_number = data.get("step_number")
    total_steps = data.get("total_steps")

    if step_number is not None and step_number < 1:
        raise ValidationError("step_number must be >= 1")

    if total_steps is not None and total_steps < 1:
        raise ValidationError("total_steps must be >= 1")

    if (
        step_number is not None
        and total_steps is not None
        and step_number > total_steps
    ):
        raise ValidationError(
            f"step_number ({step_number}) cannot exceed total_steps ({total_steps})"
        )


def _validate_confidence(data: dict[str, Any]) -> None:
    """Validate confidence level if provided.

    Args:
        data: The request data to validate

    Raises:
        ValidationError: If confidence is invalid
    """
    confidence = data.get("confidence")

    if confidence is None:
        return

    if isinstance(confidence, ConfidenceLevel):
        return

    if isinstance(confidence, str):
        valid_values = [level.value for level in ConfidenceLevel]
        if confidence.lower() not in valid_values:
            raise ValidationError(
                f"Invalid confidence level: {confidence}. "
                f"Valid values: {', '.join(valid_values)}"
            )
