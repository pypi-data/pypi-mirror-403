# mcpmon

Hot reload for MCP servers. Like nodemon, but for MCP.

## Install

```bash
# Bun (recommended)
bunx mcpmon

# Or install globally
bun install -g mcpmon

# Python alternative
pip install mcpmon

# Or download binary from GitHub releases (no dependencies)
```

## Usage

```bash
mcpmon --watch src/ -- python -m my_mcp_server
```

### Options

| Option | Description |
|--------|-------------|
| `-w, --watch <dir>` | Directory to watch (default: `.`) |
| `-e, --ext <exts>` | Extensions to watch, comma-separated (default: `py`) |
| `-q, --quiet` | Only show errors |
| `-v, --verbose` | Show file change details |
| `--debug` | Show all debug output |
| `-t, --timestamps` | Include timestamps in output |
| `-l, --log-file <file>` | Also write logs to file |

### Logging Levels

```
--quiet       Only errors
(default)     Start, stop, restart events + PID
--verbose     + file change details
--debug       + everything (ignored files, spawning, exit codes)
```

### Examples

```bash
# Basic usage - watch current directory for .py changes
mcpmon -- python server.py

# Watch src/ for .py and .json changes
mcpmon --watch src/ --ext py,json -- python -m myserver

# With timestamps and verbose output
mcpmon --timestamps --verbose -- python server.py

# Log to file for debugging
mcpmon --debug --log-file mcpmon.log -- python server.py

# With crucible-mcp
mcpmon --watch src/crucible/ -- crucible-mcp

# With sage-mcp
mcpmon --watch sage/ --ext py -- python -m sage.mcp_server
```

### Sample Output

```
[mcpmon 16:08:50] Watching sage for .py changes
[mcpmon 16:08:50 pid:53307] Started: python -m sage.mcp_server
[mcpmon 16:08:54 pid:53307] Restarting...
[mcpmon 16:08:54 pid:53411] Started: python -m sage.mcp_server
[mcpmon 16:08:54 pid:53411] Restart #1 complete
[mcpmon 16:08:57] Received SIGTERM, shutting down...
[mcpmon 16:08:57] Shutdown complete (restarts: 1)
```

## MCP Config

Use mcpmon in your `.mcp.json` for hot reload during development:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "mcpmon",
      "args": ["--watch", "src/", "--", "python", "-m", "my_server"]
    }
  }
}
```

## How it works

1. Starts your MCP server as a subprocess
2. Watches specified directory for file changes
3. On change: SIGTERM → wait 2s → SIGKILL → restart
4. Claude Code automatically reconnects to the restarted server

## Dual Implementation

mcpmon ships as both:
- **Bun/TypeScript** (`mcpmon.ts`) - Zero dependencies, fast startup
- **Python** (`mcpmon.py`) - Uses `watchfiles` for robust file watching

Both implementations have feature parity.

## Development

```bash
# Install dev dependencies (Python)
pip install -e ".[dev]"

# Run Python tests (27 tests)
pytest tests/ -v

# Run Bun/TS tests (12 tests)
bun test
```
