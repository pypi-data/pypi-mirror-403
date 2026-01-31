"""Security step domains for the 6-step audit workflow."""

from enum import Enum


class SecurityStepDomain(Enum):
    """Security domains for each audit step."""

    RECONNAISSANCE = "reconnaissance"
    AUTH_AUTHZ = "auth_authz"
    INPUT_VALIDATION = "input_validation"
    OWASP_TOP_10 = "owasp_top_10"
    DEPENDENCIES = "dependencies"
    COMPLIANCE = "compliance"

    @classmethod
    def for_step(cls, step_number: int) -> "SecurityStepDomain":
        """Get the security domain for a given step number.

        Args:
            step_number: Step number (1-6)

        Returns:
            SecurityStepDomain for that step

        Raises:
            ValueError: If step_number is not 1-6
        """
        step_map = {
            1: cls.RECONNAISSANCE,
            2: cls.AUTH_AUTHZ,
            3: cls.INPUT_VALIDATION,
            4: cls.OWASP_TOP_10,
            5: cls.DEPENDENCIES,
            6: cls.COMPLIANCE,
        }
        if step_number not in step_map:
            raise ValueError(f"Invalid step number: {step_number}. Must be 1-6.")
        return step_map[step_number]

    @property
    def display_name(self) -> str:
        """Human-readable name for the domain."""
        names = {
            SecurityStepDomain.RECONNAISSANCE: "Application Reconnaissance",
            SecurityStepDomain.AUTH_AUTHZ: "Authentication & Authorization",
            SecurityStepDomain.INPUT_VALIDATION: "Input Validation & Cryptography",
            SecurityStepDomain.OWASP_TOP_10: "OWASP Top 10 Review",
            SecurityStepDomain.DEPENDENCIES: "Dependencies & Configuration",
            SecurityStepDomain.COMPLIANCE: "Compliance & Remediation",
        }
        return names[self]
