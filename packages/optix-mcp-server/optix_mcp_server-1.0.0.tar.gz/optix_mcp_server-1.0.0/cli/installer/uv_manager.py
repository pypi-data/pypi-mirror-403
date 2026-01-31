"""UV package manager detection and installation."""

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

from cli.installer.ui import ConsoleUI

MIN_UV_VERSION = "0.4.0"


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse version string into tuple of integers."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if match:
        return tuple(int(x) for x in match.groups())
    return (0, 0, 0)


def version_gte(version: str, min_version: str) -> bool:
    """Check if version is greater than or equal to min_version."""
    return parse_version(version) >= parse_version(min_version)


def find_uv() -> str | None:
    """Find uv executable in PATH or common locations."""
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path

    common_locations = [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
    ]

    if platform.system() == "Windows":
        common_locations.extend([
            Path(os.environ.get("LOCALAPPDATA", "")) / "uv" / "uv.exe",
            Path.home() / ".cargo" / "bin" / "uv.exe",
        ])

    for location in common_locations:
        if location.exists():
            return str(location)

    return None


def get_uv_version(uv_path: str) -> str | None:
    """Get uv version string."""
    try:
        result = subprocess.run(
            [uv_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def check_uv() -> tuple[bool, str | None, str | None]:
    """Check if uv is installed and meets version requirements.

    Returns:
        Tuple of (is_valid, uv_path, version)
    """
    uv_path = find_uv()
    if not uv_path:
        return (False, None, None)

    version = get_uv_version(uv_path)
    if not version:
        return (False, uv_path, None)

    if not version_gte(version, MIN_UV_VERSION):
        return (False, uv_path, version)

    return (True, uv_path, version)


def install_uv() -> bool:
    """Install uv using the official installer.

    Returns:
        True if installation succeeded
    """
    system = platform.system()

    if system == "Windows":
        cmd = ["powershell", "-ExecutionPolicy", "ByPass", "-c",
               "irm https://astral.sh/uv/install.ps1 | iex"]
    else:
        cmd = ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return False

        os.environ["PATH"] = (
            f"{Path.home() / '.local' / 'bin'}:"
            f"{Path.home() / '.cargo' / 'bin'}:"
            f"{os.environ.get('PATH', '')}"
        )

        return find_uv() is not None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def ensure_uv(ui: ConsoleUI) -> bool:
    """Ensure uv is installed and meets version requirements.

    Args:
        ui: Console UI for displaying progress

    Returns:
        True if uv is available and valid
    """
    ui.info("Checking uv package manager...")

    is_valid, uv_path, version = check_uv()

    if is_valid:
        ui.success(f"uv {version} is installed and meets requirements")
        return True

    if uv_path and version:
        ui.warn(f"uv version {version} is below required {MIN_UV_VERSION}. Upgrading...")
    elif uv_path:
        ui.warn("Could not determine uv version. Reinstalling...")
    else:
        ui.warn("uv not found. Installing...")

    ui.info("Installing uv from astral.sh...")

    if install_uv():
        is_valid, _, version = check_uv()
        if is_valid:
            ui.success(f"uv {version} installed successfully")
            return True

    ui.error("Failed to install uv. Please install manually: https://docs.astral.sh/uv/")
    return False
