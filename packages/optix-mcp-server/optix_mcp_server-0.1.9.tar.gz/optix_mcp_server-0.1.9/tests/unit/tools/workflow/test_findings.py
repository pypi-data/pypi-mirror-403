"""Unit tests for ConsolidatedFindings."""

import pytest

from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings
from tools.workflow.state import StepHistory


class TestConsolidatedFindingsAddStep:
    """Tests for ConsolidatedFindings.add_step() - T019."""

    def test_add_step_stores_findings(self):
        """T019: add_step stores findings from step."""
        consolidated = ConsolidatedFindings()
        step = StepHistory(
            step_number=1,
            step_content="Check logs",
            findings="Found error in logs",
            confidence=ConfidenceLevel.EXPLORING,
        )

        consolidated.add_step(step)

        assert "Found error in logs" in consolidated.findings

    def test_add_step_updates_confidence(self):
        """T019: add_step updates confidence to latest value."""
        consolidated = ConsolidatedFindings()

        step1 = StepHistory(
            step_number=1,
            step_content="Initial",
            findings="Finding 1",
            confidence=ConfidenceLevel.EXPLORING,
        )
        consolidated.add_step(step1)

        step2 = StepHistory(
            step_number=2,
            step_content="Follow up",
            findings="Finding 2",
            confidence=ConfidenceLevel.HIGH,
        )
        consolidated.add_step(step2)

        assert consolidated.confidence == ConfidenceLevel.HIGH


class TestConsolidatedFindingsDeduplication:
    """Tests for file deduplication - T020."""

    def test_files_checked_deduplicates_across_steps(self):
        """T020: files_checked deduplicates files across steps."""
        consolidated = ConsolidatedFindings()

        step1 = StepHistory(
            step_number=1,
            step_content="Check A",
            findings="F1",
            confidence=ConfidenceLevel.EXPLORING,
            files_checked=["a.py", "b.py"],
        )
        consolidated.add_step(step1)

        step2 = StepHistory(
            step_number=2,
            step_content="Check B",
            findings="F2",
            confidence=ConfidenceLevel.MEDIUM,
            files_checked=["b.py", "c.py"],
        )
        consolidated.add_step(step2)

        assert consolidated.files_checked == {"a.py", "b.py", "c.py"}

    def test_relevant_files_deduplicates_across_steps(self):
        """T020: relevant_files deduplicates files across steps."""
        consolidated = ConsolidatedFindings()

        step1 = StepHistory(
            step_number=1,
            step_content="Check A",
            findings="F1",
            confidence=ConfidenceLevel.EXPLORING,
            relevant_files=["a.py"],
        )
        consolidated.add_step(step1)

        step2 = StepHistory(
            step_number=2,
            step_content="Check B",
            findings="F2",
            confidence=ConfidenceLevel.MEDIUM,
            relevant_files=["a.py", "b.py"],
        )
        consolidated.add_step(step2)

        assert consolidated.relevant_files == {"a.py", "b.py"}


class TestConsolidatedFindingsOrdering:
    """Tests for findings ordering preservation - T021."""

    def test_findings_preserve_chronological_order(self):
        """T021: findings maintain chronological order across steps."""
        consolidated = ConsolidatedFindings()

        for i in range(1, 4):
            step = StepHistory(
                step_number=i,
                step_content=f"Step {i}",
                findings=f"Finding {i}",
                confidence=ConfidenceLevel.EXPLORING,
            )
            consolidated.add_step(step)

        assert consolidated.findings == ["Finding 1", "Finding 2", "Finding 3"]

    def test_issues_preserve_chronological_order(self):
        """T021: issues_found maintain chronological order."""
        consolidated = ConsolidatedFindings()

        step1 = StepHistory(
            step_number=1,
            step_content="Check",
            findings="F1",
            confidence=ConfidenceLevel.EXPLORING,
        )
        consolidated.add_step(step1)
        consolidated.add_issue({"severity": "high", "description": "Issue 1"})

        step2 = StepHistory(
            step_number=2,
            step_content="Check more",
            findings="F2",
            confidence=ConfidenceLevel.MEDIUM,
        )
        consolidated.add_step(step2)
        consolidated.add_issue({"severity": "low", "description": "Issue 2"})

        assert len(consolidated.issues_found) == 2
        assert consolidated.issues_found[0]["description"] == "Issue 1"
        assert consolidated.issues_found[1]["description"] == "Issue 2"


class TestConsolidatedFindingsHypothesis:
    """Tests for hypothesis evolution tracking - T022."""

    def test_hypothesis_evolution_tracks_changes(self):
        """T022: hypothesis evolution tracks hypothesis with confidence."""
        consolidated = ConsolidatedFindings()

        step1 = StepHistory(
            step_number=1,
            step_content="Initial",
            findings="F1",
            confidence=ConfidenceLevel.LOW,
            hypothesis="Memory leak",
        )
        consolidated.add_step(step1)

        step2 = StepHistory(
            step_number=2,
            step_content="Verify",
            findings="F2",
            confidence=ConfidenceLevel.HIGH,
            hypothesis="Memory leak in cache",
        )
        consolidated.add_step(step2)

        evolution = consolidated.get_hypothesis_evolution()

        assert len(evolution) == 2
        assert evolution[0]["hypothesis"] == "Memory leak"
        assert evolution[0]["confidence"] == "low"
        assert evolution[1]["hypothesis"] == "Memory leak in cache"
        assert evolution[1]["confidence"] == "high"

    def test_hypothesis_evolution_skips_none_hypotheses(self):
        """T022: hypothesis evolution skips steps without hypothesis."""
        consolidated = ConsolidatedFindings()

        step1 = StepHistory(
            step_number=1,
            step_content="Initial",
            findings="F1",
            confidence=ConfidenceLevel.EXPLORING,
        )
        consolidated.add_step(step1)

        step2 = StepHistory(
            step_number=2,
            step_content="Found it",
            findings="F2",
            confidence=ConfidenceLevel.HIGH,
            hypothesis="Root cause found",
        )
        consolidated.add_step(step2)

        evolution = consolidated.get_hypothesis_evolution()

        assert len(evolution) == 1
        assert evolution[0]["hypothesis"] == "Root cause found"


class TestConsolidatedFindingsSummary:
    """Tests for ConsolidatedFindings helper methods."""

    def test_get_files_summary_returns_counts(self):
        """get_files_summary returns file count statistics."""
        consolidated = ConsolidatedFindings()

        step = StepHistory(
            step_number=1,
            step_content="Check",
            findings="F1",
            confidence=ConfidenceLevel.EXPLORING,
            files_checked=["a.py", "b.py", "c.py"],
            relevant_files=["a.py"],
        )
        consolidated.add_step(step)

        summary = consolidated.get_files_summary()

        assert summary["files_checked_count"] == 3
        assert summary["relevant_files_count"] == 1

    def test_to_dict_serializes_findings(self):
        """to_dict returns dictionary representation."""
        consolidated = ConsolidatedFindings()

        step = StepHistory(
            step_number=1,
            step_content="Check",
            findings="Found issue",
            confidence=ConfidenceLevel.HIGH,
            files_checked=["a.py"],
            relevant_files=["a.py"],
        )
        consolidated.add_step(step)

        result = consolidated.to_dict()

        assert "files_checked" in result
        assert "relevant_files" in result
        assert "findings" in result
        assert result["confidence"] == "high"
