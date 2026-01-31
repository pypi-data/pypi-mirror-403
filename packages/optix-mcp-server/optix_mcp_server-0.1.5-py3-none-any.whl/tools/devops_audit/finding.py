"""DevOpsFinding and ConsolidatedDevOpsFindings data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from tools.devops_audit.domains import DevOpsCategory
from tools.devops_audit.severity import Severity
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings


def transform_legacy_devops_finding_format(data: dict[str, Any]) -> dict[str, Any]:
    """Transform legacy/LLM finding format to current format.

    Handles common variations from LLM responses:
    - "file" / "file_path" / "files" → "affected_files" list
    - "issue" / "finding" / "problem" → "description"
    - "fix" / "recommendation" → "remediation"
    - "type" → "category"
    - Missing required fields → appropriate defaults

    Args:
        data: Finding data in legacy or current format

    Returns:
        Finding data in current expected format
    """
    if all(k in data for k in ("description", "affected_files", "category", "severity")):
        return data

    transformed = data.copy()

    if "type" in transformed and "category" not in transformed:
        transformed["category"] = transformed.pop("type")

    for alias in ("issue", "finding", "problem", "title"):
        if alias in transformed and "description" not in transformed:
            transformed["description"] = transformed.pop(alias)
            break

    for alias in ("fix", "recommendation", "solution"):
        if alias in transformed and "remediation" not in transformed:
            transformed["remediation"] = transformed.pop(alias)
            break

    if "affected_files" not in transformed:
        affected = []

        for alias in ("file", "file_path", "path"):
            if alias in transformed:
                value = transformed.pop(alias)
                if value and isinstance(value, str):
                    affected.append(value)
                break

        if "files" in transformed:
            files = transformed.pop("files")
            if isinstance(files, list):
                affected.extend(str(f) for f in files if f)
            elif isinstance(files, str):
                affected.append(files)

        transformed["affected_files"] = affected if affected else ["unknown"]

    if "affected_files" in transformed:
        af = transformed["affected_files"]
        if isinstance(af, list):
            normalized = []
            for item in af:
                if isinstance(item, str):
                    normalized.append(item)
                elif isinstance(item, dict):
                    normalized.append(item.get("file_path", item.get("path", str(item))))
                else:
                    normalized.append(str(item))
            transformed["affected_files"] = normalized

    return transformed


@dataclass
class DevOpsFinding:
    """Single infrastructure issue discovered during DevOps audit."""

    severity: Severity
    category: DevOpsCategory
    description: str
    affected_files: list[str]
    remediation: Optional[str] = None
    line_numbers: Optional[list[int]] = None
    confidence: Optional[ConfidenceLevel] = None
    llm_assessments: Optional[list[dict]] = None
    validation_timestamp: Optional[datetime] = None

    def __post_init__(self):
        if isinstance(self.severity, str):
            self.severity = Severity.from_string(self.severity)
        if isinstance(self.category, str):
            self.category = DevOpsCategory.from_string(self.category)
        if isinstance(self.confidence, str):
            self.confidence = ConfidenceLevel(self.confidence)
        if not self.affected_files:
            raise ValueError("affected_files must contain at least one file path")
        if not self.description:
            raise ValueError("description must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary representation."""
        result: dict[str, Any] = {
            "severity": self.severity.value,
            "category": self.category.value,
            "description": self.description,
            "affected_files": self.affected_files,
        }
        if self.remediation:
            result["remediation"] = self.remediation
        if self.line_numbers:
            result["line_numbers"] = self.line_numbers
        if self.confidence:
            result["confidence"] = self.confidence.value
        if self.llm_assessments:
            result["llm_assessments"] = self.llm_assessments
        if self.validation_timestamp:
            result["validation_timestamp"] = self.validation_timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DevOpsFinding":
        """Create DevOpsFinding from dictionary.

        Handles legacy/LLM format variations via transform function.

        Args:
            data: Dictionary with finding data. Accepts various field name
                  variations (e.g., "file" instead of "affected_files").

        Returns:
            DevOpsFinding instance
        """
        data = transform_legacy_devops_finding_format(data)

        timestamp = data.get("validation_timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            severity=data.get("severity", "medium"),
            category=data.get("category", "general"),
            description=data.get("description", ""),
            affected_files=data.get("affected_files", ["unknown"]),
            remediation=data.get("remediation"),
            line_numbers=data.get("line_numbers"),
            confidence=data.get("confidence"),
            llm_assessments=data.get("llm_assessments"),
            validation_timestamp=timestamp,
        )


@dataclass
class ConsolidatedDevOpsFindings(ConsolidatedFindings):
    """Aggregated findings with DevOps-specific tracking."""

    dockerfiles_analyzed: list[str] = field(default_factory=list)
    workflows_analyzed: list[str] = field(default_factory=list)
    package_files_analyzed: list[str] = field(default_factory=list)
    dockerfiles_omitted: list[str] = field(default_factory=list)
    workflows_omitted: list[str] = field(default_factory=list)
    package_files_omitted: list[str] = field(default_factory=list)
    missing_lockfiles: list[str] = field(default_factory=list)
    missing_context_requested: list[str] = field(default_factory=list)

    def get_findings_by_category(self) -> dict[DevOpsCategory, list[DevOpsFinding]]:
        """Group findings by DevOps category."""
        grouped: dict[DevOpsCategory, list[DevOpsFinding]] = {
            category: [] for category in DevOpsCategory
        }
        for issue in self.issues_found:
            try:
                finding = DevOpsFinding.from_dict(issue)
                grouped[finding.category].append(finding)
            except (KeyError, ValueError):
                pass
        return grouped

    def get_artifact_coverage_summary(self) -> dict:
        """Summary of analyzed vs omitted artifacts."""
        return {
            "dockerfiles": {
                "analyzed": len(self.dockerfiles_analyzed),
                "omitted": len(self.dockerfiles_omitted),
                "files": self.dockerfiles_analyzed,
            },
            "workflows": {
                "analyzed": len(self.workflows_analyzed),
                "omitted": len(self.workflows_omitted),
                "files": self.workflows_analyzed,
            },
            "package_files": {
                "analyzed": len(self.package_files_analyzed),
                "omitted": len(self.package_files_omitted),
                "files": self.package_files_analyzed,
            },
        }

    def get_missing_context_summary(self) -> dict:
        """Summary of requested but not provided context."""
        return {
            "missing_lockfiles": self.missing_lockfiles,
            "other_missing_context": self.missing_context_requested,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "dockerfiles_analyzed": self.dockerfiles_analyzed,
                "workflows_analyzed": self.workflows_analyzed,
                "package_files_analyzed": self.package_files_analyzed,
                "dockerfiles_omitted": self.dockerfiles_omitted,
                "workflows_omitted": self.workflows_omitted,
                "package_files_omitted": self.package_files_omitted,
                "missing_lockfiles": self.missing_lockfiles,
                "missing_context_requested": self.missing_context_requested,
            }
        )
        return base_dict

    def get_devops_audit_summary(self) -> dict[str, Any]:
        """Generate DevOps-specific summary for audit report."""
        by_severity = self.get_findings_by_severity()
        by_category = self.get_findings_by_category()
        coverage = self.get_artifact_coverage_summary()

        return {
            "total_findings": len(self.issues_found),
            "severity_counts": {
                "critical": len(by_severity["critical"]),
                "high": len(by_severity["high"]),
                "medium": len(by_severity["medium"]),
                "low": len(by_severity["low"]),
                "info": len(by_severity.get("info", [])),
            },
            "category_counts": {
                cat.value: len(findings) for cat, findings in by_category.items()
            },
            "artifact_coverage": coverage,
            "missing_context": self.get_missing_context_summary(),
            "confidence": self.confidence.value,
        }
