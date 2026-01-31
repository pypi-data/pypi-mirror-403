"""Unit tests for generate_report data models."""

from datetime import datetime
from pathlib import Path

import pytest

from tools.generate_report.models import (
    AuditLens,
    ReportGenerationError,
    ReportGenerationResponse,
    ReportMetadata,
)


class TestAuditLens:
    """Tests for AuditLens enum."""

    def test_security_lens_tool_name(self):
        """SECURITY lens should map to security_audit."""
        assert AuditLens.SECURITY.tool_name == "security_audit"

    def test_a11y_lens_tool_name(self):
        """A11Y lens should map to a11y_audit."""
        assert AuditLens.A11Y.tool_name == "a11y_audit"

    def test_principal_lens_tool_name(self):
        """PRINCIPAL lens should map to principal_audit."""
        assert AuditLens.PRINCIPAL.tool_name == "principal_audit"

    def test_devops_lens_tool_name(self):
        """DEVOPS lens should map to devops_audit."""
        assert AuditLens.DEVOPS.tool_name == "devops_audit"

    def test_from_tool_name_security(self):
        """security_audit should convert to SECURITY lens."""
        assert AuditLens.from_tool_name("security_audit") == AuditLens.SECURITY

    def test_from_tool_name_a11y(self):
        """a11y_audit should convert to A11Y lens."""
        assert AuditLens.from_tool_name("a11y_audit") == AuditLens.A11Y

    def test_from_tool_name_principal(self):
        """principal_audit should convert to PRINCIPAL lens."""
        assert AuditLens.from_tool_name("principal_audit") == AuditLens.PRINCIPAL

    def test_from_tool_name_devops(self):
        """devops_audit should convert to DEVOPS lens."""
        assert AuditLens.from_tool_name("devops_audit") == AuditLens.DEVOPS

    def test_from_tool_name_invalid(self):
        """Invalid tool name should raise ValueError."""
        with pytest.raises(ValueError) as excinfo:
            AuditLens.from_tool_name("invalid_audit")
        assert "Unknown tool name" in str(excinfo.value)
        assert "invalid_audit" in str(excinfo.value)

    def test_lens_is_string_enum(self):
        """Lens values should be strings."""
        assert AuditLens.SECURITY.value == "SECURITY"
        assert AuditLens.A11Y.value == "A11Y"
        assert AuditLens.PRINCIPAL.value == "PRINCIPAL"
        assert AuditLens.DEVOPS.value == "DEVOPS"


class TestReportMetadata:
    """Tests for ReportMetadata dataclass."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata."""
        return ReportMetadata(
            lens=AuditLens.SECURITY,
            report_number=5,
            report_path=Path("/project/reports/SECURITY_AUDIT_REPORT_5.md"),
            generated_at=datetime(2026, 1, 19, 14, 30),
            project_name="TestProject",
        )

    def test_to_dict_contains_lens(self, sample_metadata):
        """to_dict should contain lens value."""
        data = sample_metadata.to_dict()
        assert data["lens"] == "SECURITY"

    def test_to_dict_contains_report_number(self, sample_metadata):
        """to_dict should contain report number."""
        data = sample_metadata.to_dict()
        assert data["report_number"] == 5

    def test_to_dict_contains_report_path_as_string(self, sample_metadata):
        """to_dict should contain report path as string."""
        data = sample_metadata.to_dict()
        assert data["report_path"] == "/project/reports/SECURITY_AUDIT_REPORT_5.md"

    def test_to_dict_contains_generated_at_iso(self, sample_metadata):
        """to_dict should contain generated_at in ISO format."""
        data = sample_metadata.to_dict()
        assert data["generated_at"] == "2026-01-19T14:30:00"

    def test_to_dict_contains_project_name(self, sample_metadata):
        """to_dict should contain project name."""
        data = sample_metadata.to_dict()
        assert data["project_name"] == "TestProject"

    def test_filename_property(self, sample_metadata):
        """filename property should return correct format."""
        assert sample_metadata.filename == "SECURITY_AUDIT_REPORT_5.md"

    def test_default_project_name(self):
        """Default project name should be 'Unknown Project'."""
        metadata = ReportMetadata(
            lens=AuditLens.A11Y,
            report_number=1,
            report_path=Path("/reports/A11Y_AUDIT_REPORT_1.md"),
            generated_at=datetime.now(),
        )
        assert metadata.project_name == "Unknown Project"


class TestReportGenerationResponse:
    """Tests for ReportGenerationResponse dataclass."""

    def test_to_dict_success(self):
        """to_dict should include all success fields."""
        response = ReportGenerationResponse(
            success=True,
            report_path=Path("/reports/SECURITY_AUDIT_REPORT_1.md"),
            report_number=1,
            lens=AuditLens.SECURITY,
            message="Report generated successfully.",
        )
        data = response.to_dict()
        assert data["success"] is True
        assert data["report_path"] == "/reports/SECURITY_AUDIT_REPORT_1.md"
        assert data["report_number"] == 1
        assert data["lens"] == "SECURITY"
        assert data["message"] == "Report generated successfully."

    def test_to_dict_includes_severity_counts(self):
        """to_dict should include severity_counts field (FR-008)."""
        response = ReportGenerationResponse(
            success=True,
            report_path=Path("/reports/SECURITY_AUDIT_REPORT_1.md"),
            report_number=1,
            lens=AuditLens.SECURITY,
            message="Report generated.",
            severity_counts={"critical": 2, "high": 5, "medium": 8, "low": 3, "info": 1},
            files_examined=42,
        )
        data = response.to_dict()
        assert data["severity_counts"] == {"critical": 2, "high": 5, "medium": 8, "low": 3, "info": 1}

    def test_to_dict_includes_files_examined(self):
        """to_dict should include files_examined field (FR-008)."""
        response = ReportGenerationResponse(
            success=True,
            report_path=Path("/reports/SECURITY_AUDIT_REPORT_1.md"),
            report_number=1,
            lens=AuditLens.SECURITY,
            message="Report generated.",
            files_examined=42,
        )
        data = response.to_dict()
        assert data["files_examined"] == 42

    def test_default_severity_counts_is_empty_dict(self):
        """Default severity_counts should be empty dict."""
        response = ReportGenerationResponse(
            success=True,
            report_path=Path("/reports/SECURITY_AUDIT_REPORT_1.md"),
            report_number=1,
            lens=AuditLens.SECURITY,
            message="Report generated.",
        )
        assert response.severity_counts == {}

    def test_default_files_examined_is_zero(self):
        """Default files_examined should be 0."""
        response = ReportGenerationResponse(
            success=True,
            report_path=Path("/reports/SECURITY_AUDIT_REPORT_1.md"),
            report_number=1,
            lens=AuditLens.SECURITY,
            message="Report generated.",
        )
        assert response.files_examined == 0


class TestReportGenerationError:
    """Tests for ReportGenerationError dataclass."""

    def test_to_dict_error(self):
        """to_dict should include all error fields."""
        error = ReportGenerationError(
            success=False,
            error="No completed audit found.",
            error_type="NoAuditFound",
        )
        data = error.to_dict()
        assert data["success"] is False
        assert data["error"] == "No completed audit found."
        assert data["error_type"] == "NoAuditFound"

    def test_default_values(self):
        """Default values should be set correctly."""
        error = ReportGenerationError()
        assert error.success is False
        assert error.error == ""
        assert error.error_type == "GeneralError"
