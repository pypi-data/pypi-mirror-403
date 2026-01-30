#!/usr/bin/env python3
"""
Test server to verify Claude Code accepts BRAND NEW tools mid-session.

This is the critical feasibility test for mcp-gateway.

Test Protocol:
  1. Start with mcpmon: mcpmon -w /tmp -- python tests/test_new_tool_server.py
  2. Session starts with 1 tool: "always_available"
  3. Touch toggle: touch /tmp/add_new_tool.trigger
  4. mcpmon restarts server, sends tools/list_changed
  5. Server now has 2 tools: "always_available" + "brand_new_tool"
  6. Try to call "brand_new_tool"

SUCCESS: brand_new_tool is callable without session restart
FAILURE: brand_new_tool not visible or not callable
"""

import json
import sys
from pathlib import Path

# Toggle file - touch this to ADD a new tool
TOGGLE_FILE = Path("/tmp/add_new_tool.trigger")


def log(msg: str) -> None:
    """Log to stderr (MCP servers must only use stdout for JSON-RPC)."""
    print(f"[new-tool-test] {msg}", file=sys.stderr, flush=True)


def send_message(msg: dict) -> None:
    """Send a JSON-RPC message to stdout."""
    print(json.dumps(msg), flush=True)


def send_notification(method: str, params: dict | None = None) -> None:
    """Send a JSON-RPC notification (no id, no response expected)."""
    msg = {"jsonrpc": "2.0", "method": method}
    if params:
        msg["params"] = params
    send_message(msg)


def get_tools() -> list[dict]:
    """Get tools - always has base tool, conditionally adds new tool."""
    tools = [
        {
            "name": "always_available",
            "description": "This tool is always available from session start",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "A message to echo back"
                    }
                },
                "required": ["message"]
            },
        },
    ]

    if TOGGLE_FILE.exists():
        log(">>> TOGGLE FILE EXISTS - ADDING BRAND NEW TOOL <<<")
        tools.append({
            "name": "brand_new_tool",
            "description": "THIS TOOL WAS ADDED AT RUNTIME - if you can call this, mcp-gateway is feasible!",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "test_input": {
                        "type": "string",
                        "description": "Any input to prove the tool works"
                    }
                },
                "required": ["test_input"]
            },
        })
    else:
        log("Toggle file missing - only base tool available")

    return tools


def handle_tools_call(params: dict) -> dict:
    """Handle a tools/call request."""
    tool_name = params.get("name", "unknown")
    arguments = params.get("arguments", {})

    if tool_name == "always_available":
        message = arguments.get("message", "(no message)")
        return {
            "content": [
                {"type": "text", "text": f"Echo: {message}"}
            ],
            "isError": False,
        }

    elif tool_name == "brand_new_tool":
        test_input = arguments.get("test_input", "(no input)")
        return {
            "content": [
                {"type": "text", "text": f"SUCCESS! brand_new_tool called with: {test_input}\n\nThis proves that Claude Code accepts NEW tools added after session start.\nmcp-gateway is FEASIBLE!"}
            ],
            "isError": False,
        }

    else:
        return {
            "content": [
                {"type": "text", "text": f"Unknown tool: {tool_name}"}
            ],
            "isError": True,
        }


def handle_request(request: dict) -> dict | None:
    """Handle a JSON-RPC request and return response."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    log(f"Received: {method}")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                },
                "serverInfo": {
                    "name": "new-tool-test-server",
                    "version": "1.0.0",
                },
            },
        }

    elif method == "notifications/initialized":
        log("Client initialized - sending tools/list_changed notification")
        send_notification("notifications/tools/list_changed")
        return None

    elif method == "tools/list":
        tools = get_tools()
        tool_names = [t["name"] for t in tools]
        log(f"Returning {len(tools)} tools: {tool_names}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools},
        }

    elif method == "tools/call":
        result = handle_tools_call(params)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    else:
        log(f"Unknown method: {method}")
        if req_id:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return None


def main():
    log("=" * 60)
    log("NEW TOOL FEASIBILITY TEST SERVER")
    log("=" * 60)
    log(f"Toggle file: {TOGGLE_FILE}")
    log(f"Toggle exists: {TOGGLE_FILE.exists()}")
    log("")
    log("To add the new tool:")
    log(f"  touch {TOGGLE_FILE}")
    log("")
    log("Then mcpmon will restart this server and send tools/list_changed")
    log("=" * 60)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            log(f"Invalid JSON: {e}")
            continue

        response = handle_request(request)
        if response:
            send_message(response)


if __name__ == "__main__":
    main()
