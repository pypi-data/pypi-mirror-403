# mcpmon Architecture

## Gateway Mode

The gateway aggregates multiple MCP backend servers behind a single connection to Claude Code.

```
Claude Code <--stdio--> mcpmon gateway <--stdio--> backend 1
                                       <--stdio--> backend 2
                                       <--stdio--> backend n
```

### Tool Routing

With multiple backends, tools are prefixed: `backend_name::tool_name` (C++/Rust-style namespacing). With a single backend, tools pass through unmodified for seamless drop-in usage.

### Backend Lifecycle

1. Gateway starts serving immediately (responds to MCP handshake)
2. Backends initialize in parallel (non-blocking)
3. `notifications/tools/list_changed` sent when backends become ready
4. File watchers restart individual backends on code changes
5. Config watcher hot-adds/removes backends

## Critical: stdin Reading Pattern

The gateway uses **synchronous stdin reading in a dedicated thread** rather than asyncio executors. This is intentional and required for Claude Code compatibility.

### What NOT to do

```python
# DON'T - causes Claude Code to hang after permission prompt
executor = ThreadPoolExecutor(max_workers=1)
while True:
    line = await asyncio.wait_for(
        loop.run_in_executor(executor, sys.stdin.readline),
        timeout=1.0
    )
```

### Correct Pattern

```python
# DO - works correctly with Claude Code
import queue
import threading

stdin_queue = queue.Queue()

def stdin_reader():
    for line in sys.stdin:
        stdin_queue.put(line)
    stdin_queue.put(None)  # EOF

threading.Thread(target=stdin_reader, daemon=True).start()

while True:
    try:
        line = stdin_queue.get_nowait()
    except queue.Empty:
        await asyncio.sleep(0.01)  # Yield to event loop
        continue
    # process line...
```

### Why This Matters

The asyncio executor pattern (`run_in_executor` + `wait_for` with timeout) causes Claude Code to hang indefinitely after the user approves the tool permission prompt. The `tools/call` request never reaches the gateway.

Observed behavior:
- `initialize` → works
- `notifications/initialized` → works
- `tools/list` → works, tools shown in Claude Code
- User clicks "Yes" on permission prompt
- `tools/call` → **never sent** (hangs forever)

### Tested Patterns

| Pattern | Result |
|---------|--------|
| Direct MCP server (sync `for line in sys.stdin`) | ✅ Works |
| Passthrough with sync stdin + thread for stdout | ✅ Works |
| Passthrough with asyncio executor for stdin | ❌ Hangs |

Root cause in Claude Code is unknown. Discovered through debugging, January 2026.
