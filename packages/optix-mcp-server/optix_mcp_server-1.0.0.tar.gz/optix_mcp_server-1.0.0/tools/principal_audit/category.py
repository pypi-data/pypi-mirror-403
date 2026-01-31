"""FindingCategory enum for categorizing code quality findings."""

from enum import Enum


class FindingCategory(Enum):
    """Categories of code quality findings.

    Each category corresponds to a specific analysis domain in the 5-step workflow:
    - Step 1: COMPLEXITY (FR-001)
    - Step 2: DRY_VIOLATION (FR-002)
    - Step 3: COUPLING (FR-003)
    - Step 4: SEPARATION_OF_CONCERNS (FR-004)
    - Step 5: MAINTAINABILITY_RISK (FR-005)
    """

    COMPLEXITY = "complexity"
    DRY_VIOLATION = "dry_violation"
    COUPLING = "coupling"
    SEPARATION_OF_CONCERNS = "separation_of_concerns"
    MAINTAINABILITY_RISK = "maintainability_risk"
