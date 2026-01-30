#!/usr/bin/env python3
"""mcpmon: Hot reload for MCP servers. Like nodemon, but for MCP."""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import TextIO

from watchfiles import Change, watch


# =============================================================================
# Logging
# =============================================================================


class LogLevel(IntEnum):
    """Logging verbosity levels."""
    QUIET = 0    # Only errors
    NORMAL = 1   # Start, stop, restart events (default)
    VERBOSE = 2  # + file change details
    DEBUG = 3    # + everything


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


# Global logger instance
log = Logger()


# =============================================================================
# Process Management
# =============================================================================


def terminate_process(proc: subprocess.Popen) -> None:
    """Gracefully terminate process: SIGTERM, wait 2s, SIGKILL."""
    if proc.poll() is not None:
        log.debug(f"Process already exited with code {proc.returncode}", proc.pid)
        return

    log.debug("Sending SIGTERM", proc.pid)
    proc.terminate()

    try:
        proc.wait(timeout=2)
        log.debug(f"Process exited with code {proc.returncode}", proc.pid)
    except subprocess.TimeoutExpired:
        log.debug("SIGTERM timeout, sending SIGKILL", proc.pid)
        proc.kill()
        proc.wait()
        log.debug("Process killed", proc.pid)


def start_process(command: list[str]) -> subprocess.Popen:
    """Start the MCP server process."""
    log.debug(f"Spawning: {' '.join(command)}")
    proc = subprocess.Popen(command)
    log.info(f"Started: {' '.join(command)}", proc.pid)
    return proc


# =============================================================================
# File Watching
# =============================================================================


def get_change_type_name(change_type: Change) -> str:
    """Human-readable change type."""
    return {
        Change.added: "added",
        Change.modified: "modified",
        Change.deleted: "deleted",
    }.get(change_type, "changed")


def should_reload(changes: set, extensions: set[str]) -> tuple[bool, list[tuple[str, str]]]:
    """Check if any changed file matches our extensions.

    Returns:
        (should_reload, list of (change_type_name, path) for matching files)
    """
    matching = []
    for change_type, path in changes:
        if change_type in (Change.added, Change.modified):
            if Path(path).suffix.lstrip(".") in extensions:
                matching.append((get_change_type_name(change_type), path))

    return bool(matching), matching


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hot reload wrapper for MCP servers",
        usage="mcpmon [options] --watch <dir> -- <command>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Logging levels:
  --quiet       Only errors
  (default)     Start, stop, restart events
  --verbose     + file change details
  --debug       + everything

Examples:
  mcpmon --watch src/ -- python -m my_server
  mcpmon -w . -e py,json --verbose -- node server.js
  mcpmon --timestamps --log-file mcpmon.log -- python server.py
""",
    )

    # Watch options
    parser.add_argument(
        "--watch", "-w",
        type=str,
        default=".",
        help="Directory to watch (default: current directory)",
    )
    parser.add_argument(
        "--ext", "-e",
        type=str,
        default="py",
        help="File extensions to watch, comma-separated (default: py)",
    )

    # Logging options
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only show errors",
    )
    log_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show file change details",
    )
    log_group.add_argument(
        "--debug",
        action="store_true",
        help="Show all debug output",
    )

    parser.add_argument(
        "--timestamps", "-t",
        action="store_true",
        help="Include timestamps in output",
    )
    parser.add_argument(
        "--log-file", "-l",
        type=Path,
        help="Also write logs to file (always includes timestamps)",
    )

    # Command
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run (after --)",
    )

    args = parser.parse_args()

    # Remove leading -- from command if present
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]

    if not args.command:
        parser.error("No command specified. Use: mcpmon --watch src/ -- <command>")

    return args


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    args = parse_args()

    # Configure logger
    if args.quiet:
        log.level = LogLevel.QUIET
    elif args.verbose:
        log.level = LogLevel.VERBOSE
    elif args.debug:
        log.level = LogLevel.DEBUG

    log.show_timestamps = args.timestamps
    log.log_file = args.log_file
    log.open_file()

    watch_path = Path(args.watch).resolve()
    extensions = {ext.strip().lstrip(".") for ext in args.ext.split(",")}
    command = args.command

    log.info(f"Watching {watch_path} for .{', .'.join(sorted(extensions))} changes")
    log.debug(f"Log level: {log.level.name}")
    if log.log_file:
        log.debug(f"Log file: {log.log_file}")

    proc = start_process(command)
    restart_count = 0

    # Handle signals gracefully
    def signal_handler(signum, frame):
        sig_name = signal.Signals(signum).name
        log.info(f"Received {sig_name}, shutting down...")
        terminate_process(proc)
        log.info(f"Shutdown complete (restarts: {restart_count})")
        log.close_file()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        for changes in watch(watch_path):
            reload_needed, matching_files = should_reload(changes, extensions)

            if reload_needed:
                # Log each changed file at verbose level
                for change_type, path in matching_files:
                    rel_path = Path(path).relative_to(watch_path) if path.startswith(str(watch_path)) else path
                    log.verbose(f"File {change_type}: {rel_path}")

                log.info("Restarting...", proc.pid)
                terminate_process(proc)
                proc = start_process(command)
                restart_count += 1
                log.info(f"Restart #{restart_count} complete", proc.pid)
            else:
                # Log ignored changes at debug level
                for change_type, path in changes:
                    log.debug(f"Ignored {get_change_type_name(change_type)}: {path}")

    except KeyboardInterrupt:
        pass
    finally:
        terminate_process(proc)
        log.info(f"Exited (total restarts: {restart_count})")
        log.close_file()


if __name__ == "__main__":
    main()
