"""Sequential report numbering with race condition handling.

Provides atomic file numbering using O_EXCL pattern to prevent
duplicate report numbers under concurrent access.
"""

import os
import re
from pathlib import Path

from tools.generate_report.models import AuditLens

MAX_RETRY_ATTEMPTS = 10


def get_highest_report_number(reports_dir: Path, lens: AuditLens) -> int:
    """Scan reports directory to find the highest existing report number for a lens.

    Args:
        reports_dir: Path to the reports directory
        lens: The audit lens to scan for

    Returns:
        Highest existing report number, or 0 if no reports exist
    """
    if not reports_dir.exists():
        return 0

    pattern = re.compile(rf"^{lens.value}_AUDIT_REPORT_(\d+)\.md$")
    highest = 0

    for file_path in reports_dir.iterdir():
        if file_path.is_file():
            match = pattern.match(file_path.name)
            if match:
                num = int(match.group(1))
                highest = max(highest, num)

    return highest


def allocate_report_number(reports_dir: Path, lens: AuditLens) -> tuple[int, Path]:
    """Allocate the next available report number atomically.

    Uses O_EXCL flag to ensure atomic file creation and prevent race conditions
    when multiple processes try to create reports simultaneously.

    Args:
        reports_dir: Path to the reports directory
        lens: The audit lens for the report

    Returns:
        Tuple of (report_number, report_path)

    Raises:
        RuntimeError: If all retry attempts are exhausted (max 10 per FR-006)
    """
    base_num = get_highest_report_number(reports_dir, lens)

    for attempt in range(MAX_RETRY_ATTEMPTS):
        candidate_num = base_num + 1 + attempt
        candidate_path = reports_dir / f"{lens.value}_AUDIT_REPORT_{candidate_num}.md"

        try:
            fd = os.open(candidate_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            return candidate_num, candidate_path

        except FileExistsError:
            continue

    raise RuntimeError(
        f"Failed to allocate report number after {MAX_RETRY_ATTEMPTS} attempts. "
        f"This may indicate high concurrent activity or stale files in {reports_dir}. "
        f"Consider manually cleaning up old report files."
    )


def scan_existing_reports(reports_dir: Path) -> dict[AuditLens, list[int]]:
    """Scan reports directory and return existing report numbers by lens.

    Args:
        reports_dir: Path to the reports directory

    Returns:
        Dictionary mapping AuditLens to list of existing report numbers
    """
    result: dict[AuditLens, list[int]] = {lens: [] for lens in AuditLens}

    if not reports_dir.exists():
        return result

    for lens in AuditLens:
        pattern = re.compile(rf"^{lens.value}_AUDIT_REPORT_(\d+)\.md$")
        for file_path in reports_dir.iterdir():
            if file_path.is_file():
                match = pattern.match(file_path.name)
                if match:
                    result[lens].append(int(match.group(1)))

    for lens in result:
        result[lens].sort()

    return result
