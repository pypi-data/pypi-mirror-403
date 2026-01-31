"""Finding-related dataclasses for Principal Engineer Audit Tool."""

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.principal_audit.category import FindingCategory
from tools.principal_audit.severity import Severity
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings


def transform_legacy_finding_format(data: dict[str, Any]) -> dict[str, Any]:
    """Transform legacy finding format to current format.

    Handles data from clients that use different field names:
    - "finding" → "description"
    - "recommendation" → "remediation"
    - "file_path" + "line_number" → "affected_files" array
    - "file" → "file_path" (alias)
    - "line_range" → "line_start" + "line_end" (parsed from "10-20" format)
    - "title" → merged into "description"
    - Adds default "confidence" if missing

    Args:
        data: Finding data in legacy or current format

    Returns:
        Finding data in current expected format
    """
    # Return as-is if already in COMPLETE correct format
    # Must have category (not just "type") to be considered complete
    if "description" in data and "affected_files" in data and "category" in data:
        return data

    transformed = data.copy()

    # Handle "type" as alias for "category"
    if "type" in transformed and "category" not in transformed:
        transformed["category"] = transformed.pop("type")

    # Transform field names
    if "finding" in transformed:
        transformed["description"] = transformed.pop("finding")

    if "recommendation" in transformed:
        transformed["remediation"] = transformed.pop("recommendation")

    # Handle "file" as alias for "file_path"
    if "file" in transformed and "file_path" not in transformed:
        file_value = transformed.pop("file")
        # Only use if it's a real file path (not "General" or "N/A")
        if file_value and file_value.lower() not in ("general", "n/a"):
            transformed["file_path"] = file_value

    # Handle "line" as alias for "line_range" (e.g., "321-571")
    if "line" in transformed and "line_range" not in transformed:
        transformed["line_range"] = transformed.pop("line")

    # Handle "line_range" as alias for line info (e.g., "100-150" or "N/A")
    if "line_range" in transformed:
        line_range = transformed.pop("line_range")
        # Only parse if it's a real value (not "N/A")
        if line_range and str(line_range).lower() not in ("n/a",):
            line_range_str = str(line_range)
            if "-" in line_range_str:
                parts = line_range_str.split("-")
                if len(parts) == 2:
                    try:
                        transformed["line_start"] = int(parts[0].strip())
                        transformed["line_end"] = int(parts[1].strip())
                    except ValueError:
                        pass
            else:
                try:
                    transformed["line_number"] = int(line_range_str)
                except ValueError:
                    pass

    # Handle "title" - merge into description if description exists,
    # otherwise use as description
    if "title" in transformed:
        title = transformed.pop("title")
        if title:
            if "description" in transformed and transformed["description"]:
                transformed["description"] = f"{title}: {transformed['description']}"
            elif not transformed.get("description"):
                transformed["description"] = title

    # Transform file location to affected_files array
    if "file_path" in transformed and "affected_files" not in transformed:
        affected_file = {"file_path": transformed.pop("file_path")}

        if "line_number" in transformed:
            line_num = transformed.pop("line_number")
            affected_file["line_start"] = line_num

        if "line_start" in transformed:
            affected_file["line_start"] = transformed.pop("line_start")

        if "line_end" in transformed:
            affected_file["line_end"] = transformed.pop("line_end")

        if "function_name" in transformed:
            affected_file["function_name"] = transformed.pop("function_name")

        transformed["affected_files"] = [affected_file]

    # If still no affected_files, create a placeholder
    if "affected_files" not in transformed:
        # Clean up any remaining line info that wasn't used
        transformed.pop("line_start", None)
        transformed.pop("line_end", None)
        transformed.pop("line_number", None)
        transformed.pop("function_name", None)
        transformed["affected_files"] = [{"file_path": "general"}]

    # Add default confidence if missing
    if "confidence" not in transformed:
        # Default to "high" for now - could be smarter based on severity
        transformed["confidence"] = "high"

    # Remove extra fields that aren't part of the schema
    if "explanation" in transformed:
        # Append explanation to description if present
        if transformed.get("description"):
            transformed["description"] = f"{transformed['description']}. {transformed['explanation']}"
        transformed.pop("explanation")

    return transformed


def normalize_category(category: str) -> str:
    """Normalize category string to valid FindingCategory value.

    Handles common variations and mappings from LLM responses to
    ensure category strings match the FindingCategory enum values.

    Args:
        category: Raw category string (e.g., from LLM or user input)

    Returns:
        Valid FindingCategory value string

    Raises:
        ValueError: If category cannot be normalized to a valid value
    """
    normalized = category.lower().strip().replace("-", "_").replace(" ", "_")

    category_map = {
        "complexity": "complexity",
        "dry_violation": "dry_violation",
        "dry": "dry_violation",
        "duplication": "dry_violation",
        "coupling": "coupling",
        "separation_of_concerns": "separation_of_concerns",
        "separation": "separation_of_concerns",
        "maintainability_risk": "maintainability_risk",
        "maintainability": "maintainability_risk",
    }

    if normalized in category_map:
        return category_map[normalized]

    raise ValueError(
        f"'{category}' cannot be mapped to a valid FindingCategory. "
        f"Valid categories: {', '.join(category_map.values())}"
    )


@dataclass
class AffectedFile:
    """A file affected by a code quality finding.

    Attributes:
        file_path: Relative path from project root
        line_start: Starting line number (optional for file-level findings)
        line_end: Ending line number (optional)
        function_name: Function/method name if applicable
        snippet: Code snippet for context (optional)
    """

    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    function_name: Optional[str] = None
    snippet: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "function_name": self.function_name,
            "snippet": self.snippet,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AffectedFile":
        """Create from dictionary."""
        return cls(
            file_path=data["file_path"],
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
            function_name=data.get("function_name"),
            snippet=data.get("snippet"),
        )


@dataclass
class CouplingMetrics:
    """Coupling metrics for architectural analysis.

    Attributes:
        afferent_coupling: Number of incoming dependencies (Ca)
        efferent_coupling: Number of outgoing dependencies (Ce)
        instability: I = Ce / (Ca + Ce), range [0, 1] (optional)
        module_name: Module or package name (optional)
        dependency_count: Total dependency count (optional)
    """

    afferent_coupling: int
    efferent_coupling: int
    instability: Optional[float] = None
    module_name: Optional[str] = None
    dependency_count: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "afferent_coupling": self.afferent_coupling,
            "efferent_coupling": self.efferent_coupling,
            "instability": self.instability,
            "module_name": self.module_name,
            "dependency_count": self.dependency_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CouplingMetrics":
        """Create from dictionary.

        Handles both full field names (afferent_coupling, efferent_coupling)
        and shorthand aliases (afferent, efferent).
        """
        return cls(
            afferent_coupling=data.get("afferent_coupling") or data.get("afferent", 0),
            efferent_coupling=data.get("efferent_coupling") or data.get("efferent", 0),
            instability=data.get("instability"),
            module_name=data.get("module_name"),
            dependency_count=data.get("dependency_count"),
        )


@dataclass
class LLMAssessment:
    """Assessment from a single LLM provider.

    Attributes:
        provider: LLM provider name (openai, anthropic, gemini)
        model: Specific model version
        severity: Assessed severity
        confidence: LLM's confidence in assessment
        reasoning: Explanation for assessment
    """

    provider: str
    model: str
    severity: Severity
    confidence: ConfidenceLevel
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider": self.provider,
            "model": self.model,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "reasoning": self.reasoning,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMAssessment":
        """Create from dictionary."""
        return cls(
            provider=data["provider"],
            model=data["model"],
            severity=Severity(data["severity"]),
            confidence=ConfidenceLevel(data["confidence"]),
            reasoning=data["reasoning"],
        )


@dataclass
class PrincipalEngineerFinding:
    """A code quality or architectural finding.

    Attributes:
        category: Finding category (complexity, DRY, coupling, etc.)
        severity: Impact level of the finding
        description: Clear issue description
        affected_files: Files with line numbers
        remediation: Recommended refactoring approach
        confidence: Confidence in this finding
        llm_assessments: Multi-LLM validation results (optional)
        complexity_score: McCabe score for COMPLEXITY findings
        similarity_percentage: Percentage for DRY_VIOLATION findings
        coupling_metrics: Metrics for COUPLING findings
    """

    category: FindingCategory
    severity: Severity
    description: str
    affected_files: list[AffectedFile]
    remediation: str
    confidence: ConfidenceLevel
    llm_assessments: Optional[list[LLMAssessment]] = None
    complexity_score: Optional[float] = None
    similarity_percentage: Optional[float] = None
    coupling_metrics: Optional[CouplingMetrics] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "affected_files": [f.to_dict() for f in self.affected_files],
            "remediation": self.remediation,
            "confidence": self.confidence.value,
            "llm_assessments": [a.to_dict() for a in (self.llm_assessments or [])],
            "complexity_score": self.complexity_score,
            "similarity_percentage": self.similarity_percentage,
            "coupling_metrics": self.coupling_metrics.to_dict() if self.coupling_metrics else None,
        }

    @classmethod
    def validate_dict(cls, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate finding dict has required fields.

        Returns:
            Tuple of (is_valid, missing_fields)
        """
        required = ["category", "severity", "description", "affected_files", "remediation", "confidence"]
        missing = [f for f in required if f not in data]
        return (len(missing) == 0, missing)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrincipalEngineerFinding":
        """Create from dictionary.

        Args:
            data: Dictionary with finding data. Must include 'category', 'severity',
                  'description', 'affected_files', 'remediation', and 'confidence'.
                  Also accepts legacy format with 'finding', 'recommendation', 'file_path'.

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Transform legacy format to current format
        data = transform_legacy_finding_format(data)

        if "category" not in data:
            raise KeyError(
                f"Missing required field 'category'. Available fields: {list(data.keys())}"
            )

        if "description" not in data:
            raise KeyError(
                f"Missing required field 'description'. Available fields: {list(data.keys())}"
            )

        if "affected_files" not in data:
            raise KeyError(
                f"Missing required field 'affected_files'. Available fields: {list(data.keys())}"
            )

        if "remediation" not in data:
            raise KeyError(
                f"Missing required field 'remediation'. Available fields: {list(data.keys())}"
            )

        llm_assessments = None
        if data.get("llm_assessments"):
            llm_assessments = [LLMAssessment.from_dict(a) for a in data["llm_assessments"]]

        coupling_metrics = None
        if data.get("coupling_metrics"):
            coupling_metrics = CouplingMetrics.from_dict(data["coupling_metrics"])

        category_str = normalize_category(data["category"])

        return cls(
            category=FindingCategory(category_str),
            severity=Severity(data["severity"]),
            description=data["description"],
            affected_files=[AffectedFile.from_dict(f) for f in data["affected_files"]],
            remediation=data["remediation"],
            confidence=ConfidenceLevel(data["confidence"]),
            llm_assessments=llm_assessments,
            complexity_score=data.get("complexity_score"),
            similarity_percentage=data.get("similarity_percentage"),
            coupling_metrics=coupling_metrics,
        )


@dataclass
class ConsolidatedPrincipalFindings(ConsolidatedFindings):
    """Consolidated findings from Principal Engineer audit workflow.

    Extends ConsolidatedFindings with category-specific collections
    and file tracking by priority tier.
    """

    complexity_findings: list[PrincipalEngineerFinding] = field(default_factory=list)
    dry_violations: list[PrincipalEngineerFinding] = field(default_factory=list)
    coupling_issues: list[PrincipalEngineerFinding] = field(default_factory=list)
    separation_of_concerns_issues: list[PrincipalEngineerFinding] = field(default_factory=list)
    maintainability_risks: list[PrincipalEngineerFinding] = field(default_factory=list)

    files_analyzed: list[str] = field(default_factory=list)
    files_omitted: list[str] = field(default_factory=list)

    omitted_priority_1: list[str] = field(default_factory=list)
    omitted_priority_2: list[str] = field(default_factory=list)
    omitted_priority_3: list[str] = field(default_factory=list)

    requested_context: list[str] = field(default_factory=list)
    provided_context: list[str] = field(default_factory=list)

    def add_step(self, step_data: Any) -> None:
        """Merge step data into consolidated state.

        Extends parent to also populate files_analyzed for consistency.
        """
        super().add_step(step_data)
        for f in step_data.files_checked:
            if f not in self.files_analyzed:
                self.files_analyzed.append(f)

    def add_issue(self, issue_dict: dict[str, Any]) -> None:
        """Add a finding to the appropriate category collection with deduplication.

        Args:
            issue_dict: Dictionary representation of a PrincipalEngineerFinding
        """
        finding = PrincipalEngineerFinding.from_dict(issue_dict)

        def is_duplicate(existing_list: list[PrincipalEngineerFinding]) -> bool:
            for existing in existing_list:
                if (existing.description == finding.description and
                        existing.severity == finding.severity):
                    return True
            return False

        if finding.category == FindingCategory.COMPLEXITY:
            if not is_duplicate(self.complexity_findings):
                self.complexity_findings.append(finding)
        elif finding.category == FindingCategory.DRY_VIOLATION:
            if not is_duplicate(self.dry_violations):
                self.dry_violations.append(finding)
        elif finding.category == FindingCategory.COUPLING:
            if not is_duplicate(self.coupling_issues):
                self.coupling_issues.append(finding)
        elif finding.category == FindingCategory.SEPARATION_OF_CONCERNS:
            if not is_duplicate(self.separation_of_concerns_issues):
                self.separation_of_concerns_issues.append(finding)
        elif finding.category == FindingCategory.MAINTAINABILITY_RISK:
            if not is_duplicate(self.maintainability_risks):
                self.maintainability_risks.append(finding)

        super()._add_issue_if_unique(issue_dict)

    def get_all_findings(self) -> list[PrincipalEngineerFinding]:
        """Get all findings across all categories.

        Returns:
            List of all PrincipalEngineerFinding objects
        """
        return (
            self.complexity_findings
            + self.dry_violations
            + self.coupling_issues
            + self.separation_of_concerns_issues
            + self.maintainability_risks
        )

    def get_findings_by_severity(self) -> dict[str, list[PrincipalEngineerFinding]]:
        """Group findings by severity level.

        Returns:
            Dictionary mapping severity name to list of findings
        """
        all_findings = self.get_all_findings()
        return {
            "critical": [f for f in all_findings if f.severity == Severity.CRITICAL],
            "high": [f for f in all_findings if f.severity == Severity.HIGH],
            "medium": [f for f in all_findings if f.severity == Severity.MEDIUM],
            "low": [f for f in all_findings if f.severity == Severity.LOW],
            "info": [f for f in all_findings if f.severity == Severity.INFO],
        }

    def get_audit_summary(self) -> dict[str, Any]:
        """Generate summary for audit report.

        Returns:
            Dictionary with audit summary data
        """
        by_severity = self.get_findings_by_severity()
        total_files = len(self.files_analyzed)
        omitted_files = len(self.files_omitted)

        return {
            "total_findings": len(self.get_all_findings()),
            "severity_counts": {
                "critical": len(by_severity["critical"]),
                "high": len(by_severity["high"]),
                "medium": len(by_severity["medium"]),
                "low": len(by_severity["low"]),
                "info": len(by_severity["info"]),
            },
            "files_examined": total_files,
            "files_omitted": omitted_files,
            "summary_text": (
                f"Analyzed {total_files} files, omitted {omitted_files} files. "
                f"Found {len(by_severity['critical'])} CRITICAL, {len(by_severity['high'])} HIGH, "
                f"{len(by_severity['medium'])} MEDIUM, {len(by_severity['low'])} LOW, "
                f"{len(by_severity['info'])} INFO severity findings."
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of consolidated findings
        """
        base_dict = super().to_dict()
        base_dict.update({
            "complexity_findings": [f.to_dict() for f in self.complexity_findings],
            "dry_violations": [f.to_dict() for f in self.dry_violations],
            "coupling_issues": [f.to_dict() for f in self.coupling_issues],
            "separation_of_concerns_issues": [f.to_dict() for f in self.separation_of_concerns_issues],
            "maintainability_risks": [f.to_dict() for f in self.maintainability_risks],
            "files_analyzed": self.files_analyzed,
            "files_omitted": self.files_omitted,
            "omitted_priority_1": self.omitted_priority_1,
            "omitted_priority_2": self.omitted_priority_2,
            "omitted_priority_3": self.omitted_priority_3,
            "requested_context": self.requested_context,
            "provided_context": self.provided_context,
        })
        return base_dict
