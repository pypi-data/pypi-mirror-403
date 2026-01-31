"""SecurityFinding dataclass for vulnerability representation."""

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.security_audit.severity import Severity


@dataclass
class SecurityFinding:
    """Represents a discovered security vulnerability."""

    severity: Severity
    category: str
    description: str
    affected_files: list[str] = field(default_factory=list)
    remediation: Optional[str] = None
    cwe_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecurityFinding":
        """Create SecurityFinding from dictionary.

        Args:
            data: Dictionary with finding data

        Returns:
            SecurityFinding instance
        """
        severity = data.get("severity", "medium")
        if isinstance(severity, str):
            severity = Severity.from_string(severity)

        return cls(
            severity=severity,
            category=data.get("category", "Unknown"),
            description=data.get("description", ""),
            affected_files=data.get("affected_files", []),
            remediation=data.get("remediation"),
            cwe_id=data.get("cwe_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with finding data
        """
        result = {
            "severity": self.severity.value,
            "category": self.category,
            "description": self.description,
            "affected_files": self.affected_files,
        }
        if self.remediation:
            result["remediation"] = self.remediation
        if self.cwe_id:
            result["cwe_id"] = self.cwe_id
        return result
