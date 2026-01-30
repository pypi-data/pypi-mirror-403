"""mcpmon: Hot reload for MCP servers. Like nodemon, but for MCP."""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from watchfiles import Change, watch

from .log import Logger, LogLevel

# Re-export for backward compatibility
__all__ = [
    "Logger",
    "LogLevel",
    "log",
    "get_change_type_name",
    "should_reload",
    "send_tools_list_changed",
    "terminate_process",
    "start_process",
    "main",
]

__version__ = "1.0.0"

# Global logger instance
log = Logger()


# =============================================================================
# Process Management (Single Server Mode)
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
    """Start the MCP server process with stdout capture for notification injection."""
    log.debug(f"Spawning: {' '.join(command)}")
    proc = subprocess.Popen(
        command,
        stdin=sys.stdin,  # Pass through stdin directly
        stdout=subprocess.PIPE,  # Capture stdout for forwarding
        stderr=sys.stderr,  # Pass through stderr
    )
    # Start forwarding thread
    threading.Thread(target=forward_stdout, args=(proc,), daemon=True).start()
    log.info(f"Started: {' '.join(command)}", proc.pid)
    return proc


def forward_stdout(proc: subprocess.Popen) -> None:
    """Forward subprocess stdout to our stdout, line by line."""
    try:
        for line in proc.stdout:
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
    except (BrokenPipeError, OSError):
        pass  # Process terminated


def send_tools_list_changed() -> None:
    """Send tools/list_changed notification to client."""
    notification = json.dumps(
        {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}
    )
    sys.stdout.write(notification + "\n")
    sys.stdout.flush()
    log.info("Sent tools/list_changed notification")


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


def should_reload(
    changes: set, extensions: set[str]
) -> tuple[bool, list[tuple[str, str]]]:
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
        usage="mcpmon [options] --watch <dir> -- <command>\n       mcpmon --config <file>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  Single server:  mcpmon --watch src/ -- python server.py
  Multi gateway:  mcpmon --config .mcpmon.yaml

Logging levels:
  --quiet       Only errors
  (default)     Start, stop, restart events
  --verbose     + file change details
  --debug       + everything

Examples:
  # Single server with hot reload
  mcpmon --watch src/ -- python -m my_server
  mcpmon -w . -e py,json --verbose -- node server.js

  # Multi-server gateway mode
  mcpmon --config .mcpmon.yaml
  mcpmon -c ~/.config/mcpmon/config.yaml
""",
    )

    # Mode selection
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Config file for multi-server gateway mode",
    )

    # Watch options (single server mode)
    parser.add_argument(
        "--watch",
        "-w",
        type=str,
        default=".",
        help="Directory to watch (default: current directory)",
    )
    parser.add_argument(
        "--ext",
        "-e",
        type=str,
        default="py",
        help="File extensions to watch, comma-separated (default: py)",
    )

    # Logging options
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show errors",
    )
    log_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show file change details",
    )
    log_group.add_argument(
        "--debug",
        action="store_true",
        help="Show all debug output",
    )

    parser.add_argument(
        "--timestamps",
        "-t",
        action="store_true",
        help="Include timestamps in output",
    )
    parser.add_argument(
        "--log-file",
        "-l",
        type=Path,
        help="Also write logs to file (always includes timestamps)",
    )

    # Notification options
    parser.add_argument(
        "--notify-tools-changed",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Send tools/list_changed notification after restart (default: on)",
    )

    # Command (single server mode)
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run (after --)",
    )

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"mcpmon {__version__}",
    )

    args = parser.parse_args()

    # Remove leading -- from command if present
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]

    # Validate: need either --config or command
    if not args.config and not args.command:
        parser.error(
            "No mode specified. Use:\n"
            "  Single server: mcpmon --watch src/ -- <command>\n"
            "  Multi gateway: mcpmon --config <file>"
        )

    return args


# =============================================================================
# Single Server Mode (Original Behavior)
# =============================================================================


def run_single_server(args: argparse.Namespace) -> None:
    """Run mcpmon in single-server mode (original behavior)."""
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
                    rel_path = (
                        Path(path).relative_to(watch_path)
                        if path.startswith(str(watch_path))
                        else path
                    )
                    log.verbose(f"File {change_type}: {rel_path}")

                log.info("Restarting...", proc.pid)
                terminate_process(proc)
                proc = start_process(command)
                restart_count += 1
                log.info(f"Restart #{restart_count} complete", proc.pid)

                # Send notification after brief delay for subprocess initialization
                if args.notify_tools_changed:
                    time.sleep(0.1)
                    send_tools_list_changed()
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

    if args.config:
        # Multi-server gateway mode
        from .gateway import run_gateway

        log.info(f"Starting gateway mode with config: {args.config}")
        run_gateway(args.config, log)
    else:
        # Single-server mode (original behavior)
        run_single_server(args)


if __name__ == "__main__":
    main()
