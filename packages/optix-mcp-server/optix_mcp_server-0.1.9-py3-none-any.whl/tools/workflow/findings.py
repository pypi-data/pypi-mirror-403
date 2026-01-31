"""ConsolidatedFindings model for aggregating workflow step data."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from tools.workflow.confidence import ConfidenceLevel


@dataclass
class ConsolidatedFindings:
    """Aggregation model that combines findings from all workflow steps.

    Uses sets for file deduplication and lists for ordered history.
    Tracks the evolution of findings, hypotheses, and confidence across steps.
    """

    files_checked: set[str] = field(default_factory=set)
    relevant_files: set[str] = field(default_factory=set)
    relevant_context: set[str] = field(default_factory=set)
    findings: list[str] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    issues_found: list[dict[str, Any]] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.EXPLORING

    def add_step(self, step_data: Any) -> None:
        """Merge step data into consolidated state.

        Deduplicates files while preserving finding order.

        Args:
            step_data: StepHistory instance with step findings
        """
        self.files_checked.update(step_data.files_checked)
        self.relevant_files.update(step_data.relevant_files)

        if step_data.findings:
            self.findings.append(step_data.findings)
            step_timestamp = getattr(step_data, "timestamp", None)
            step_number = getattr(step_data, "step_number", None)
            self._parse_and_add_findings(step_data.findings, step_number, step_timestamp)

        if step_data.hypothesis:
            self.hypotheses.append({
                "hypothesis": step_data.hypothesis,
                "confidence": step_data.confidence.value,
                "step_number": step_data.step_number,
            })

        self.confidence = step_data.confidence

    def _parse_and_add_findings(
        self,
        findings_str: str,
        step_number: int | None = None,
        step_timestamp: datetime | None = None,
    ) -> None:
        """Parse JSON findings string and add valid findings to issues_found.

        Args:
            findings_str: JSON string of findings array
            step_number: Step number where findings were discovered
            step_timestamp: Timestamp of the step
        """
        if not findings_str or findings_str.strip() == "":
            return
        try:
            parsed = json.loads(findings_str)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        self._add_issue_if_unique(item, step_number, step_timestamp)
        except (json.JSONDecodeError, TypeError):
            pass

    def _add_issue_if_unique(
        self,
        issue: dict[str, Any],
        step_number: int | None = None,
        step_timestamp: datetime | None = None,
    ) -> bool:
        """Add issue only if not a duplicate based on description+severity+location.

        Args:
            issue: Dictionary with severity, description, and location/file_path
            step_number: Step number where the issue was discovered
            step_timestamp: Timestamp when the issue was discovered

        Returns:
            True if issue was added, False if duplicate
        """
        desc = issue.get("description", "")
        severity = issue.get("severity", "info")
        location = issue.get("location", issue.get("file_path", ""))
        dedup_key = f"{severity}:{desc}:{location}"

        for existing in self.issues_found:
            existing_key = (
                f"{existing.get('severity', 'info')}:"
                f"{existing.get('description', '')}:"
                f"{existing.get('location', existing.get('file_path', ''))}"
            )
            if existing_key == dedup_key:
                return False

        issue["finding_id"] = f"OPX-{uuid.uuid4().hex[:8].upper()}"
        issue["discovered_at"] = (
            step_timestamp.isoformat() if step_timestamp else datetime.now().isoformat()
        )
        issue["discovered_in_step"] = step_number

        self.issues_found.append(issue)
        return True

    def add_issue(self, issue: dict[str, Any]) -> None:
        """Add an issue to the consolidated findings with deduplication.

        Args:
            issue: Dictionary with severity and description
        """
        self._add_issue_if_unique(issue)

    def add_context(self, context: list[str]) -> None:
        """Add relevant context (methods/functions) to findings.

        Args:
            context: List of context strings to add
        """
        self.relevant_context.update(context)

    def add_image(self, image_path: str) -> None:
        """Add an image path to the findings.

        Args:
            image_path: Path to image file
        """
        self.images.append(image_path)

    def get_files_summary(self) -> dict[str, int]:
        """Return deduplicated file statistics.

        Returns:
            Dictionary with file count statistics
        """
        return {
            "files_checked_count": len(self.files_checked),
            "relevant_files_count": len(self.relevant_files),
            "relevant_context_count": len(self.relevant_context),
        }

    def get_hypothesis_evolution(self) -> list[dict[str, Any]]:
        """Return hypothesis progression across steps.

        Returns:
            List of hypothesis records with confidence
        """
        return self.hypotheses.copy()

    def to_dict(self) -> dict[str, Any]:
        """Convert the consolidated findings to a dictionary.

        Returns:
            Dictionary representation of the findings
        """
        return {
            "files_checked": list(self.files_checked),
            "relevant_files": list(self.relevant_files),
            "relevant_context": list(self.relevant_context),
            "findings": self.findings,
            "hypotheses": self.hypotheses,
            "issues_found": self.issues_found,
            "images": self.images,
            "confidence": self.confidence.value,
        }

    def get_findings_by_severity(self) -> dict[str, list[dict[str, Any]]]:
        """Group issues_found by severity level.

        Returns:
            Dictionary mapping severity to list of issues
        """
        result: dict[str, list[dict[str, Any]]] = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }
        for issue in self.issues_found:
            severity = issue.get("severity", "medium").lower()
            if severity in result:
                result[severity].append(issue)
            else:
                result["medium"].append(issue)
        return result

    def has_critical_or_high(self) -> bool:
        """Check if any critical or high severity findings exist.

        Returns:
            True if critical or high severity issues found
        """
        for issue in self.issues_found:
            severity = issue.get("severity", "").lower()
            if severity in ("critical", "high"):
                return True
        return False

    def get_audit_summary(self) -> dict[str, Any]:
        """Generate summary for audit report.

        Returns:
            Dictionary with audit summary data
        """
        by_severity = self.get_findings_by_severity()
        return {
            "total_vulnerabilities": len(self.issues_found),
            "severity_counts": {
                "critical": len(by_severity["critical"]),
                "high": len(by_severity["high"]),
                "medium": len(by_severity["medium"]),
                "low": len(by_severity["low"]),
                "info": len(by_severity["info"]),
            },
            "files_examined": len(self.files_checked),
            "confidence": self.confidence.value,
        }
