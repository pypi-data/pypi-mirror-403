"""Log configuration management for optix-mcp-server."""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class OptixLogLevel(Enum):
    """Log levels supported by optix-mcp-server."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"

    @classmethod
    def from_string(cls, value: str) -> "OptixLogLevel":
        """Parse log level from string, defaulting to INFO for invalid values."""
        if not value:
            return cls.INFO

        normalized = value.upper().strip()
        if normalized == "WARNING":
            normalized = "WARN"

        try:
            return cls(normalized)
        except ValueError:
            return cls.INFO

    def to_python_level(self) -> int:
        """Convert to Python logging level."""
        mapping = {
            OptixLogLevel.DEBUG: logging.DEBUG,
            OptixLogLevel.INFO: logging.INFO,
            OptixLogLevel.WARN: logging.WARNING,
        }
        return mapping[self]


DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(tool_name)s] %(message)s"
DEFAULT_LOG_FILE = str(PROJECT_ROOT / "logs" / "optix.log")


@dataclass
class LogConfig:
    """Configuration for the logging system."""
    level: OptixLogLevel = OptixLogLevel.INFO
    log_file_path: str = DEFAULT_LOG_FILE
    log_to_stderr: bool = True
    format_string: str = DEFAULT_LOG_FORMAT
    _invalid_level_warning: Optional[str] = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> "LogConfig":
        """Create LogConfig from environment variables."""
        env_level = os.getenv("OPTIX_LOG_LEVEL", "").strip()
        if not env_level:
            env_level = os.getenv("LOG_LEVEL", "INFO").strip()

        original_value = env_level
        level = OptixLogLevel.from_string(env_level)

        invalid_warning = None
        if original_value and original_value.upper() not in ("DEBUG", "INFO", "WARN", "WARNING"):
            invalid_warning = f"Invalid log level '{original_value}', defaulting to INFO"

        log_file = os.getenv("OPTIX_LOG_FILE", DEFAULT_LOG_FILE)

        return cls(
            level=level,
            log_file_path=log_file,
            log_to_stderr=True,
            format_string=DEFAULT_LOG_FORMAT,
            _invalid_level_warning=invalid_warning,
        )

    def has_invalid_level_warning(self) -> bool:
        """Check if an invalid level was provided."""
        return self._invalid_level_warning is not None

    def get_invalid_level_warning(self) -> Optional[str]:
        """Get the warning message for invalid level."""
        return self._invalid_level_warning


_config: Optional[LogConfig] = None


def get_log_config() -> LogConfig:
    """Get the current logging configuration.

    Returns:
        LogConfig instance with current settings.
    """
    global _config
    if _config is None:
        _config = LogConfig.from_env()
    return _config


def reset_log_config() -> None:
    """Reset the log configuration (mainly for testing)."""
    global _config
    _config = None
