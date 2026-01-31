"""Unit tests for StepGuidance."""

import pytest

from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.guidance import StepGuidance


class TestStepGuidanceDataclass:
    """Tests for StepGuidance dataclass - T029."""

    def test_step_guidance_creation_with_required_fields(self):
        """T029: StepGuidance can be created with required fields."""
        guidance = StepGuidance(
            required_actions=["Action 1", "Action 2"],
        )

        assert guidance.required_actions == ["Action 1", "Action 2"]
        assert guidance.suggestions == []
        assert guidance.next_step_focus is None
        assert guidance.confidence_guidance == ""

    def test_step_guidance_creation_with_all_fields(self):
        """T029: StepGuidance can be created with all fields."""
        guidance = StepGuidance(
            required_actions=["Action 1"],
            suggestions=["Suggestion 1"],
            next_step_focus="Focus area",
            confidence_guidance="How to increase confidence",
        )

        assert guidance.required_actions == ["Action 1"]
        assert guidance.suggestions == ["Suggestion 1"]
        assert guidance.next_step_focus == "Focus area"
        assert guidance.confidence_guidance == "How to increase confidence"

    def test_step_guidance_to_dict(self):
        """T029: StepGuidance.to_dict returns dictionary representation."""
        guidance = StepGuidance(
            required_actions=["Action 1", "Action 2"],
            suggestions=["Hint 1"],
            next_step_focus="Check logs",
            confidence_guidance="Gather more evidence",
        )

        result = guidance.to_dict()

        assert result["required_actions"] == ["Action 1", "Action 2"]
        assert result["suggestions"] == ["Hint 1"]
        assert result["next_step_focus"] == "Check logs"
        assert result["confidence_guidance"] == "Gather more evidence"


class TestDefaultGetRequiredActions:
    """Tests for default get_required_actions() - T030."""

    def test_exploring_confidence_returns_broad_actions(self):
        """T030: Low confidence returns broad investigation actions."""
        from tools.workflow.base import WorkflowTool
        from typing import Any

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()
        actions = tool.get_required_actions(1, ConfidenceLevel.EXPLORING)

        assert len(actions) >= 2
        assert any("broaden" in a.lower() or "gather" in a.lower() for a in actions)

    def test_high_confidence_returns_verification_actions(self):
        """T030: High confidence returns verification-focused actions."""
        from tools.workflow.base import WorkflowTool
        from typing import Any

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()
        actions = tool.get_required_actions(3, ConfidenceLevel.HIGH)

        assert len(actions) >= 2
        assert any("validat" in a.lower() or "document" in a.lower() for a in actions)


class TestConfidenceBasedGuidance:
    """Tests for confidence-based guidance variation - T031."""

    def test_guidance_varies_by_confidence_level(self):
        """T031: Step guidance varies based on confidence level."""
        from tools.workflow.base import WorkflowTool
        from tools.workflow.request import WorkflowRequest
        from tools.workflow.state import WorkflowStateManager
        from typing import Any

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        manager = WorkflowStateManager()
        manager.clear_all()

        tool = TestTool()

        low_actions = tool.get_required_actions(1, ConfidenceLevel.LOW)
        high_actions = tool.get_required_actions(3, ConfidenceLevel.HIGH)

        assert low_actions != high_actions

    def test_certain_confidence_returns_completion_actions(self):
        """T031: Certain confidence returns completion-focused actions."""
        from tools.workflow.base import WorkflowTool
        from typing import Any

        class TestTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

        tool = TestTool()
        actions = tool.get_required_actions(5, ConfidenceLevel.CERTAIN)

        assert len(actions) >= 1
        assert any(
            "verif" in a.lower() or "conclus" in a.lower() or "document" in a.lower()
            for a in actions
        )


class TestCustomStepGuidance:
    """Tests for custom step guidance override."""

    def test_custom_tool_can_override_get_required_actions(self):
        """Custom tools can override get_required_actions for domain guidance."""
        from tools.workflow.base import WorkflowTool
        from typing import Any

        class SecurityTool(WorkflowTool):
            @property
            def name(self) -> str:
                return "security"

            @property
            def description(self) -> str:
                return "Security audit tool"

            def prepare_expert_analysis_context(self, consolidated) -> dict[str, Any]:
                return {}

            def get_required_actions(
                self, step_number: int, confidence: ConfidenceLevel
            ) -> list[str]:
                if step_number == 1:
                    return ["Review authentication flows", "Check input validation"]
                return ["Document security findings", "Prepare remediation plan"]

        tool = SecurityTool()
        step1_actions = tool.get_required_actions(1, ConfidenceLevel.EXPLORING)
        step2_actions = tool.get_required_actions(2, ConfidenceLevel.HIGH)

        assert "Review authentication flows" in step1_actions
        assert "Prepare remediation plan" in step2_actions
