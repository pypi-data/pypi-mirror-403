# mcpmon

Hot reload for MCP servers. Like nodemon, but for MCP.

## Install

```bash
pip install mcpmon
```

## Usage

```bash
mcpmon --watch src/ -- python -m my_mcp_server
```

### Options

- `--watch, -w` - Directory to watch (default: current directory)
- `--ext, -e` - File extensions to watch, comma-separated (default: py)

### Examples

```bash
# Watch current directory for .py changes
mcpmon -- python server.py

# Watch src/ for .py and .json changes
mcpmon --watch src/ --ext py,json -- python -m myserver

# With crucible-mcp
mcpmon --watch src/crucible/ -- crucible-mcp

# With sage-mcp
mcpmon --watch ~/.sage/ --ext py,yaml -- sage-mcp
```

## How it works

1. Starts your MCP server as a subprocess
2. Watches specified directory for file changes
3. On change: SIGTERM → wait 2s → SIGKILL → restart
4. Claude Code automatically reconnects to the restarted server
