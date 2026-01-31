"""Data models for the Optix Dashboard.

These are read-only projections of existing data for API responses.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Optional

from tools.workflow.state import WorkflowState, StepHistory


def _format_findings_for_display(findings: str) -> str:
    """Format findings string for dashboard display.

    Converts raw JSON findings to human-readable summary.
    """
    if not findings or findings.strip() == "":
        return ""

    try:
        parsed = json.loads(findings)
        if isinstance(parsed, list):
            count = len(parsed)
            if count == 0:
                return ""
            severities = {}
            for item in parsed:
                if isinstance(item, dict):
                    sev = item.get("severity", "info")
                    severities[sev] = severities.get(sev, 0) + 1

            if severities:
                parts = [f"{c} {s}" for s, c in sorted(severities.items(), key=lambda x: x[1], reverse=True)]
                return f"{count} findings: {', '.join(parts)}"
            return f"{count} findings recorded"
        return findings
    except (json.JSONDecodeError, TypeError):
        return findings

AUDIT_TOTAL_STEPS: dict[str, int] = {
    "security_audit": 6,
    "a11y_audit": 6,
    "devops_audit": 4,
    "principal_audit": 5,
}

AUDIT_TYPE_MAP: dict[str, str] = {
    "SECURITY_AUDIT": "Security",
    "A11Y_AUDIT": "A11y",
    "DEVOPS_AUDIT": "DevOps",
    "PRINCIPAL_AUDIT": "Principal",
}

CONFIDENCE_COLORS: dict[str, str] = {
    "exploring": "gray",
    "low": "yellow",
    "medium": "orange",
    "high": "green",
    "very_high": "emerald",
    "almost_certain": "blue",
    "certain": "blue",
}

WORKFLOW_ACTIVE_THRESHOLD_SECONDS: int = 300


def format_uptime(seconds: float) -> str:
    """Format uptime in seconds to human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def infer_audit_type(filename: str) -> str:
    """Infer audit type from report filename."""
    for prefix, audit_type in AUDIT_TYPE_MAP.items():
        if filename.upper().startswith(prefix):
            return audit_type
    return "Unknown"


@dataclass
class StepSummary:
    """Single step in the workflow history."""
    step_number: int
    step_content: str
    findings: str
    confidence: str
    files_checked_count: int
    timestamp: str

    @classmethod
    def from_step(cls, step: StepHistory) -> "StepSummary":
        """Create StepSummary from StepHistory."""
        return cls(
            step_number=step.step_number,
            step_content=step.step_content,
            findings=_format_findings_for_display(step.findings),
            confidence=step.confidence.value,
            files_checked_count=len(step.files_checked),
            timestamp=step.timestamp.isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class IssueSummary:
    """Single issue/finding from the audit."""
    severity: str
    description: str
    location: Optional[str] = None
    category: Optional[str] = None
    finding_id: Optional[str] = None
    discovered_at: Optional[str] = None
    discovered_in_step: Optional[int] = None
    remediation: Optional[str] = None
    cwe_id: Optional[str] = None

    @classmethod
    def from_finding(cls, finding: dict) -> "IssueSummary":
        """Create IssueSummary from finding dict."""
        severity = finding.get("severity", "info")
        if isinstance(severity, str):
            severity = severity.lower()
        else:
            severity = "info"

        location = finding.get("location") or finding.get("file_path")
        if not location:
            affected_files = finding.get("affected_files", [])
            if affected_files and isinstance(affected_files, list):
                first_file = affected_files[0]
                if isinstance(first_file, dict):
                    location = first_file.get("file_path") or first_file.get("path")
                elif isinstance(first_file, str):
                    location = first_file

        return cls(
            severity=severity,
            description=finding.get("description", str(finding)),
            location=location,
            category=finding.get("category"),
            finding_id=finding.get("finding_id"),
            discovered_at=finding.get("discovered_at"),
            discovered_in_step=finding.get("discovered_in_step"),
            remediation=finding.get("remediation"),
            cwe_id=finding.get("cwe_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WorkflowSummary:
    """Summary projection of a WorkflowState for dashboard display."""
    id: str
    audit_type: str
    status: str
    current_step: int
    total_steps: int
    progress_percent: float
    confidence: str
    findings_count: int
    files_checked_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_state(cls, state: WorkflowState, status: str) -> "WorkflowSummary":
        """Create WorkflowSummary from WorkflowState."""
        total_steps = AUDIT_TOTAL_STEPS.get(state.tool_name, 6)
        current_step = max((s.step_number for s in state.step_history), default=0)
        progress = min(100.0, (current_step / total_steps) * 100)

        findings_count = 0
        files_checked_count = 0
        if state.consolidated is not None:
            issues = getattr(state.consolidated, "issues_found", [])
            findings_count = len(issues) if issues else 0
            files = getattr(state.consolidated, "files_checked", [])
            files_checked_count = len(files) if files else 0

        return cls(
            id=state.continuation_id,
            audit_type=state.tool_name,
            status=status,
            current_step=current_step,
            total_steps=total_steps,
            progress_percent=progress,
            confidence=state.get_latest_confidence().value,
            findings_count=findings_count,
            files_checked_count=files_checked_count,
            created_at=state.created_at.isoformat(),
            updated_at=state.updated_at.isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WorkflowDetail:
    """Full workflow details including step history and issues."""
    id: str
    audit_type: str
    status: str
    current_step: int
    total_steps: int
    progress_percent: float
    confidence: str
    findings_count: int
    files_checked_count: int
    created_at: str
    updated_at: str
    project_root_path: Optional[str]
    step_history: list[StepSummary]
    issues: list[IssueSummary]
    files_checked: list[str]

    @classmethod
    def from_state(cls, state: WorkflowState, status: str) -> "WorkflowDetail":
        """Create WorkflowDetail from WorkflowState."""
        total_steps = AUDIT_TOTAL_STEPS.get(state.tool_name, 6)
        current_step = max((s.step_number for s in state.step_history), default=0)
        progress = min(100.0, (current_step / total_steps) * 100)

        findings_count = 0
        files_checked: list[str] = []
        issues: list[IssueSummary] = []

        if state.consolidated is not None:
            issues_found = getattr(state.consolidated, "issues_found", [])
            findings_count = len(issues_found) if issues_found else 0
            issues = [IssueSummary.from_finding(f) for f in (issues_found or [])]
            files = getattr(state.consolidated, "files_checked", [])
            files_checked = list(files) if files else []

        step_history = [StepSummary.from_step(s) for s in state.step_history]

        step_numbers = [s.step_number for s in step_history]
        if len(step_numbers) != len(set(step_numbers)):
            import logging
            logging.getLogger("dashboard").warning(
                f"Duplicate step_numbers detected in workflow {state.continuation_id}: {step_numbers}"
            )

        return cls(
            id=state.continuation_id,
            audit_type=state.tool_name,
            status=status,
            current_step=current_step,
            total_steps=total_steps,
            progress_percent=progress,
            confidence=state.get_latest_confidence().value,
            findings_count=findings_count,
            files_checked_count=len(files_checked),
            created_at=state.created_at.isoformat(),
            updated_at=state.updated_at.isoformat(),
            project_root_path=state.project_root_path,
            step_history=step_history,
            issues=issues,
            files_checked=files_checked,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "audit_type": self.audit_type,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percent": self.progress_percent,
            "confidence": self.confidence,
            "findings_count": self.findings_count,
            "files_checked_count": self.files_checked_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_root_path": self.project_root_path,
            "step_history": [s.to_dict() for s in self.step_history],
            "issues": [i.to_dict() for i in self.issues],
            "files_checked": self.files_checked,
        }
        return result


@dataclass
class ReportSummary:
    """Summary of a generated audit report file."""
    filename: str
    audit_type: str
    size: int
    size_formatted: str
    created_at: str

    @classmethod
    def from_file(cls, file_path: Path) -> "ReportSummary":
        """Create ReportSummary from file path."""
        stat = file_path.stat()
        return cls(
            filename=file_path.name,
            audit_type=infer_audit_type(file_path.name),
            size=stat.st_size,
            size_formatted=format_file_size(stat.st_size),
            created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class HealthResponse:
    """Server health information for dashboard display."""
    status: str
    server_name: str
    version: str
    uptime_seconds: float
    uptime_formatted: str
    tools_available: list[str]
    active_workflow_count: int

    @classmethod
    def from_health_check(
        cls,
        status: str,
        server_name: str,
        version: str,
        uptime_seconds: float,
        tools_available: list[str],
        active_workflow_count: int,
    ) -> "HealthResponse":
        """Create HealthResponse from health check data."""
        return cls(
            status=status,
            server_name=server_name,
            version=version,
            uptime_seconds=uptime_seconds,
            uptime_formatted=format_uptime(uptime_seconds),
            tools_available=tools_available,
            active_workflow_count=active_workflow_count,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WorkflowDebugDetail:
    """Raw workflow state details for debugging purposes."""
    id: str
    tool_name: str
    is_finished: bool
    created_at: str
    updated_at: str
    project_root_path: Optional[str]
    step_history_raw: list[dict[str, Any]]
    consolidated_raw: Optional[dict[str, Any]]

    @classmethod
    def from_state(cls, state: WorkflowState) -> "WorkflowDebugDetail":
        """Create WorkflowDebugDetail from WorkflowState."""
        consolidated_raw = None
        if state.consolidated and hasattr(state.consolidated, "to_dict"):
            consolidated_raw = state.consolidated.to_dict()

        return cls(
            id=state.continuation_id,
            tool_name=state.tool_name,
            is_finished=state.is_finished,
            created_at=state.created_at.isoformat(),
            updated_at=state.updated_at.isoformat(),
            project_root_path=state.project_root_path,
            step_history_raw=[s.to_dict() for s in state.step_history],
            consolidated_raw=consolidated_raw,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
