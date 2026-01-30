"""Tests for mcpmon gateway mode."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcpmon.config import GatewayConfig, ServerConfig, load_config


# =============================================================================
# Config Tests
# =============================================================================


class TestConfig:
    """Test configuration loading."""

    def test_load_simple_config(self, tmp_path):
        """Load a simple config with just commands."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
servers:
  server1:
    command: echo
"""
        )

        config = load_config(config_file)
        assert "server1" in config.servers
        assert config.servers["server1"].command == "echo"

    def test_load_config_with_args(self, tmp_path):
        """Load config with command args."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
servers:
  myserver:
    command: python
    args: ["-m", "my_module"]
"""
        )

        config = load_config(config_file)
        assert config.servers["myserver"].command == "python"
        assert config.servers["myserver"].args == ["-m", "my_module"]

    def test_load_config_with_watch(self, tmp_path):
        """Load config with watch directory."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
servers:
  myserver:
    command: server
    watch: ./src
    extensions: py,json
"""
        )

        config = load_config(config_file)
        assert config.servers["myserver"].watch == "./src"
        assert config.servers["myserver"].extensions == "py,json"

    def test_load_config_with_env(self, tmp_path, monkeypatch):
        """Load config with environment variables."""
        monkeypatch.setenv("TEST_API_KEY", "secret123")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
servers:
  myserver:
    command: server
    env:
      DEBUG: "true"
      API_KEY: "${TEST_API_KEY}"
"""
        )

        config = load_config(config_file)
        assert config.servers["myserver"].env["DEBUG"] == "true"
        assert config.servers["myserver"].env["API_KEY"] == "secret123"

    def test_load_config_with_settings(self, tmp_path):
        """Load config with global settings."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
settings:
  log_level: debug
  notify_on_change: false

servers:
  myserver:
    command: server
"""
        )

        config = load_config(config_file)
        assert config.log_level == "debug"
        assert config.notify_on_change is False

    def test_load_multiple_servers(self, tmp_path):
        """Load config with multiple servers."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
servers:
  sage:
    command: sage-mcp
  crucible:
    command: crucible-mcp
  other:
    command: other-mcp
"""
        )

        config = load_config(config_file)
        assert len(config.servers) == 3
        assert "sage" in config.servers
        assert "crucible" in config.servers
        assert "other" in config.servers


# =============================================================================
# Gateway Integration Tests
# =============================================================================


class TestGatewayIntegration:
    """Integration tests for gateway mode."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def dummy_mcp_server(self, temp_dir):
        """Create a dummy MCP server script."""
        server_script = temp_dir / "dummy_server.py"
        server_script.write_text(
            '''
import json
import sys

def send(msg):
    print(json.dumps(msg), flush=True)

def log(msg):
    print(f"[dummy] {msg}", file=sys.stderr, flush=True)

TOOLS = [
    {"name": "test_tool", "description": "A test tool", "inputSchema": {"type": "object"}},
]

for line in sys.stdin:
    request = json.loads(line.strip())
    method = request.get("method", "")
    req_id = request.get("id")

    log(f"Got: {method}")

    if method == "initialize":
        send({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "dummy", "version": "1.0.0"}
            }
        })
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        send({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": f"Called {tool_name}"}], "isError": False}
        })
    elif method == "ping":
        send({"jsonrpc": "2.0", "id": req_id, "result": {}})
'''
        )
        return server_script

    @pytest.mark.timeout(15)
    def test_gateway_starts_with_config(self, temp_dir, dummy_mcp_server):
        """Gateway should start and list aggregated tools."""
        # Create config
        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            f"""
servers:
  backend1:
    command: python
    args: ["{dummy_mcp_server}"]
"""
        )

        # Start gateway
        proc = subprocess.Popen(
            [sys.executable, "-m", "mcpmon", "--config", str(config_file), "--debug"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent,
        )

        try:
            # Give gateway time to start backends
            time.sleep(1)

            # Send initialize
            init_request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                }
            )
            proc.stdin.write((init_request + "\n").encode())
            proc.stdin.flush()

            # Read response with timeout
            import select
            ready, _, _ = select.select([proc.stdout], [], [], 5)
            assert ready, "No response from gateway"

            response = proc.stdout.readline().decode()
            data = json.loads(response)
            assert data.get("result", {}).get("serverInfo", {}).get("name") == "mcpmon-gateway"

            # Send tools/list
            tools_request = json.dumps(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            )
            proc.stdin.write((tools_request + "\n").encode())
            proc.stdin.flush()

            # Read tools response (may need to skip notification)
            for _ in range(10):  # Max 10 messages
                ready, _, _ = select.select([proc.stdout], [], [], 5)
                if not ready:
                    break
                response = proc.stdout.readline().decode()
                if not response:
                    break
                data = json.loads(response)
                if data.get("id") == 2:
                    break

            tools = data.get("result", {}).get("tools", [])
            assert len(tools) == 1
            assert tools[0]["name"] == "test_tool"  # Single backend = no prefix

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    @pytest.mark.timeout(15)
    def test_gateway_routes_tool_calls(self, temp_dir, dummy_mcp_server):
        """Gateway should route tool calls to correct backend."""
        import select

        config_file = temp_dir / "config.yaml"
        config_file.write_text(
            f"""
servers:
  mybackend:
    command: python
    args: ["{dummy_mcp_server}"]
"""
        )

        proc = subprocess.Popen(
            [sys.executable, "-m", "mcpmon", "--config", str(config_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent,
        )

        try:
            # Give gateway time to start
            time.sleep(1)

            # Initialize
            init_request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {},
                }
            )
            proc.stdin.write((init_request + "\n").encode())
            proc.stdin.flush()

            # Read init response
            select.select([proc.stdout], [], [], 5)
            proc.stdout.readline()

            # Call tool with prefixed name
            call_request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "mybackend__test_tool",
                        "arguments": {},
                    },
                }
            )
            proc.stdin.write((call_request + "\n").encode())
            proc.stdin.flush()

            # Read response (skip notifications)
            data = {}
            for _ in range(10):
                ready, _, _ = select.select([proc.stdout], [], [], 5)
                if not ready:
                    break
                response = proc.stdout.readline().decode()
                if not response:
                    break
                data = json.loads(response)
                if data.get("id") == 2:
                    break

            result = data.get("result", {})
            assert result.get("isError") is False
            content = result.get("content", [])
            assert len(content) == 1
            assert "test_tool" in content[0].get("text", "")

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


# =============================================================================
# CLI Tests
# =============================================================================


class TestGatewayCLI:
    """Test gateway CLI options."""

    def test_config_flag_in_help(self):
        """--config should be documented in help."""
        result = subprocess.run(
            [sys.executable, "-m", "mcpmon", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "--config" in result.stdout
        assert "gateway" in result.stdout.lower()

    def test_version_flag(self):
        """--version should show version."""
        result = subprocess.run(
            [sys.executable, "-m", "mcpmon", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "1.0.0" in result.stdout
