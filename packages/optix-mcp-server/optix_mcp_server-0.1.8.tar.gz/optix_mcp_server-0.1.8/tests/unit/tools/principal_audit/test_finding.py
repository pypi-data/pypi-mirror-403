"""Tests for finding-related dataclasses."""

import pytest

from tools.principal_audit.category import FindingCategory
from tools.principal_audit.finding import (
    AffectedFile,
    ConsolidatedPrincipalFindings,
    CouplingMetrics,
    PrincipalEngineerFinding,
    normalize_category,
    transform_legacy_finding_format,
)
from tools.principal_audit.severity import Severity
from tools.workflow.confidence import ConfidenceLevel


class TestAffectedFile:
    """Test suite for AffectedFile dataclass."""

    def test_create_minimal(self):
        """Should create AffectedFile with only required fields."""
        af = AffectedFile(file_path="src/main.py")
        assert af.file_path == "src/main.py"
        assert af.line_start is None
        assert af.line_end is None
        assert af.function_name is None
        assert af.snippet is None

    def test_create_full(self):
        """Should create AffectedFile with all fields."""
        af = AffectedFile(
            file_path="src/main.py",
            line_start=10,
            line_end=25,
            function_name="process_data",
            snippet="def process_data():\n    pass",
        )
        assert af.file_path == "src/main.py"
        assert af.line_start == 10
        assert af.line_end == 25
        assert af.function_name == "process_data"
        assert af.snippet == "def process_data():\n    pass"

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        af = AffectedFile(
            file_path="src/main.py",
            line_start=10,
            line_end=25,
            function_name="process_data",
        )
        result = af.to_dict()
        assert result["file_path"] == "src/main.py"
        assert result["line_start"] == 10
        assert result["line_end"] == 25
        assert result["function_name"] == "process_data"
        assert result["snippet"] is None

    def test_from_dict(self):
        """Should create from dictionary correctly."""
        data = {
            "file_path": "src/main.py",
            "line_start": 10,
            "line_end": 25,
            "function_name": "process_data",
            "snippet": None,
        }
        af = AffectedFile.from_dict(data)
        assert af.file_path == "src/main.py"
        assert af.line_start == 10
        assert af.line_end == 25

    def test_from_dict_minimal(self):
        """Should create from dictionary with only required fields."""
        data = {"file_path": "src/main.py"}
        af = AffectedFile.from_dict(data)
        assert af.file_path == "src/main.py"
        assert af.line_start is None


class TestCouplingMetrics:
    """Test suite for CouplingMetrics dataclass."""

    def test_create(self):
        """Should create CouplingMetrics with all fields."""
        cm = CouplingMetrics(
            afferent_coupling=3,
            efferent_coupling=8,
            instability=0.73,
            module_name="UserService",
            dependency_count=8,
        )
        assert cm.afferent_coupling == 3
        assert cm.efferent_coupling == 8
        assert cm.instability == 0.73
        assert cm.module_name == "UserService"
        assert cm.dependency_count == 8

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        cm = CouplingMetrics(
            afferent_coupling=3,
            efferent_coupling=8,
            instability=0.73,
            module_name="UserService",
            dependency_count=8,
        )
        result = cm.to_dict()
        assert result["afferent_coupling"] == 3
        assert result["efferent_coupling"] == 8
        assert result["instability"] == 0.73
        assert result["module_name"] == "UserService"
        assert result["dependency_count"] == 8

    def test_from_dict(self):
        """Should create from dictionary correctly."""
        data = {
            "afferent_coupling": 3,
            "efferent_coupling": 8,
            "instability": 0.73,
            "module_name": "UserService",
            "dependency_count": 8,
        }
        cm = CouplingMetrics.from_dict(data)
        assert cm.afferent_coupling == 3
        assert cm.efferent_coupling == 8
        assert cm.instability == 0.73

    def test_create_with_optional_fields(self):
        """Should create CouplingMetrics with only required fields."""
        cm = CouplingMetrics(
            afferent_coupling=5,
            efferent_coupling=3,
        )
        assert cm.afferent_coupling == 5
        assert cm.efferent_coupling == 3
        assert cm.instability is None
        assert cm.module_name is None
        assert cm.dependency_count is None

    def test_from_dict_partial_fields(self):
        """Should create from dictionary with only required fields."""
        data = {
            "afferent_coupling": 5,
            "efferent_coupling": 3,
        }
        cm = CouplingMetrics.from_dict(data)
        assert cm.afferent_coupling == 5
        assert cm.efferent_coupling == 3
        assert cm.instability is None
        assert cm.module_name is None
        assert cm.dependency_count is None

    def test_from_dict_with_alias_fields(self):
        """Should handle afferent/efferent aliases."""
        data = {
            "afferent": 1,
            "efferent": 1,
        }
        cm = CouplingMetrics.from_dict(data)
        assert cm.afferent_coupling == 1
        assert cm.efferent_coupling == 1

    def test_from_dict_full_names_take_precedence_over_aliases(self):
        """Full field names should take precedence over aliases."""
        data = {
            "afferent_coupling": 5,
            "efferent_coupling": 3,
            "afferent": 1,
            "efferent": 1,
        }
        cm = CouplingMetrics.from_dict(data)
        assert cm.afferent_coupling == 5
        assert cm.efferent_coupling == 3


class TestPrincipalEngineerFinding:
    """Test suite for PrincipalEngineerFinding dataclass."""

    def test_create_minimal(self):
        """Should create finding with required fields."""
        finding = PrincipalEngineerFinding(
            category=FindingCategory.COMPLEXITY,
            severity=Severity.HIGH,
            description="Function too complex",
            affected_files=[AffectedFile(file_path="src/main.py")],
            remediation="Split into smaller functions",
            confidence=ConfidenceLevel.HIGH,
        )
        assert finding.category == FindingCategory.COMPLEXITY
        assert finding.severity == Severity.HIGH
        assert finding.description == "Function too complex"
        assert len(finding.affected_files) == 1
        assert finding.remediation == "Split into smaller functions"
        assert finding.confidence == ConfidenceLevel.HIGH
        assert finding.llm_assessments is None
        assert finding.complexity_score is None

    def test_create_with_complexity_score(self):
        """Should create complexity finding with score."""
        finding = PrincipalEngineerFinding(
            category=FindingCategory.COMPLEXITY,
            severity=Severity.HIGH,
            description="Function too complex",
            affected_files=[AffectedFile(file_path="src/main.py", function_name="process")],
            remediation="Split into smaller functions",
            confidence=ConfidenceLevel.HIGH,
            complexity_score=23.0,
        )
        assert finding.complexity_score == 23.0

    def test_create_with_similarity_percentage(self):
        """Should create DRY finding with similarity percentage."""
        finding = PrincipalEngineerFinding(
            category=FindingCategory.DRY_VIOLATION,
            severity=Severity.MEDIUM,
            description="Duplicated validation logic",
            affected_files=[
                AffectedFile(file_path="src/a.py"),
                AffectedFile(file_path="src/b.py"),
            ],
            remediation="Extract to shared utility",
            confidence=ConfidenceLevel.HIGH,
            similarity_percentage=87.5,
        )
        assert finding.similarity_percentage == 87.5

    def test_create_with_coupling_metrics(self):
        """Should create coupling finding with metrics."""
        metrics = CouplingMetrics(
            afferent_coupling=2,
            efferent_coupling=8,
            instability=0.8,
            module_name="UserService",
            dependency_count=8,
        )
        finding = PrincipalEngineerFinding(
            category=FindingCategory.COUPLING,
            severity=Severity.CRITICAL,
            description="High coupling detected",
            affected_files=[AffectedFile(file_path="src/user_service.py")],
            remediation="Apply dependency injection",
            confidence=ConfidenceLevel.HIGH,
            coupling_metrics=metrics,
        )
        assert finding.coupling_metrics is not None
        assert finding.coupling_metrics.efferent_coupling == 8

    def test_create_with_info_severity(self):
        """Should create finding with INFO severity."""
        finding = PrincipalEngineerFinding(
            category=FindingCategory.MAINTAINABILITY_RISK,
            severity=Severity.INFO,
            description="Good separation of concerns observed",
            affected_files=[AffectedFile(file_path="src/clean.py")],
            remediation="Keep this pattern",
            confidence=ConfidenceLevel.HIGH,
        )
        assert finding.severity == Severity.INFO
        assert finding.severity.numeric_value() == 0.0

    def test_create_with_partial_coupling_metrics(self):
        """Should create coupling finding with only required metrics."""
        metrics = CouplingMetrics(
            afferent_coupling=5,
            efferent_coupling=3,
        )
        finding = PrincipalEngineerFinding(
            category=FindingCategory.COUPLING,
            severity=Severity.MEDIUM,
            description="Moderate coupling",
            affected_files=[AffectedFile(file_path="src/service.py")],
            remediation="Monitor coupling",
            confidence=ConfidenceLevel.MEDIUM,
            coupling_metrics=metrics,
        )
        assert finding.coupling_metrics is not None
        assert finding.coupling_metrics.afferent_coupling == 5
        assert finding.coupling_metrics.efferent_coupling == 3
        assert finding.coupling_metrics.instability is None
        assert finding.coupling_metrics.module_name is None

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        finding = PrincipalEngineerFinding(
            category=FindingCategory.COMPLEXITY,
            severity=Severity.HIGH,
            description="Function too complex",
            affected_files=[AffectedFile(file_path="src/main.py", line_start=10)],
            remediation="Split into smaller functions",
            confidence=ConfidenceLevel.HIGH,
            complexity_score=23.0,
        )
        result = finding.to_dict()
        assert result["category"] == "complexity"
        assert result["severity"] == "high"
        assert result["description"] == "Function too complex"
        assert result["complexity_score"] == 23.0
        assert len(result["affected_files"]) == 1
        assert result["affected_files"][0]["file_path"] == "src/main.py"

    def test_from_dict(self):
        """Should create from dictionary correctly."""
        data = {
            "category": "complexity",
            "severity": "high",
            "description": "Function too complex",
            "affected_files": [{"file_path": "src/main.py", "line_start": 10}],
            "remediation": "Split into smaller functions",
            "confidence": "high",
            "llm_assessments": [],
            "complexity_score": 23.0,
            "similarity_percentage": None,
            "coupling_metrics": None,
        }
        finding = PrincipalEngineerFinding.from_dict(data)
        assert finding.category == FindingCategory.COMPLEXITY
        assert finding.severity == Severity.HIGH
        assert finding.complexity_score == 23.0

    def test_from_dict_with_info_severity(self):
        """Should create from dictionary with INFO severity."""
        data = {
            "category": "maintainability_risk",
            "severity": "info",
            "description": "Good pattern: Clean separation of concerns",
            "affected_files": [{"file_path": "src/clean.py"}],
            "remediation": "Maintain this pattern",
            "confidence": "high",
        }
        finding = PrincipalEngineerFinding.from_dict(data)
        assert finding.severity == Severity.INFO
        assert finding.severity.value == "info"

    def test_from_dict_with_partial_coupling_metrics(self):
        """Should create from dictionary with partial coupling_metrics."""
        data = {
            "category": "coupling",
            "severity": "medium",
            "description": "Singleton pattern detected",
            "affected_files": [{"file_path": "src/manager.py"}],
            "remediation": "Consider dependency injection",
            "confidence": "high",
            "coupling_metrics": {
                "afferent_coupling": 5,
                "efferent_coupling": 2,
            },
        }
        finding = PrincipalEngineerFinding.from_dict(data)
        assert finding.coupling_metrics is not None
        assert finding.coupling_metrics.afferent_coupling == 5
        assert finding.coupling_metrics.efferent_coupling == 2
        assert finding.coupling_metrics.instability is None
        assert finding.coupling_metrics.module_name is None
        assert finding.coupling_metrics.dependency_count is None

    def test_to_dict_from_dict_roundtrip(self):
        """Should survive roundtrip conversion."""
        original = PrincipalEngineerFinding(
            category=FindingCategory.COUPLING,
            severity=Severity.CRITICAL,
            description="Circular dependency",
            affected_files=[
                AffectedFile(file_path="src/a.py"),
                AffectedFile(file_path="src/b.py"),
            ],
            remediation="Break cycle with events",
            confidence=ConfidenceLevel.VERY_HIGH,
            coupling_metrics=CouplingMetrics(
                afferent_coupling=2,
                efferent_coupling=5,
                instability=0.71,
                module_name="ServiceA",
                dependency_count=5,
            ),
        )
        data = original.to_dict()
        restored = PrincipalEngineerFinding.from_dict(data)
        assert restored.category == original.category
        assert restored.severity == original.severity
        assert restored.coupling_metrics.instability == original.coupling_metrics.instability

    def test_validate_dict_with_all_fields(self):
        """Should return valid when all required fields present."""
        data = {
            "category": "complexity",
            "severity": "high",
            "description": "Function too complex",
            "affected_files": [{"file_path": "src/main.py"}],
            "remediation": "Split into smaller functions",
            "confidence": "high",
        }
        is_valid, missing = PrincipalEngineerFinding.validate_dict(data)
        assert is_valid is True
        assert missing == []

    def test_validate_dict_with_missing_category(self):
        """Should return invalid and list missing category field."""
        data = {
            "severity": "high",
            "description": "Function too complex",
            "affected_files": [{"file_path": "src/main.py"}],
            "remediation": "Split into smaller functions",
            "confidence": "high",
        }
        is_valid, missing = PrincipalEngineerFinding.validate_dict(data)
        assert is_valid is False
        assert missing == ["category"]

    def test_validate_dict_with_multiple_missing_fields(self):
        """Should return invalid and list all missing fields."""
        data = {
            "description": "Function too complex",
        }
        is_valid, missing = PrincipalEngineerFinding.validate_dict(data)
        assert is_valid is False
        assert "category" in missing
        assert "severity" in missing
        assert "affected_files" in missing
        assert "remediation" in missing
        assert "confidence" in missing
        assert "description" not in missing

    def test_validate_dict_with_empty_dict(self):
        """Should return invalid with all required fields missing."""
        data = {}
        is_valid, missing = PrincipalEngineerFinding.validate_dict(data)
        assert is_valid is False
        assert len(missing) == 6


class TestConsolidatedPrincipalFindings:
    """Test suite for ConsolidatedPrincipalFindings dataclass."""

    def test_create_empty(self):
        """Should create empty consolidated findings."""
        cpf = ConsolidatedPrincipalFindings()
        assert len(cpf.complexity_findings) == 0
        assert len(cpf.dry_violations) == 0
        assert len(cpf.coupling_issues) == 0
        assert len(cpf.separation_of_concerns_issues) == 0
        assert len(cpf.maintainability_risks) == 0
        assert len(cpf.files_analyzed) == 0
        assert len(cpf.files_omitted) == 0

    def test_add_complexity_finding(self):
        """Should add complexity finding to correct collection."""
        cpf = ConsolidatedPrincipalFindings()
        finding_dict = {
            "category": "complexity",
            "severity": "high",
            "description": "High complexity",
            "affected_files": [{"file_path": "src/main.py"}],
            "remediation": "Refactor",
            "confidence": "high",
        }
        cpf.add_issue(finding_dict)
        assert len(cpf.complexity_findings) == 1
        assert len(cpf.dry_violations) == 0
        assert cpf.complexity_findings[0].category == FindingCategory.COMPLEXITY

    def test_add_dry_violation_finding(self):
        """Should add DRY violation to correct collection."""
        cpf = ConsolidatedPrincipalFindings()
        finding_dict = {
            "category": "dry_violation",
            "severity": "medium",
            "description": "Duplicated code",
            "affected_files": [{"file_path": "src/a.py"}, {"file_path": "src/b.py"}],
            "remediation": "Extract to utility",
            "confidence": "high",
            "similarity_percentage": 85.0,
        }
        cpf.add_issue(finding_dict)
        assert len(cpf.dry_violations) == 1
        assert cpf.dry_violations[0].similarity_percentage == 85.0

    def test_add_coupling_finding(self):
        """Should add coupling finding to correct collection."""
        cpf = ConsolidatedPrincipalFindings()
        finding_dict = {
            "category": "coupling",
            "severity": "critical",
            "description": "Circular dependency",
            "affected_files": [{"file_path": "src/a.py"}],
            "remediation": "Break cycle",
            "confidence": "certain",
        }
        cpf.add_issue(finding_dict)
        assert len(cpf.coupling_issues) == 1

    def test_add_separation_finding(self):
        """Should add separation of concerns finding to correct collection."""
        cpf = ConsolidatedPrincipalFindings()
        finding_dict = {
            "category": "separation_of_concerns",
            "severity": "medium",
            "description": "Mixed responsibilities",
            "affected_files": [{"file_path": "src/service.py"}],
            "remediation": "Apply layered architecture",
            "confidence": "high",
        }
        cpf.add_issue(finding_dict)
        assert len(cpf.separation_of_concerns_issues) == 1

    def test_add_maintainability_finding(self):
        """Should add maintainability risk to correct collection."""
        cpf = ConsolidatedPrincipalFindings()
        finding_dict = {
            "category": "maintainability_risk",
            "severity": "low",
            "description": "Magic number",
            "affected_files": [{"file_path": "src/config.py"}],
            "remediation": "Define constant",
            "confidence": "certain",
        }
        cpf.add_issue(finding_dict)
        assert len(cpf.maintainability_risks) == 1

    def test_get_all_findings(self):
        """Should return all findings across categories."""
        cpf = ConsolidatedPrincipalFindings()
        for category in ["complexity", "dry_violation", "coupling", "separation_of_concerns", "maintainability_risk"]:
            cpf.add_issue({
                "category": category,
                "severity": "medium",
                "description": f"Test {category}",
                "affected_files": [{"file_path": "src/test.py"}],
                "remediation": "Fix it",
                "confidence": "high",
            })
        all_findings = cpf.get_all_findings()
        assert len(all_findings) == 5

    def test_get_findings_by_severity(self):
        """Should group findings by severity."""
        cpf = ConsolidatedPrincipalFindings()
        cpf.add_issue({
            "category": "complexity",
            "severity": "critical",
            "description": "Critical finding",
            "affected_files": [{"file_path": "src/a.py"}],
            "remediation": "Fix",
            "confidence": "high",
        })
        cpf.add_issue({
            "category": "coupling",
            "severity": "high",
            "description": "High finding",
            "affected_files": [{"file_path": "src/b.py"}],
            "remediation": "Fix",
            "confidence": "high",
        })
        cpf.add_issue({
            "category": "dry_violation",
            "severity": "medium",
            "description": "Medium finding",
            "affected_files": [{"file_path": "src/c.py"}],
            "remediation": "Fix",
            "confidence": "high",
        })
        by_severity = cpf.get_findings_by_severity()
        assert len(by_severity["critical"]) == 1
        assert len(by_severity["high"]) == 1
        assert len(by_severity["medium"]) == 1
        assert len(by_severity["low"]) == 0
        assert len(by_severity["info"]) == 0

    def test_get_findings_by_severity_with_info(self):
        """Should include info severity findings."""
        cpf = ConsolidatedPrincipalFindings()
        cpf.add_issue({
            "category": "complexity",
            "severity": "info",
            "description": "Good pattern observed",
            "affected_files": [{"file_path": "src/clean.py"}],
            "remediation": "Keep it up",
            "confidence": "high",
        })
        by_severity = cpf.get_findings_by_severity()
        assert len(by_severity["info"]) == 1
        assert by_severity["info"][0].description == "Good pattern observed"

    def test_get_audit_summary(self):
        """Should generate audit summary dictionary."""
        cpf = ConsolidatedPrincipalFindings()
        cpf.files_analyzed = ["src/a.py", "src/b.py", "src/c.py"]
        cpf.files_omitted = ["tests/test_a.py"]
        cpf.add_issue({
            "category": "complexity",
            "severity": "critical",
            "description": "Critical",
            "affected_files": [{"file_path": "src/a.py"}],
            "remediation": "Fix",
            "confidence": "high",
        })
        summary = cpf.get_audit_summary()
        assert isinstance(summary, dict)
        assert summary["files_examined"] == 3
        assert summary["files_omitted"] == 1
        assert summary["total_findings"] == 1
        assert summary["severity_counts"]["critical"] == 1
        assert summary["severity_counts"]["high"] == 0
        assert "3 files" in summary["summary_text"]

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        cpf = ConsolidatedPrincipalFindings()
        cpf.files_analyzed = ["src/main.py"]
        cpf.files_omitted = ["tests/test.py"]
        cpf.omitted_priority_1 = []
        cpf.omitted_priority_2 = []
        cpf.omitted_priority_3 = ["tests/test.py"]
        cpf.add_issue({
            "category": "complexity",
            "severity": "high",
            "description": "Complex",
            "affected_files": [{"file_path": "src/main.py"}],
            "remediation": "Simplify",
            "confidence": "high",
        })
        result = cpf.to_dict()
        assert "complexity_findings" in result
        assert len(result["complexity_findings"]) == 1
        assert result["files_analyzed"] == ["src/main.py"]
        assert result["files_omitted"] == ["tests/test.py"]
        assert result["omitted_priority_3"] == ["tests/test.py"]

    def test_inherits_from_consolidated_findings(self):
        """Should maintain compatibility with ConsolidatedFindings."""
        cpf = ConsolidatedPrincipalFindings()
        cpf.add_issue({
            "category": "complexity",
            "severity": "high",
            "description": "Test",
            "affected_files": [{"file_path": "src/test.py"}],
            "remediation": "Fix",
            "confidence": "high",
        })
        assert len(cpf.issues_found) == 1

    def test_add_step_populates_files_analyzed(self):
        """Should populate files_analyzed from step_data.files_checked."""
        from dataclasses import dataclass, field
        from typing import Optional

        @dataclass
        class MockStepData:
            step_number: int = 1
            files_checked: set = field(default_factory=set)
            relevant_files: set = field(default_factory=set)
            findings: str = ""
            hypothesis: Optional[str] = None
            confidence: ConfidenceLevel = ConfidenceLevel.EXPLORING

        cpf = ConsolidatedPrincipalFindings()
        step_data = MockStepData(
            step_number=1,
            files_checked={"src/main.py", "src/utils.py", "src/config.py"},
        )
        cpf.add_step(step_data)
        assert len(cpf.files_analyzed) == 3
        assert "src/main.py" in cpf.files_analyzed
        assert "src/utils.py" in cpf.files_analyzed
        assert "src/config.py" in cpf.files_analyzed
        assert len(cpf.files_checked) == 3

    def test_add_step_deduplicates_files_analyzed(self):
        """Should not add duplicate files to files_analyzed."""
        from dataclasses import dataclass, field
        from typing import Optional

        @dataclass
        class MockStepData:
            step_number: int = 1
            files_checked: set = field(default_factory=set)
            relevant_files: set = field(default_factory=set)
            findings: str = ""
            hypothesis: Optional[str] = None
            confidence: ConfidenceLevel = ConfidenceLevel.EXPLORING

        cpf = ConsolidatedPrincipalFindings()
        cpf.files_analyzed = ["src/main.py"]
        step_data = MockStepData(
            step_number=2,
            files_checked={"src/main.py", "src/new_file.py"},
        )
        cpf.add_step(step_data)
        assert len(cpf.files_analyzed) == 2
        assert cpf.files_analyzed.count("src/main.py") == 1
        assert "src/new_file.py" in cpf.files_analyzed


class TestNormalizeCategory:
    """Test suite for normalize_category function."""

    def test_normalize_exact_match(self):
        """Should return exact match for valid categories."""
        assert normalize_category("complexity") == "complexity"
        assert normalize_category("dry_violation") == "dry_violation"
        assert normalize_category("coupling") == "coupling"
        assert normalize_category("separation_of_concerns") == "separation_of_concerns"
        assert normalize_category("maintainability_risk") == "maintainability_risk"

    def test_normalize_maintainability_to_maintainability_risk(self):
        """Should map 'maintainability' to 'maintainability_risk'."""
        assert normalize_category("maintainability") == "maintainability_risk"

    def test_normalize_case_insensitive(self):
        """Should handle uppercase and mixed case."""
        assert normalize_category("COMPLEXITY") == "complexity"
        assert normalize_category("Complexity") == "complexity"
        assert normalize_category("MAINTAINABILITY") == "maintainability_risk"
        assert normalize_category("Maintainability_Risk") == "maintainability_risk"

    def test_normalize_with_whitespace(self):
        """Should strip leading/trailing whitespace."""
        assert normalize_category("  complexity  ") == "complexity"
        assert normalize_category("  maintainability  ") == "maintainability_risk"

    def test_normalize_dry_variations(self):
        """Should handle DRY variations."""
        assert normalize_category("dry") == "dry_violation"
        assert normalize_category("duplication") == "dry_violation"
        assert normalize_category("dry_violation") == "dry_violation"

    def test_normalize_separation_variations(self):
        """Should handle separation of concerns variations."""
        assert normalize_category("separation") == "separation_of_concerns"
        assert normalize_category("separation_of_concerns") == "separation_of_concerns"

    def test_normalize_with_hyphens(self):
        """Should normalize hyphens to underscores."""
        assert normalize_category("dry-violation") == "dry_violation"
        assert normalize_category("separation-of-concerns") == "separation_of_concerns"

    def test_normalize_invalid_category_raises_error(self):
        """Should raise ValueError for invalid categories."""
        with pytest.raises(ValueError) as exc_info:
            normalize_category("invalid_category")
        assert "cannot be mapped" in str(exc_info.value)
        assert "invalid_category" in str(exc_info.value)

    def test_normalize_empty_string_raises_error(self):
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError):
            normalize_category("")


class TestPrincipalEngineerFindingCategoryNormalization:
    """Test suite for PrincipalEngineerFinding with category normalization."""

    def test_from_dict_with_maintainability_category(self):
        """Should handle 'maintainability' category in from_dict."""
        data = {
            "category": "maintainability",
            "severity": "high",
            "description": "Code maintainability issue",
            "affected_files": [{"file_path": "src/main.py"}],
            "remediation": "Improve code structure",
            "confidence": "high",
        }
        finding = PrincipalEngineerFinding.from_dict(data)
        assert finding.category == FindingCategory.MAINTAINABILITY_RISK

    def test_from_dict_with_uppercase_maintainability(self):
        """Should handle uppercase 'MAINTAINABILITY' category."""
        data = {
            "category": "MAINTAINABILITY",
            "severity": "high",
            "description": "Code maintainability issue",
            "affected_files": [{"file_path": "src/main.py"}],
            "remediation": "Improve code structure",
            "confidence": "high",
        }
        finding = PrincipalEngineerFinding.from_dict(data)
        assert finding.category == FindingCategory.MAINTAINABILITY_RISK

    def test_from_dict_with_whitespace_category(self):
        """Should handle category with whitespace."""
        data = {
            "category": "  maintainability  ",
            "severity": "medium",
            "description": "Test",
            "affected_files": [{"file_path": "test.py"}],
            "remediation": "Fix",
            "confidence": "medium",
        }
        finding = PrincipalEngineerFinding.from_dict(data)
        assert finding.category == FindingCategory.MAINTAINABILITY_RISK

    def test_from_dict_with_dry_variation(self):
        """Should handle 'dry' as shorthand for 'dry_violation'."""
        data = {
            "category": "dry",
            "severity": "medium",
            "description": "Duplicated code",
            "affected_files": [{"file_path": "src/a.py"}],
            "remediation": "Extract",
            "confidence": "high",
        }
        finding = PrincipalEngineerFinding.from_dict(data)
        assert finding.category == FindingCategory.DRY_VIOLATION

    def test_from_dict_with_invalid_category_raises_error(self):
        """Should raise ValueError for invalid category."""
        data = {
            "category": "invalid_category",
            "severity": "high",
            "description": "Test",
            "affected_files": [{"file_path": "test.py"}],
            "remediation": "Fix",
            "confidence": "high",
        }
        with pytest.raises(ValueError) as exc_info:
            PrincipalEngineerFinding.from_dict(data)
        assert "invalid_category" in str(exc_info.value)

    def test_from_dict_missing_category_field(self):
        """Should raise KeyError with helpful message when category is missing."""
        data = {
            "severity": "high",
            "description": "Test finding without category",
            "affected_files": [{"file_path": "test.py"}],
            "remediation": "Fix it",
            "confidence": "high",
        }
        with pytest.raises(KeyError) as exc_info:
            PrincipalEngineerFinding.from_dict(data)
        assert "Missing required field 'category'" in str(exc_info.value)
        assert "Available fields:" in str(exc_info.value)


class TestTransformLegacyFindingFormat:
    """Test suite for transform_legacy_finding_format function."""

    def test_transform_legacy_format_with_finding_field(self):
        """Should transform 'finding' to 'description'."""
        legacy = {
            "category": "complexity",
            "severity": "high",
            "finding": "Function is too complex",
            "file_path": "src/main.py",
            "line_number": 100,
            "recommendation": "Split into smaller functions",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["description"] == "Function is too complex"
        assert "finding" not in result

    def test_transform_legacy_format_with_recommendation_field(self):
        """Should transform 'recommendation' to 'remediation'."""
        legacy = {
            "category": "dry_violation",
            "severity": "medium",
            "finding": "Duplicated code",
            "file_path": "src/a.py",
            "recommendation": "Extract to utility",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["remediation"] == "Extract to utility"
        assert "recommendation" not in result

    def test_transform_legacy_format_file_path_to_affected_files(self):
        """Should transform file_path + line_number to affected_files array."""
        legacy = {
            "category": "coupling",
            "severity": "high",
            "finding": "High coupling",
            "file_path": "/path/to/file.ts",
            "line_number": 138,
            "recommendation": "Fix it",
        }
        result = transform_legacy_finding_format(legacy)
        assert "affected_files" in result
        assert len(result["affected_files"]) == 1
        assert result["affected_files"][0]["file_path"] == "/path/to/file.ts"
        assert result["affected_files"][0]["line_start"] == 138
        assert "file_path" not in result
        assert "line_number" not in result

    def test_transform_legacy_format_adds_default_confidence(self):
        """Should add default confidence if missing."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "finding": "Hard to maintain",
            "file_path": "src/service.py",
            "recommendation": "Refactor",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["confidence"] == "high"

    def test_transform_legacy_format_with_explanation(self):
        """Should merge explanation into description."""
        legacy = {
            "category": "complexity",
            "severity": "high",
            "finding": "Complex function",
            "explanation": "This function has 30 branches",
            "file_path": "src/main.py",
            "recommendation": "Simplify",
        }
        result = transform_legacy_finding_format(legacy)
        assert "Complex function" in result["description"]
        assert "This function has 30 branches" in result["description"]
        assert "explanation" not in result

    def test_transform_already_correct_format(self):
        """Should return as-is if already in correct format."""
        correct = {
            "category": "complexity",
            "severity": "high",
            "description": "Already correct",
            "affected_files": [{"file_path": "src/main.py"}],
            "remediation": "Fix it",
            "confidence": "high",
        }
        result = transform_legacy_finding_format(correct)
        assert result == correct

    def test_transform_with_function_name(self):
        """Should preserve function_name in affected_files."""
        legacy = {
            "category": "complexity",
            "severity": "high",
            "finding": "Complex",
            "file_path": "src/main.py",
            "line_number": 100,
            "function_name": "processData",
            "recommendation": "Split",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["affected_files"][0]["function_name"] == "processData"

    def test_transform_with_line_start_end(self):
        """Should handle line_start and line_end."""
        legacy = {
            "category": "dry_violation",
            "severity": "medium",
            "finding": "Duplicated",
            "file_path": "src/main.py",
            "line_start": 100,
            "line_end": 150,
            "recommendation": "Extract",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["affected_files"][0]["line_start"] == 100
        assert result["affected_files"][0]["line_end"] == 150

    def test_transform_with_file_instead_of_file_path(self):
        """Should transform 'file' to affected_files."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "file": "src/service.ts",
            "description": "Issue found",
            "remediation": "Fix it",
        }
        result = transform_legacy_finding_format(legacy)
        assert "affected_files" in result
        assert result["affected_files"][0]["file_path"] == "src/service.ts"

    def test_transform_with_general_file_value(self):
        """Should handle 'General' file value gracefully with placeholder."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "file": "General",
            "line_range": "N/A",
            "description": "Issue found",
            "remediation": "Fix it",
        }
        result = transform_legacy_finding_format(legacy)
        assert "affected_files" in result
        assert result["affected_files"][0]["file_path"] == "general"

    def test_transform_with_na_file_value(self):
        """Should handle 'N/A' file value gracefully with placeholder."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "file": "N/A",
            "description": "Issue found",
            "remediation": "Fix it",
        }
        result = transform_legacy_finding_format(legacy)
        assert "affected_files" in result
        assert result["affected_files"][0]["file_path"] == "general"

    def test_transform_with_line_range(self):
        """Should parse line_range like '100-150'."""
        legacy = {
            "category": "complexity",
            "severity": "high",
            "file": "src/main.py",
            "line_range": "100-150",
            "description": "Complex function",
            "remediation": "Simplify",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["affected_files"][0]["line_start"] == 100
        assert result["affected_files"][0]["line_end"] == 150

    def test_transform_with_line_range_single_number(self):
        """Should parse line_range with single number."""
        legacy = {
            "category": "complexity",
            "severity": "high",
            "file": "src/main.py",
            "line_range": "42",
            "description": "Issue at line",
            "remediation": "Fix it",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["affected_files"][0]["line_start"] == 42

    def test_transform_with_line_range_na(self):
        """Should handle 'N/A' line_range gracefully."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "file": "src/main.py",
            "line_range": "N/A",
            "description": "General issue",
            "remediation": "Fix it",
        }
        result = transform_legacy_finding_format(legacy)
        assert "affected_files" in result
        assert result["affected_files"][0]["file_path"] == "src/main.py"
        assert "line_start" not in result["affected_files"][0]

    def test_transform_with_title_field(self):
        """Should merge title into description."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "file": "General",
            "title": "Error Handling Issue",
            "description": "Inconsistent patterns across codebase",
            "remediation": "Standardize",
        }
        result = transform_legacy_finding_format(legacy)
        assert "Error Handling Issue" in result["description"]
        assert "Inconsistent patterns" in result["description"]

    def test_transform_with_title_only(self):
        """Should use title as description if no description provided."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "file": "General",
            "title": "Inconsistent Error Handling Patterns",
            "remediation": "Standardize",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["description"] == "Inconsistent Error Handling Patterns"

    def test_transform_real_world_example(self):
        """Should handle the exact format from the error report."""
        legacy = {
            "category": "maintainability",
            "severity": "medium",
            "file": "General",
            "line_range": "N/A",
            "title": "Inconsistent Error Handling Patterns",
            "description": "Error handling varies...",
            "remediation": "Establish consistent error handling...",
            "confidence": "high",
        }
        result = transform_legacy_finding_format(legacy)
        assert "affected_files" in result
        assert result["affected_files"][0]["file_path"] == "general"
        assert "Inconsistent Error Handling Patterns" in result["description"]
        assert "Error handling varies" in result["description"]
        assert result["remediation"] == "Establish consistent error handling..."
        assert result["confidence"] == "high"

    def test_transform_type_to_category(self):
        """Should transform 'type' to 'category'."""
        legacy = {
            "type": "dry_violation",
            "severity": "low",
            "file": "src/main.py",
            "description": "Duplicated code detected",
            "recommendation": "Extract to utility function",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["category"] == "dry_violation"
        assert "type" not in result

    def test_transform_with_non_numeric_line(self):
        """Should handle non-numeric line values like 'various'."""
        legacy = {
            "type": "coupling",
            "severity": "medium",
            "file": "multiple files",
            "line": "various",
            "description": "High coupling detected",
            "recommendation": "Decouple modules",
        }
        result = transform_legacy_finding_format(legacy)
        assert result["category"] == "coupling"
        # Non-numeric 'various' should not produce line_start/line_end
        assert "line_start" not in result["affected_files"][0]
        assert "affected_files" in result

    def test_transform_with_affected_files_but_missing_category(self):
        """Should still transform type → category even if affected_files exists."""
        partial = {
            "type": "complexity",
            "severity": "high",
            "description": "Complex function",
            "affected_files": [{"file_path": "src/main.py"}],
            "recommendation": "Simplify",
        }
        result = transform_legacy_finding_format(partial)
        assert result["category"] == "complexity"
        assert "type" not in result

    def test_transform_mcp_client_exact_failing_format(self):
        """Should handle the exact format from the MCP client that was failing."""
        legacy = {
            "type": "dry_violation",
            "severity": "low",
            "file": "multiple services",
            "line": "various",
            "description": "plainToInstance transformation patterns repeated",
            "recommendation": "Consider creating typed factory methods",
        }
        result = transform_legacy_finding_format(legacy)
        assert "category" in result
        assert result["category"] == "dry_violation"
        assert "type" not in result
        assert "affected_files" in result
        assert result["remediation"] == "Consider creating typed factory methods"


class TestPrincipalEngineerFindingLegacyFormat:
    """Test suite for PrincipalEngineerFinding with legacy format."""

    def test_from_dict_with_legacy_format(self):
        """Should accept legacy format with 'finding' and 'recommendation'."""
        legacy_data = {
            "category": "separation_of_concerns",
            "severity": "high",
            "finding": "Input validation mixed with business logic",
            "file_path": "src/candidates.service.ts",
            "line_number": 138,
            "recommendation": "Extract validation to separate layer",
        }
        finding = PrincipalEngineerFinding.from_dict(legacy_data)
        assert finding.category == FindingCategory.SEPARATION_OF_CONCERNS
        assert finding.severity == Severity.HIGH
        assert "Input validation mixed" in finding.description
        assert len(finding.affected_files) == 1
        assert finding.affected_files[0].file_path == "src/candidates.service.ts"
        assert finding.affected_files[0].line_start == 138
        assert "Extract validation" in finding.remediation
        assert finding.confidence == ConfidenceLevel.HIGH

    def test_from_dict_with_legacy_maintainability_category(self):
        """Should handle legacy 'maintainability' category."""
        legacy_data = {
            "category": "maintainability",
            "severity": "critical",
            "finding": "God Object antipattern - 2119 lines",
            "file_path": "src/candidates.service.ts",
            "line_number": 1,
            "recommendation": "Split into multiple services",
        }
        finding = PrincipalEngineerFinding.from_dict(legacy_data)
        assert finding.category == FindingCategory.MAINTAINABILITY_RISK

    def test_from_dict_with_legacy_format_and_explanation(self):
        """Should merge explanation into description."""
        legacy_data = {
            "category": "coupling",
            "severity": "high",
            "finding": "High coupling detected",
            "explanation": "Service depends on 14 other services",
            "file_path": "src/service.ts",
            "line_number": 90,
            "recommendation": "Apply dependency injection",
        }
        finding = PrincipalEngineerFinding.from_dict(legacy_data)
        assert "High coupling detected" in finding.description
        assert "Service depends on 14 other services" in finding.description


class TestConsolidatedPrincipalFindingsCategoryNormalization:
    """Test suite for ConsolidatedPrincipalFindings with category normalization."""

    def test_add_issue_with_maintainability_category(self):
        """Should add finding with 'maintainability' to maintainability_risks."""
        cpf = ConsolidatedPrincipalFindings()
        finding_dict = {
            "category": "maintainability",
            "severity": "medium",
            "description": "Code maintainability concern",
            "affected_files": [{"file_path": "src/service.py"}],
            "remediation": "Refactor for clarity",
            "confidence": "high",
        }
        cpf.add_issue(finding_dict)
        assert len(cpf.maintainability_risks) == 1
        assert len(cpf.complexity_findings) == 0
        assert cpf.maintainability_risks[0].category == FindingCategory.MAINTAINABILITY_RISK

    def test_add_issue_with_dry_shorthand(self):
        """Should add finding with 'dry' shorthand to dry_violations."""
        cpf = ConsolidatedPrincipalFindings()
        finding_dict = {
            "category": "dry",
            "severity": "medium",
            "description": "Duplicated logic",
            "affected_files": [{"file_path": "src/a.py"}],
            "remediation": "Extract shared code",
            "confidence": "high",
        }
        cpf.add_issue(finding_dict)
        assert len(cpf.dry_violations) == 1
        assert cpf.dry_violations[0].category == FindingCategory.DRY_VIOLATION
