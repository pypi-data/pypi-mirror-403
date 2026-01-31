"""Unit tests for sequential numbering logic (T044, T049)."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.generate_report.models import AuditLens
from tools.generate_report.numbering import (
    MAX_RETRY_ATTEMPTS,
    allocate_report_number,
    get_highest_report_number,
    scan_existing_reports,
)


class TestGetHighestReportNumber:
    """Tests for get_highest_report_number function."""

    def test_returns_zero_for_empty_directory(self, tmp_path):
        """Should return 0 for empty directory."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        result = get_highest_report_number(reports_dir, AuditLens.SECURITY)
        assert result == 0

    def test_returns_zero_for_nonexistent_directory(self, tmp_path):
        """Should return 0 for nonexistent directory."""
        reports_dir = tmp_path / "reports"
        result = get_highest_report_number(reports_dir, AuditLens.SECURITY)
        assert result == 0

    def test_finds_highest_number(self, tmp_path):
        """Should find highest existing report number."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "SECURITY_AUDIT_REPORT_1.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT_3.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT_7.md").touch()
        result = get_highest_report_number(reports_dir, AuditLens.SECURITY)
        assert result == 7

    def test_ignores_other_lenses(self, tmp_path):
        """Should ignore reports from other lenses."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "SECURITY_AUDIT_REPORT_5.md").touch()
        (reports_dir / "A11Y_AUDIT_REPORT_10.md").touch()
        result = get_highest_report_number(reports_dir, AuditLens.SECURITY)
        assert result == 5

    def test_ignores_non_matching_files(self, tmp_path):
        """Should ignore files that don't match the pattern."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "SECURITY_AUDIT_REPORT_3.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT_invalid.md").touch()
        (reports_dir / "other_file.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT.md").touch()
        result = get_highest_report_number(reports_dir, AuditLens.SECURITY)
        assert result == 3


class TestAllocateReportNumber:
    """Tests for allocate_report_number function."""

    def test_allocates_number_one_for_empty_directory(self, tmp_path):
        """Should allocate number 1 for empty directory."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_num, report_path = allocate_report_number(reports_dir, AuditLens.SECURITY)
        assert report_num == 1
        assert report_path == reports_dir / "SECURITY_AUDIT_REPORT_1.md"

    def test_allocates_next_number(self, tmp_path):
        """Should allocate next sequential number."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "SECURITY_AUDIT_REPORT_1.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT_2.md").touch()
        report_num, report_path = allocate_report_number(reports_dir, AuditLens.SECURITY)
        assert report_num == 3
        assert report_path == reports_dir / "SECURITY_AUDIT_REPORT_3.md"

    def test_creates_placeholder_file(self, tmp_path):
        """Should create placeholder file to claim the number."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_num, report_path = allocate_report_number(reports_dir, AuditLens.A11Y)
        assert report_path.exists()

    def test_handles_different_lenses(self, tmp_path):
        """Should handle different lenses independently."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "SECURITY_AUDIT_REPORT_5.md").touch()
        report_num, report_path = allocate_report_number(reports_dir, AuditLens.A11Y)
        assert report_num == 1
        assert "A11Y" in report_path.name

    def test_retries_on_file_exists(self, tmp_path):
        """Should retry with next number if file exists."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "PRINCIPAL_AUDIT_REPORT_1.md").touch()
        report_num, report_path = allocate_report_number(reports_dir, AuditLens.PRINCIPAL)
        assert report_num == 2

    def test_raises_after_max_retries(self, tmp_path):
        """Should raise RuntimeError after max retry attempts (T049)."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        def always_fail_open(*args, **kwargs):
            raise FileExistsError("Simulated race condition")

        with patch.object(os, "open", side_effect=always_fail_open):
            with patch(
                "tools.generate_report.numbering.get_highest_report_number",
                return_value=1,
            ):
                with pytest.raises(RuntimeError) as excinfo:
                    allocate_report_number(reports_dir, AuditLens.DEVOPS)
                error_msg = str(excinfo.value).lower()
                assert "failed to allocate" in error_msg
                assert f"{MAX_RETRY_ATTEMPTS} attempts" in error_msg

    def test_max_retry_attempts_is_10(self):
        """Max retry attempts should be 10 per FR-006."""
        assert MAX_RETRY_ATTEMPTS == 10


class TestScanExistingReports:
    """Tests for scan_existing_reports function."""

    def test_returns_empty_for_nonexistent_directory(self, tmp_path):
        """Should return empty dict for nonexistent directory."""
        reports_dir = tmp_path / "reports"
        result = scan_existing_reports(reports_dir)
        for lens in AuditLens:
            assert lens in result
            assert result[lens] == []

    def test_scans_all_lenses(self, tmp_path):
        """Should scan and return reports for all lenses."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "SECURITY_AUDIT_REPORT_1.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT_2.md").touch()
        (reports_dir / "A11Y_AUDIT_REPORT_1.md").touch()
        (reports_dir / "PRINCIPAL_AUDIT_REPORT_1.md").touch()
        (reports_dir / "PRINCIPAL_AUDIT_REPORT_5.md").touch()
        result = scan_existing_reports(reports_dir)
        assert result[AuditLens.SECURITY] == [1, 2]
        assert result[AuditLens.A11Y] == [1]
        assert result[AuditLens.PRINCIPAL] == [1, 5]
        assert result[AuditLens.DEVOPS] == []

    def test_returns_sorted_numbers(self, tmp_path):
        """Should return sorted list of numbers."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "SECURITY_AUDIT_REPORT_5.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT_1.md").touch()
        (reports_dir / "SECURITY_AUDIT_REPORT_3.md").touch()
        result = scan_existing_reports(reports_dir)
        assert result[AuditLens.SECURITY] == [1, 3, 5]
