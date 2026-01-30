"""Logging infrastructure for mcpmon."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import TextIO


class LogLevel(IntEnum):
    """Logging verbosity levels."""

    QUIET = 0  # Only errors
    NORMAL = 1  # Start, stop, restart events (default)
    VERBOSE = 2  # + file change details
    DEBUG = 3  # + everything


@dataclass
class Logger:
    """Structured logger with levels, timestamps, and optional file output."""

    level: LogLevel = LogLevel.NORMAL
    show_timestamps: bool = False
    log_file: Path | None = None
    _file_handle: TextIO | None = None

    def _format(self, msg: str, pid: int | None = None) -> str:
        """Format a log message with optional timestamp and PID."""
        parts = ["[mcpmon"]

        if self.show_timestamps:
            parts.append(datetime.now().strftime("%H:%M:%S"))

        if pid is not None:
            parts.append(f"pid:{pid}")

        prefix = " ".join(parts) + "]"
        return f"{prefix} {msg}"

    def _write(self, msg: str) -> None:
        """Write to stderr and optionally to log file."""
        print(msg, file=sys.stderr)

        if self._file_handle:
            # Always include timestamp in file logs
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._file_handle.write(f"[{ts}] {msg}\n")
            self._file_handle.flush()

    def open_file(self) -> None:
        """Open log file if configured."""
        if self.log_file:
            self._file_handle = self.log_file.open("a")

    def close_file(self) -> None:
        """Close log file if open."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

    # --- Log methods by level ---

    def error(self, msg: str, pid: int | None = None) -> None:
        """Always shown (QUIET+)."""
        self._write(self._format(f"ERROR: {msg}", pid))

    def info(self, msg: str, pid: int | None = None) -> None:
        """Start, stop, restart events (NORMAL+)."""
        if self.level >= LogLevel.NORMAL:
            self._write(self._format(msg, pid))

    def verbose(self, msg: str, pid: int | None = None) -> None:
        """File change details (VERBOSE+)."""
        if self.level >= LogLevel.VERBOSE:
            self._write(self._format(msg, pid))

    def debug(self, msg: str, pid: int | None = None) -> None:
        """Everything else (DEBUG only)."""
        if self.level >= LogLevel.DEBUG:
            self._write(self._format(f"DEBUG: {msg}", pid))
