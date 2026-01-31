"""
Confidence Level Utilities

Utilities for working with confidence levels in expert analysis.
Extracted from DevOps validation for generic use.
"""

from tools.workflow.confidence import ConfidenceLevel


CONFIDENCE_NUMERIC_MAP = {
    ConfidenceLevel.EXPLORING: 0.20,
    ConfidenceLevel.LOW: 0.40,
    ConfidenceLevel.MEDIUM: 0.60,
    ConfidenceLevel.HIGH: 0.75,
    ConfidenceLevel.VERY_HIGH: 0.85,
    ConfidenceLevel.ALMOST_CERTAIN: 0.95,
    ConfidenceLevel.CERTAIN: 1.00,
}


def confidence_to_numeric(confidence: ConfidenceLevel) -> float:
    """
    Convert ConfidenceLevel enum to numeric score.

    Args:
        confidence: ConfidenceLevel enum

    Returns:
        Numeric confidence score (0.0-1.0)
    """
    return CONFIDENCE_NUMERIC_MAP.get(confidence, 0.50)


def numeric_to_confidence(value: float) -> ConfidenceLevel:
    """
    Convert numeric score to ConfidenceLevel enum.

    Args:
        value: Numeric confidence (0.0-1.0)

    Returns:
        ConfidenceLevel enum
    """
    if value >= 1.00:
        return ConfidenceLevel.CERTAIN
    elif value >= 0.95:
        return ConfidenceLevel.ALMOST_CERTAIN
    elif value >= 0.85:
        return ConfidenceLevel.VERY_HIGH
    elif value >= 0.75:
        return ConfidenceLevel.HIGH
    elif value >= 0.60:
        return ConfidenceLevel.MEDIUM
    elif value >= 0.40:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.EXPLORING


def map_confidence_to_score(confidence_str: str) -> float:
    """
    Map confidence level string to numeric score.

    Args:
        confidence_str: Confidence level (exploring, low, medium, high, very_high, certain)

    Returns:
        Numeric confidence score (0.0-1.0)
    """
    mapping = {
        "exploring": 0.2,
        "low": 0.4,
        "medium": 0.6,
        "high": 0.75,
        "very_high": 0.85,
        "almost_certain": 0.95,
        "certain": 1.0,
    }
    return mapping.get(confidence_str.lower(), 0.5)
