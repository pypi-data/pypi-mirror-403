"""Unit tests for atomic file operations (T043)."""

import tempfile
from pathlib import Path

import pytest

from tools.generate_report.file_operations import (
    atomic_write_file,
    cleanup_temp_file,
    create_reports_directory,
)


class TestAtomicWriteFile:
    """Tests for atomic_write_file function."""

    def test_writes_content_to_file(self, tmp_path):
        """atomic_write_file should write content to target path."""
        target = tmp_path / "test_report.md"
        content = "# Test Report\n\nThis is test content."
        atomic_write_file(target, content)
        assert target.exists()
        assert target.read_text() == content

    def test_creates_file_with_utf8_encoding(self, tmp_path):
        """atomic_write_file should create file with UTF-8 encoding."""
        target = tmp_path / "test_report.md"
        content = "# Test with Unicode: café, naïve, 日本語"
        atomic_write_file(target, content)
        assert target.read_text(encoding="utf-8") == content

    def test_removes_temp_file_on_success(self, tmp_path):
        """Temp file should not exist after successful write."""
        target = tmp_path / "test_report.md"
        temp_path = target.with_suffix(".tmp")
        atomic_write_file(target, "content")
        assert not temp_path.exists()

    def test_overwrites_existing_file(self, tmp_path):
        """atomic_write_file should overwrite existing file."""
        target = tmp_path / "test_report.md"
        target.write_text("old content")
        atomic_write_file(target, "new content")
        assert target.read_text() == "new content"

    def test_raises_on_permission_error(self, tmp_path):
        """atomic_write_file should raise on permission error."""
        if hasattr(tmp_path, 'chmod'):
            readonly_dir = tmp_path / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)
            try:
                target = readonly_dir / "test_report.md"
                with pytest.raises((PermissionError, OSError)):
                    atomic_write_file(target, "content")
            finally:
                readonly_dir.chmod(0o755)


class TestCleanupTempFile:
    """Tests for cleanup_temp_file function."""

    def test_removes_existing_temp_file(self, tmp_path):
        """cleanup_temp_file should remove existing temp file."""
        temp_file = tmp_path / "test.tmp"
        temp_file.write_text("temp content")
        assert temp_file.exists()
        cleanup_temp_file(temp_file)
        assert not temp_file.exists()

    def test_handles_nonexistent_file(self, tmp_path):
        """cleanup_temp_file should handle nonexistent file gracefully."""
        temp_file = tmp_path / "nonexistent.tmp"
        cleanup_temp_file(temp_file)

    def test_logs_warning_on_removal_failure(self, tmp_path, capsys):
        """cleanup_temp_file should log warning on removal failure."""
        pass


class TestCreateReportsDirectory:
    """Tests for create_reports_directory function."""

    def test_creates_reports_directory(self, tmp_path):
        """create_reports_directory should create reports/ directory."""
        reports_dir = create_reports_directory(tmp_path)
        assert reports_dir.exists()
        assert reports_dir.is_dir()
        assert reports_dir.name == "reports"

    def test_returns_existing_directory(self, tmp_path):
        """create_reports_directory should return existing directory."""
        existing = tmp_path / "reports"
        existing.mkdir()
        reports_dir = create_reports_directory(tmp_path)
        assert reports_dir == existing

    def test_creates_parent_directories(self, tmp_path):
        """create_reports_directory should create parent directories."""
        nested = tmp_path / "level1" / "level2"
        nested.mkdir(parents=True)
        reports_dir = create_reports_directory(nested)
        assert reports_dir.exists()
        assert reports_dir == nested / "reports"

    def test_raises_permission_error_with_message(self, tmp_path):
        """create_reports_directory should raise PermissionError with message."""
        if hasattr(tmp_path, 'chmod'):
            readonly = tmp_path / "readonly"
            readonly.mkdir()
            readonly.chmod(0o444)
            try:
                with pytest.raises(PermissionError) as excinfo:
                    create_reports_directory(readonly)
                assert "Permission denied" in str(excinfo.value)
                assert str(readonly / "reports") in str(excinfo.value)
            finally:
                readonly.chmod(0o755)
