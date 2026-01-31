"""Custom log handlers for optix-mcp-server."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


class UnbufferedFileHandler(logging.FileHandler):
    """File handler that flushes after every write for real-time monitoring.

    This handler ensures log entries appear immediately in the file,
    making it compatible with `tail -f` for real-time monitoring.
    """

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = "utf-8",
        delay: bool = False,
    ):
        log_dir = Path(filename).parent
        if log_dir and not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(
                    f"Warning: Could not create log directory {log_dir}: {e}",
                    file=sys.stderr,
                )
                raise

        super().__init__(filename, mode, encoding, delay)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record and flush immediately."""
        try:
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)


class StderrFallbackHandler(logging.StreamHandler):
    """Handler that writes to stderr as fallback when file logging fails."""

    def __init__(self):
        super().__init__(sys.stderr)
