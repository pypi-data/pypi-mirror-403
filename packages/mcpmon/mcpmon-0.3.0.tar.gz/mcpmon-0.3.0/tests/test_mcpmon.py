"""Unit and integration tests for mcpmon."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcpmon import (
    Logger,
    LogLevel,
    get_change_type_name,
    should_reload,
)


# =============================================================================
# Unit Tests - Logger
# =============================================================================


class TestLogLevel:
    """Test LogLevel enum."""

    def test_level_ordering(self):
        """Log levels should be ordered: QUIET < NORMAL < VERBOSE < DEBUG."""
        assert LogLevel.QUIET < LogLevel.NORMAL
        assert LogLevel.NORMAL < LogLevel.VERBOSE
        assert LogLevel.VERBOSE < LogLevel.DEBUG

    def test_level_values(self):
        """Log levels should have expected numeric values."""
        assert LogLevel.QUIET == 0
        assert LogLevel.NORMAL == 1
        assert LogLevel.VERBOSE == 2
        assert LogLevel.DEBUG == 3


class TestLogger:
    """Test Logger class."""

    def test_default_settings(self):
        """Logger should have sensible defaults."""
        logger = Logger()
        assert logger.level == LogLevel.NORMAL
        assert logger.show_timestamps is False
        assert logger.log_file is None

    def test_format_basic(self):
        """Format should include [mcpmon] prefix."""
        logger = Logger()
        msg = logger._format("test message")
        assert msg.startswith("[mcpmon]")
        assert "test message" in msg

    def test_format_with_pid(self):
        """Format should include PID when provided."""
        logger = Logger()
        msg = logger._format("test", pid=12345)
        assert "pid:12345" in msg

    def test_format_with_timestamps(self):
        """Format should include timestamp when enabled."""
        logger = Logger(show_timestamps=True)
        msg = logger._format("test")
        # Timestamp format is HH:MM:SS
        import re
        assert re.search(r"\d{2}:\d{2}:\d{2}", msg)

    def test_format_without_timestamps(self):
        """Format should not include timestamp when disabled."""
        logger = Logger(show_timestamps=False)
        msg = logger._format("test")
        import re
        # Should not have time pattern in basic format
        assert not re.search(r"\d{2}:\d{2}:\d{2}", msg)

    def test_info_respects_level(self, capsys):
        """info() should respect log level."""
        logger = Logger(level=LogLevel.QUIET)
        logger.info("should not appear")
        captured = capsys.readouterr()
        assert "should not appear" not in captured.err

        logger = Logger(level=LogLevel.NORMAL)
        logger.info("should appear")
        captured = capsys.readouterr()
        assert "should appear" in captured.err

    def test_verbose_respects_level(self, capsys):
        """verbose() should respect log level."""
        logger = Logger(level=LogLevel.NORMAL)
        logger.verbose("should not appear")
        captured = capsys.readouterr()
        assert "should not appear" not in captured.err

        logger = Logger(level=LogLevel.VERBOSE)
        logger.verbose("should appear")
        captured = capsys.readouterr()
        assert "should appear" in captured.err

    def test_debug_respects_level(self, capsys):
        """debug() should respect log level."""
        logger = Logger(level=LogLevel.VERBOSE)
        logger.debug("should not appear")
        captured = capsys.readouterr()
        assert "should not appear" not in captured.err

        logger = Logger(level=LogLevel.DEBUG)
        logger.debug("should appear")
        captured = capsys.readouterr()
        assert "DEBUG:" in captured.err
        assert "should appear" in captured.err

    def test_error_always_shown(self, capsys):
        """error() should always be shown, even at QUIET level."""
        logger = Logger(level=LogLevel.QUIET)
        logger.error("error message")
        captured = capsys.readouterr()
        assert "ERROR:" in captured.err
        assert "error message" in captured.err

    def test_log_file_write(self):
        """Logger should write to file when configured."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            log_path = Path(f.name)

        try:
            logger = Logger(log_file=log_path)
            logger.open_file()
            logger.info("file test message")
            logger.close_file()

            content = log_path.read_text()
            assert "file test message" in content
            # File logs should always have timestamps
            import re
            assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content)
        finally:
            log_path.unlink(missing_ok=True)


# =============================================================================
# Unit Tests - File Watching
# =============================================================================


class TestShouldReload:
    """Test should_reload function."""

    def test_matching_extension(self):
        """Should return True for matching extensions."""
        from watchfiles import Change

        changes = {(Change.modified, "/path/to/file.py")}
        extensions = {"py"}

        reload, matches = should_reload(changes, extensions)
        assert reload is True
        assert len(matches) == 1
        assert matches[0][0] == "modified"
        assert matches[0][1] == "/path/to/file.py"

    def test_non_matching_extension(self):
        """Should return False for non-matching extensions."""
        from watchfiles import Change

        changes = {(Change.modified, "/path/to/file.txt")}
        extensions = {"py"}

        reload, matches = should_reload(changes, extensions)
        assert reload is False
        assert len(matches) == 0

    def test_multiple_extensions(self):
        """Should match multiple configured extensions."""
        from watchfiles import Change

        extensions = {"py", "json", "yaml"}

        for ext in ["py", "json", "yaml"]:
            changes = {(Change.modified, f"/path/to/file.{ext}")}
            reload, _ = should_reload(changes, extensions)
            assert reload is True

    def test_deleted_files_ignored(self):
        """Should not reload for deleted files."""
        from watchfiles import Change

        changes = {(Change.deleted, "/path/to/file.py")}
        extensions = {"py"}

        reload, matches = should_reload(changes, extensions)
        assert reload is False

    def test_added_files_trigger_reload(self):
        """Should reload for newly added files."""
        from watchfiles import Change

        changes = {(Change.added, "/path/to/new_file.py")}
        extensions = {"py"}

        reload, matches = should_reload(changes, extensions)
        assert reload is True
        assert matches[0][0] == "added"

    def test_multiple_changes(self):
        """Should handle multiple file changes."""
        from watchfiles import Change

        changes = {
            (Change.modified, "/path/to/file1.py"),
            (Change.modified, "/path/to/file2.py"),
            (Change.modified, "/path/to/file3.txt"),  # Should not match
        }
        extensions = {"py"}

        reload, matches = should_reload(changes, extensions)
        assert reload is True
        assert len(matches) == 2


class TestGetChangeTypeName:
    """Test get_change_type_name function."""

    def test_change_types(self):
        """Should return human-readable change type names."""
        from watchfiles import Change

        assert get_change_type_name(Change.added) == "added"
        assert get_change_type_name(Change.modified) == "modified"
        assert get_change_type_name(Change.deleted) == "deleted"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for mcpmon."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def dummy_server(self, temp_dir):
        """Create a dummy server script that logs when started."""
        server_script = temp_dir / "server.py"
        server_script.write_text("""
import sys
import time
import signal

print(f"[test-server] Started (pid={__import__('os').getpid()})", file=sys.stderr)
sys.stderr.flush()

def handle_term(sig, frame):
    print("[test-server] Received SIGTERM", file=sys.stderr)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_term)

while True:
    time.sleep(0.1)
""")
        return server_script

    def test_mcpmon_starts_server(self, temp_dir, dummy_server):
        """mcpmon should start the server subprocess."""
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m", "mcpmon",
                "--watch", str(temp_dir),
                "--", sys.executable, str(dummy_server),
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=Path(__file__).parent.parent,
        )

        try:
            # Wait for startup
            time.sleep(2)

            # Check that mcpmon is running
            assert proc.poll() is None, "mcpmon should still be running"

        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_mcpmon_restarts_on_change(self, temp_dir, dummy_server):
        """mcpmon should restart server when watched file changes."""
        # Create a watched file
        watched_file = temp_dir / "watched.py"
        watched_file.write_text("# initial")

        log_file = temp_dir / "mcpmon.log"

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m", "mcpmon",
                "--watch", str(temp_dir),
                "--ext", "py",
                "--log-file", str(log_file),
                "--", sys.executable, str(dummy_server),
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=Path(__file__).parent.parent,
        )

        try:
            # Wait for initial startup
            time.sleep(2)

            # Trigger a reload by modifying the watched file
            watched_file.write_text("# modified")

            # Wait for restart
            time.sleep(2)

            # Check log file for restart message
            log_content = log_file.read_text()
            assert "Restart #1" in log_content, f"Expected restart in log: {log_content}"

        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_mcpmon_ignores_non_matching_files(self, temp_dir, dummy_server):
        """mcpmon should ignore changes to non-matching extensions."""
        # Create a non-matching file
        other_file = temp_dir / "readme.txt"
        other_file.write_text("initial")

        log_file = temp_dir / "mcpmon.log"

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m", "mcpmon",
                "--watch", str(temp_dir),
                "--ext", "py",  # Only watch .py files
                "--debug",
                "--log-file", str(log_file),
                "--", sys.executable, str(dummy_server),
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=Path(__file__).parent.parent,
        )

        try:
            # Wait for initial startup
            time.sleep(2)

            # Modify the non-matching file
            other_file.write_text("modified")

            # Wait a bit
            time.sleep(2)

            # Check that no restart occurred
            log_content = log_file.read_text()
            assert "Restart #1" not in log_content, "Should not restart for .txt file"
            # But should log that it was ignored (debug mode)
            assert "Ignored" in log_content or "readme.txt" in log_content

        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_mcpmon_graceful_shutdown(self, temp_dir, dummy_server):
        """mcpmon should handle SIGTERM gracefully."""
        log_file = temp_dir / "mcpmon.log"

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m", "mcpmon",
                "--watch", str(temp_dir),
                "--log-file", str(log_file),
                "--", sys.executable, str(dummy_server),
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=Path(__file__).parent.parent,
        )

        try:
            # Wait for startup
            time.sleep(2)

            # Send SIGTERM
            proc.terminate()

            # Wait for graceful shutdown
            proc.wait(timeout=5)

            # Check log for shutdown message
            log_content = log_file.read_text()
            assert "Shutdown complete" in log_content

        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("mcpmon did not shut down gracefully")

    def test_mcpmon_timestamps_option(self, temp_dir, dummy_server):
        """--timestamps should add timestamps to output."""
        log_file = temp_dir / "mcpmon.log"

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m", "mcpmon",
                "--watch", str(temp_dir),
                "--timestamps",
                "--log-file", str(log_file),
                "--", sys.executable, str(dummy_server),
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=Path(__file__).parent.parent,
        )

        try:
            time.sleep(2)
        finally:
            proc.terminate()
            proc.wait(timeout=5)

        # Log file always has full timestamps
        import re
        log_content = log_file.read_text()
        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", log_content)


# =============================================================================
# CLI Argument Tests
# =============================================================================


class TestCLI:
    """Test CLI argument parsing."""

    def test_help_flag(self):
        """--help should show usage and exit 0."""
        result = subprocess.run(
            [sys.executable, "-m", "mcpmon", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout

    def test_missing_command_error(self):
        """Should error if no command specified."""
        result = subprocess.run(
            [sys.executable, "-m", "mcpmon", "--watch", "."],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode != 0
        assert "command" in result.stderr.lower() or "No command" in result.stderr

    def test_version_in_help(self):
        """Help should include examples."""
        result = subprocess.run(
            [sys.executable, "-m", "mcpmon", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert "Examples:" in result.stdout
