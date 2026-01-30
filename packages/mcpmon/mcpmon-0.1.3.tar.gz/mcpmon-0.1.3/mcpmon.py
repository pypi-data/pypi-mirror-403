#!/usr/bin/env python3
"""mcpmon: Hot reload for MCP servers. Like nodemon, but for MCP."""

import argparse
import signal
import subprocess
import sys
from pathlib import Path

from watchfiles import watch, Change


def parse_args():
    parser = argparse.ArgumentParser(
        description="Hot reload wrapper for MCP servers",
        usage="mcpmon --watch <dir> [--ext <ext>] -- <command>",
    )
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


def terminate_process(proc: subprocess.Popen) -> None:
    """Gracefully terminate process: SIGTERM, wait 2s, SIGKILL."""
    if proc.poll() is not None:
        return

    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def start_process(command: list[str]) -> subprocess.Popen:
    """Start the MCP server process."""
    return subprocess.Popen(command)


def should_reload(changes: set, extensions: set[str]) -> bool:
    """Check if any changed file matches our extensions."""
    for change_type, path in changes:
        if change_type in (Change.added, Change.modified) and Path(path).suffix.lstrip(".") in extensions:
            return True
    return False


def main():
    args = parse_args()

    watch_path = Path(args.watch).resolve()
    extensions = {ext.strip().lstrip(".") for ext in args.ext.split(",")}
    command = args.command

    print(f"[mcpmon] Watching {watch_path} for .{', .'.join(extensions)} changes")
    print(f"[mcpmon] Running: {' '.join(command)}")

    proc = start_process(command)

    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n[mcpmon] Shutting down...")
        terminate_process(proc)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        for changes in watch(watch_path):
            if should_reload(changes, extensions):
                changed_files = [p for _, p in changes]
                print(f"[mcpmon] Change detected: {', '.join(changed_files)}")
                print("[mcpmon] Restarting...")

                terminate_process(proc)
                proc = start_process(command)

                print("[mcpmon] Server restarted")
    except KeyboardInterrupt:
        pass
    finally:
        terminate_process(proc)


if __name__ == "__main__":
    main()
