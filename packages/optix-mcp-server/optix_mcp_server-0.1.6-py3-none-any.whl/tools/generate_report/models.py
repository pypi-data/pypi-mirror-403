"""Data models for the generate_report tool.

Provides type-safe entities for report generation including:
- AuditLens enum for lens identification
- ReportMetadata for report metadata
- Response/Error dataclasses for MCP responses
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class AuditLens(str, Enum):
    """Supported audit lens types."""

    SECURITY = "SECURITY"
    A11Y = "A11Y"
    PRINCIPAL = "PRINCIPAL"
    DEVOPS = "DEVOPS"

    @property
    def tool_name(self) -> str:
        """Get the corresponding tool name."""
        mapping = {
            AuditLens.SECURITY: "security_audit",
            AuditLens.A11Y: "a11y_audit",
            AuditLens.PRINCIPAL: "principal_audit",
            AuditLens.DEVOPS: "devops_audit",
        }
        return mapping[self]

    @classmethod
    def from_tool_name(cls, tool_name: str) -> "AuditLens":
        """Convert tool name to AuditLens.

        Args:
            tool_name: The audit tool name (e.g., "security_audit")

        Returns:
            Corresponding AuditLens enum value

        Raises:
            ValueError: If tool_name is not recognized
        """
        mapping = {
            "security_audit": cls.SECURITY,
            "a11y_audit": cls.A11Y,
            "principal_audit": cls.PRINCIPAL,
            "devops_audit": cls.DEVOPS,
        }
        if tool_name not in mapping:
            valid_tools = ", ".join(mapping.keys())
            raise ValueError(
                f"Unknown tool name: {tool_name}. Expected one of: {valid_tools}"
            )
        return mapping[tool_name]


@dataclass
class ReportMetadata:
    """Metadata for a generated audit report."""

    lens: AuditLens
    report_number: int
    report_path: Path
    generated_at: datetime
    project_name: str = "Unknown Project"

    def to_dict(self) -> dict:
        """Convert metadata to dictionary for JSON serialization."""
        return {
            "lens": self.lens.value,
            "report_number": self.report_number,
            "report_path": str(self.report_path),
            "generated_at": self.generated_at.isoformat(),
            "project_name": self.project_name,
        }

    @property
    def filename(self) -> str:
        """Get the report filename."""
        return f"{self.lens.value}_AUDIT_REPORT_{self.report_number}.md"


@dataclass
class ReportGenerationResponse:
    """Response from successful report generation."""

    success: bool
    report_path: Path
    report_number: int
    lens: AuditLens
    message: str
    severity_counts: dict[str, int] = field(default_factory=dict)
    files_examined: int = 0

    def to_dict(self) -> dict:
        """Convert response to dictionary for MCP JSON response."""
        return {
            "success": self.success,
            "report_path": str(self.report_path),
            "report_number": self.report_number,
            "lens": self.lens.value,
            "message": self.message,
            "severity_counts": self.severity_counts,
            "files_examined": self.files_examined,
        }


@dataclass
class ReportGenerationError:
    """Response from failed report generation."""

    success: bool = False
    error: str = ""
    error_type: str = "GeneralError"

    def to_dict(self) -> dict:
        """Convert error to dictionary for MCP JSON response."""
        return {
            "success": self.success,
            "error": self.error,
            "error_type": self.error_type,
        }
