"""Configuration file writers for JSON and TOML formats."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class ConfigWriter(ABC):
    """Base class for configuration file writers."""

    MAX_BACKUPS = 3

    def backup_file(self, path: Path) -> Path | None:
        """Create a backup of the config file."""
        if not path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f"{path.suffix}.backup.{timestamp}")

        backup_path.write_bytes(path.read_bytes())
        self._rotate_backups(path)

        return backup_path

    def _rotate_backups(self, path: Path) -> None:
        """Keep only the most recent backups."""
        pattern = f"{path.name}.backup.*"
        backups = sorted(
            path.parent.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[self.MAX_BACKUPS:]:
            old_backup.unlink()

    def ensure_parent_dir(self, path: Path) -> None:
        """Ensure parent directory exists."""
        path.parent.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def read(self, path: Path) -> dict[str, Any]:
        """Read configuration from file."""
        pass

    @abstractmethod
    def write(self, path: Path, data: dict[str, Any]) -> None:
        """Write configuration to file."""
        pass

    @abstractmethod
    def merge_server_config(
        self,
        path: Path,
        key_path: str,
        server_name: str,
        config: dict[str, Any],
    ) -> None:
        """Merge server configuration into the config file."""
        pass


class JSONConfigWriter(ConfigWriter):
    """Writer for JSON configuration files."""

    def read(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}

        content = path.read_text().strip()
        if not content:
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def write(self, path: Path, data: dict[str, Any]) -> None:
        self.ensure_parent_dir(path)
        path.write_text(json.dumps(data, indent=2) + "\n")

    def merge_server_config(
        self,
        path: Path,
        key_path: str,
        server_name: str,
        config: dict[str, Any],
    ) -> None:
        self.backup_file(path)
        data = self.read(path)

        keys = key_path.split(".") if key_path else []
        current = data
        for key in keys:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[server_name] = config
        self.write(path, data)


class TOMLConfigWriter(ConfigWriter):
    """Writer for TOML configuration files."""

    def read(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}

        try:
            return tomllib.loads(path.read_text())
        except Exception:
            return {}

    def write(self, path: Path, data: dict[str, Any]) -> None:
        self.ensure_parent_dir(path)

        def format_value(v: Any) -> str:
            if isinstance(v, bool):
                return str(v).lower()
            elif isinstance(v, list):
                items = ", ".join(f'"{i}"' for i in v)
                return f"[{items}]"
            elif isinstance(v, str):
                return f'"{v}"'
            else:
                return str(v)

        def write_toml_section(f, data: dict, prefix: str = "") -> None:
            for key, value in data.items():
                if isinstance(value, dict):
                    nested_dicts = {k: v for k, v in value.items() if isinstance(v, dict)}
                    simple_values = {k: v for k, v in value.items() if not isinstance(v, dict)}

                    if simple_values or not nested_dicts:
                        f.write(f"\n[{prefix}{key}]\n")
                        for k, v in simple_values.items():
                            f.write(f"{k} = {format_value(v)}\n")

                    for nested_key, nested_value in nested_dicts.items():
                        write_toml_section(f, {nested_key: nested_value}, f"{prefix}{key}.")

        with open(path, "w") as f:
            write_toml_section(f, data)

    def merge_server_config(
        self,
        path: Path,
        key_path: str,
        server_name: str,
        config: dict[str, Any],
    ) -> None:
        self.backup_file(path)
        data = self.read(path)

        if key_path not in data:
            data[key_path] = {}

        data[key_path][server_name] = config
        self.write(path, data)
