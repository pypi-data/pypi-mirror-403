"""Atomic file operations for report generation.

Provides safe file writing with cleanup on failure using
temp file + rename pattern for atomicity.
"""

import sys
from pathlib import Path


def atomic_write_file(target_path: Path, content: str) -> None:
    """Write content to file atomically using temp file + rename pattern.

    Args:
        target_path: Final destination path for the file
        content: Content to write to the file

    Raises:
        OSError: If file write or rename fails
        PermissionError: If permission denied
    """
    temp_path = target_path.with_suffix(".tmp")

    try:
        temp_path.write_text(content, encoding="utf-8")
        temp_path.rename(target_path)
    except Exception:
        cleanup_temp_file(temp_path)
        raise


def cleanup_temp_file(temp_path: Path) -> None:
    """Best-effort cleanup of temp file.

    Args:
        temp_path: Path to temp file to remove
    """
    if temp_path.exists():
        try:
            temp_path.unlink()
        except OSError as e:
            print(
                f"[WARN] Failed to cleanup temp file {temp_path}: {e}",
                file=sys.stderr,
            )


def create_reports_directory(project_root: Path) -> Path:
    """Create the reports directory if it doesn't exist.

    Args:
        project_root: Project root directory path

    Returns:
        Path to the reports directory

    Raises:
        PermissionError: If permission denied when creating directory
        OSError: If directory creation fails for other reasons
    """
    reports_dir = project_root / "reports"

    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir
    except PermissionError as e:
        raise PermissionError(
            f"Failed to create reports directory: Permission denied at {reports_dir}. "
            f"Please check directory permissions or run with appropriate privileges."
        ) from e
    except OSError as e:
        raise OSError(f"Failed to create reports directory at {reports_dir}: {e}") from e
