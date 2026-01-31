"""Tool-specific logger factory for optix-mcp-server."""

import logging
import sys
from pathlib import Path
from typing import Optional

from logging_utils.config import get_log_config, LogConfig
from logging_utils.formatter import ToolLogFormatter
from logging_utils.handlers import UnbufferedFileHandler, StderrFallbackHandler


OPTIX_LOGGER_NAME = "optix"

_file_handler: Optional[logging.Handler] = None
_stderr_handler: Optional[logging.Handler] = None
_logging_initialized: bool = False


class ToolLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that automatically includes tool name in records."""

    def __init__(self, logger: logging.Logger, tool_name: str):
        super().__init__(logger, {"tool_name": tool_name})
        self.tool_name = tool_name

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"]["tool_name"] = self.tool_name
        return msg, kwargs

    def warn(self, msg, *args, **kwargs):
        """Alias for warning() to match spec's WARN level."""
        self.warning(msg, *args, **kwargs)


def setup_file_logging(log_file_path: Optional[str] = None) -> None:
    """Initialize file-based logging for real-time monitoring.

    Creates the log directory if it doesn't exist and configures
    the root optix logger with file and stderr handlers.

    Args:
        log_file_path: Path to log file. Uses config default if not specified.
    """
    global _file_handler, _stderr_handler, _logging_initialized

    if _logging_initialized:
        return

    config = get_log_config()
    file_path = log_file_path or config.log_file_path
    formatter = ToolLogFormatter(config.format_string)

    root_logger = logging.getLogger(OPTIX_LOGGER_NAME)
    root_logger.setLevel(config.level.to_python_level())

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    try:
        log_dir = Path(file_path).parent
        if log_dir and not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

        _file_handler = UnbufferedFileHandler(file_path)
        _file_handler.setFormatter(formatter)
        _file_handler.setLevel(config.level.to_python_level())
        root_logger.addHandler(_file_handler)
    except (OSError, IOError) as e:
        print(
            f"Warning: Could not setup file logging to {file_path}: {e}. "
            "Using stderr only.",
            file=sys.stderr,
        )

    if config.log_to_stderr:
        _stderr_handler = StderrFallbackHandler()
        _stderr_handler.setFormatter(formatter)
        _stderr_handler.setLevel(config.level.to_python_level())
        root_logger.addHandler(_stderr_handler)

    if config.has_invalid_level_warning():
        root_logger.warning(config.get_invalid_level_warning())

    _logging_initialized = True


def get_tool_logger(tool_name: str) -> ToolLoggerAdapter:
    """Create a logger for a specific tool.

    Args:
        tool_name: Identifier for the tool (e.g., "security_audit").

    Returns:
        Configured logger adapter with tool context.

    Raises:
        ValueError: If tool_name is empty.
    """
    if not tool_name or not tool_name.strip():
        raise ValueError("tool_name must be a non-empty string")

    if not _logging_initialized:
        setup_file_logging()

    logger = logging.getLogger(f"{OPTIX_LOGGER_NAME}.{tool_name}")
    return ToolLoggerAdapter(logger, tool_name.strip())


def reset_logging() -> None:
    """Reset logging state (mainly for testing)."""
    global _file_handler, _stderr_handler, _logging_initialized

    root_logger = logging.getLogger(OPTIX_LOGGER_NAME)
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    _file_handler = None
    _stderr_handler = None
    _logging_initialized = False
