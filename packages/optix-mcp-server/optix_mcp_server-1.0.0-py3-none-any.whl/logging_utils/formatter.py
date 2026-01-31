"""Custom log formatter with tool name support."""

import logging
from typing import Optional


class ToolLogFormatter(logging.Formatter):
    """Log formatter that includes tool name in output.

    Format: %(asctime)s - %(levelname)s - [%(tool_name)s] %(message)s
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        default_tool_name: str = "server",
    ):
        if fmt is None:
            fmt = "%(asctime)s - %(levelname)s - [%(tool_name)s] %(message)s"
        super().__init__(fmt, datefmt)
        self.default_tool_name = default_tool_name

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with tool name."""
        if not hasattr(record, "tool_name") or record.tool_name is None:
            record.tool_name = self.default_tool_name

        if record.levelname == "WARNING":
            record.levelname = "WARN"

        return super().format(record)
