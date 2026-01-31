"""Unit tests for security audit step guidance."""

import pytest

from tools.security_audit.domains import SecurityStepDomain
from tools.security_audit.guidance import (
    SecurityAuditGuidance,
    get_mandatory_pause_instruction,
    get_step_guidance,
)
from tools.workflow.confidence import ConfidenceLevel


class TestGetMandatoryPauseInstruction:
    """Tests for mandatory pause instruction (T028)."""

    def test_contains_mandatory_keyword(self):
        """Instruction should contain MANDATORY keyword."""
        instruction = get_mandatory_pause_instruction("security_audit", 1)
        assert "MANDATORY" in instruction

    def test_contains_do_not_call(self):
        """Instruction should say DO NOT call tool immediately."""
        instruction = get_mandatory_pause_instruction("security_audit", 1)
        assert "DO NOT call" in instruction

    def test_contains_tool_name(self):
        """Instruction should reference the tool name."""
        instruction = get_mandatory_pause_instruction("security_audit", 1)
        assert "security_audit" in instruction

    def test_contains_next_step_number(self):
        """Instruction should reference the next step number."""
        instruction = get_mandatory_pause_instruction("security_audit", 1)
        assert "step_number: 2" in instruction

    def test_instructs_to_examine_code(self):
        """Instruction should tell user to examine code files."""
        instruction = get_mandatory_pause_instruction("security_audit", 3)
        assert "examine" in instruction.lower()


class TestStep1Guidance:
    """Tests for Step 1: Reconnaissance guidance (T029)."""

    def test_step_1_domain_is_reconnaissance(self):
        """Step 1 should have RECONNAISSANCE domain."""
        guidance = get_step_guidance(1, ConfidenceLevel.EXPLORING, "security_audit")
        assert guidance.domain == SecurityStepDomain.RECONNAISSANCE

    def test_step_1_has_required_actions(self):
        """Step 1 should have required actions for reconnaissance."""
        guidance = get_step_guidance(1, ConfidenceLevel.EXPLORING, "security_audit")
        assert len(guidance.required_actions) > 0
        actions_text = " ".join(guidance.required_actions).lower()
        assert "application" in actions_text or "technology" in actions_text

    def test_step_1_has_focus_areas(self):
        """Step 1 should have focus areas."""
        guidance = get_step_guidance(1, ConfidenceLevel.EXPLORING, "security_audit")
        assert len(guidance.focus_areas) > 0


class TestStep2Guidance:
    """Tests for Step 2: Auth/AuthZ guidance (T030)."""

    def test_step_2_domain_is_auth_authz(self):
        """Step 2 should have AUTH_AUTHZ domain."""
        guidance = get_step_guidance(2, ConfidenceLevel.LOW, "security_audit")
        assert guidance.domain == SecurityStepDomain.AUTH_AUTHZ

    def test_step_2_covers_authentication(self):
        """Step 2 should cover authentication."""
        guidance = get_step_guidance(2, ConfidenceLevel.LOW, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "authentication" in actions_text or "auth" in actions_text

    def test_step_2_covers_authorization(self):
        """Step 2 should cover authorization."""
        guidance = get_step_guidance(2, ConfidenceLevel.LOW, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "authorization" in actions_text or "privilege" in actions_text


class TestStep3Guidance:
    """Tests for Step 3: Input Validation guidance (T031)."""

    def test_step_3_domain_is_input_validation(self):
        """Step 3 should have INPUT_VALIDATION domain."""
        guidance = get_step_guidance(3, ConfidenceLevel.MEDIUM, "security_audit")
        assert guidance.domain == SecurityStepDomain.INPUT_VALIDATION

    def test_step_3_covers_validation(self):
        """Step 3 should cover input validation."""
        guidance = get_step_guidance(3, ConfidenceLevel.MEDIUM, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "validation" in actions_text or "sanitization" in actions_text

    def test_step_3_covers_injection(self):
        """Step 3 should cover injection vulnerabilities."""
        guidance = get_step_guidance(3, ConfidenceLevel.MEDIUM, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "injection" in actions_text


class TestStep4Guidance:
    """Tests for Step 4: OWASP Top 10 guidance (T032)."""

    def test_step_4_domain_is_owasp(self):
        """Step 4 should have OWASP_TOP_10 domain."""
        guidance = get_step_guidance(4, ConfidenceLevel.MEDIUM, "security_audit")
        assert guidance.domain == SecurityStepDomain.OWASP_TOP_10

    def test_step_4_covers_owasp_categories(self):
        """Step 4 should reference OWASP categories."""
        guidance = get_step_guidance(4, ConfidenceLevel.MEDIUM, "security_audit")
        actions_text = " ".join(guidance.required_actions)
        assert "A01" in actions_text or "A02" in actions_text or "A03" in actions_text


class TestStep5Guidance:
    """Tests for Step 5: Dependencies guidance (T033)."""

    def test_step_5_domain_is_dependencies(self):
        """Step 5 should have DEPENDENCIES domain."""
        guidance = get_step_guidance(5, ConfidenceLevel.HIGH, "security_audit")
        assert guidance.domain == SecurityStepDomain.DEPENDENCIES

    def test_step_5_covers_dependencies(self):
        """Step 5 should cover dependency auditing."""
        guidance = get_step_guidance(5, ConfidenceLevel.HIGH, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "dependencies" in actions_text or "third-party" in actions_text

    def test_step_5_covers_secrets(self):
        """Step 5 should cover secrets in code."""
        guidance = get_step_guidance(5, ConfidenceLevel.HIGH, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "secrets" in actions_text or "configuration" in actions_text


class TestStep6Guidance:
    """Tests for Step 6: Compliance guidance (T034)."""

    def test_step_6_domain_is_compliance(self):
        """Step 6 should have COMPLIANCE domain."""
        guidance = get_step_guidance(6, ConfidenceLevel.VERY_HIGH, "security_audit")
        assert guidance.domain == SecurityStepDomain.COMPLIANCE

    def test_step_6_covers_compliance(self):
        """Step 6 should cover compliance assessment."""
        guidance = get_step_guidance(6, ConfidenceLevel.VERY_HIGH, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "compliance" in actions_text or "standards" in actions_text

    def test_step_6_covers_remediation(self):
        """Step 6 should cover remediation planning."""
        guidance = get_step_guidance(6, ConfidenceLevel.VERY_HIGH, "security_audit")
        actions_text = " ".join(guidance.required_actions).lower()
        assert "remediation" in actions_text

    def test_step_6_next_steps_is_final(self):
        """Step 6 should indicate it's the final step."""
        guidance = get_step_guidance(6, ConfidenceLevel.VERY_HIGH, "security_audit")
        assert "final step" in guidance.next_steps.lower()


class TestGuidanceNextSteps:
    """Tests for next_steps guidance across all steps (T035-T036)."""

    def test_steps_1_to_5_have_mandatory_pause(self):
        """Steps 1-5 should have MANDATORY pause instruction."""
        for step in range(1, 6):
            guidance = get_step_guidance(step, ConfidenceLevel.MEDIUM, "security_audit")
            assert "MANDATORY" in guidance.next_steps

    def test_step_6_has_completion_instruction(self):
        """Step 6 should have completion instruction."""
        guidance = get_step_guidance(6, ConfidenceLevel.HIGH, "security_audit")
        assert "next_step_required: false" in guidance.next_steps


class TestSecurityAuditGuidanceDataclass:
    """Tests for SecurityAuditGuidance dataclass (T037)."""

    def test_guidance_has_step_number(self):
        """Guidance should have step_number."""
        guidance = SecurityAuditGuidance(
            step_number=1,
            domain=SecurityStepDomain.RECONNAISSANCE,
        )
        assert guidance.step_number == 1

    def test_guidance_has_domain(self):
        """Guidance should have domain."""
        guidance = SecurityAuditGuidance(
            step_number=2,
            domain=SecurityStepDomain.AUTH_AUTHZ,
        )
        assert guidance.domain == SecurityStepDomain.AUTH_AUTHZ

    def test_guidance_default_required_actions(self):
        """Guidance should have empty required_actions by default."""
        guidance = SecurityAuditGuidance(
            step_number=1,
            domain=SecurityStepDomain.RECONNAISSANCE,
        )
        assert guidance.required_actions == []

    def test_guidance_default_focus_areas(self):
        """Guidance should have empty focus_areas by default."""
        guidance = SecurityAuditGuidance(
            step_number=1,
            domain=SecurityStepDomain.RECONNAISSANCE,
        )
        assert guidance.focus_areas == []


class TestConfidenceImpact:
    """Tests for confidence level impact on guidance (T038-T041)."""

    def test_guidance_available_at_all_confidence_levels(self):
        """Guidance should be available at all confidence levels."""
        for level in ConfidenceLevel:
            for step in range(1, 7):
                guidance = get_step_guidance(step, level, "security_audit")
                assert guidance is not None
                assert guidance.domain is not None

    def test_low_confidence_gets_full_guidance(self):
        """Low confidence should get full step guidance."""
        guidance = get_step_guidance(1, ConfidenceLevel.LOW, "security_audit")
        assert len(guidance.required_actions) > 0

    def test_certain_confidence_still_gets_guidance(self):
        """Even certain confidence gets guidance (workflow continues)."""
        guidance = get_step_guidance(3, ConfidenceLevel.CERTAIN, "security_audit")
        assert len(guidance.required_actions) > 0
