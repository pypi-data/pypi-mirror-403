"""Multi-server gateway mode for mcpmon."""

from __future__ import annotations

import asyncio
import atexit
import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from watchfiles import awatch, Change

from .config import GatewayConfig, ServerConfig, load_config
from .log import Logger, LogLevel


class BackendState(Enum):
    """Backend initialization state."""

    STARTING = "starting"
    READY = "ready"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class Backend:
    """A running backend MCP server."""

    name: str
    config: ServerConfig
    process: subprocess.Popen
    tools: list[dict] = field(default_factory=list)
    state: BackendState = BackendState.STARTING
    error: str | None = None
    _read_buffer: str = ""


class Gateway:
    """MCP gateway that aggregates multiple backend servers."""

    def __init__(self, config: GatewayConfig, logger: Logger):
        self.config = config
        self.log = logger
        self.backends: dict[str, Backend] = {}
        self.request_id = 0
        self.pending_requests: dict[int, asyncio.Future] = {}
        self.initialized = False
        self._shutdown = False
        self._backend_init_tasks: dict[str, asyncio.Task] = {}

        # Register cleanup on exit
        atexit.register(self._atexit_cleanup)

    def _atexit_cleanup(self):
        """Emergency cleanup on interpreter exit."""
        for name, backend in list(self.backends.items()):
            try:
                if backend.process.poll() is None:
                    backend.process.terminate()
                    try:
                        backend.process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        backend.process.kill()
            except Exception:
                pass

    async def start(self):
        """Start serving immediately, init backends in parallel."""
        self.log.info(f"Gateway starting with {len(self.config.servers)} backend(s)")
        for name in self.config.servers:
            self.log.debug(f"  - {name}")

        # Start serving IMMEDIATELY (handles MCP handshake)
        serve_task = asyncio.create_task(self._serve())

        # Initialize all backends in PARALLEL (non-blocking)
        init_tasks = []
        for name, server_config in self.config.servers.items():
            task = asyncio.create_task(self._init_backend_safe(name, server_config))
            self._backend_init_tasks[name] = task
            init_tasks.append(task)

        # Wait for all backends to finish init (success or failure)
        if init_tasks:
            await asyncio.gather(*init_tasks)

        # Clear init tasks dict
        self._backend_init_tasks.clear()

        # Log summary
        ready = [n for n, b in self.backends.items() if b.state == BackendState.READY]
        failed = [n for n, b in self.backends.items() if b.state == BackendState.FAILED]
        if ready:
            self.log.info(f"Backends ready: {', '.join(ready)}")
        if failed:
            self.log.error(f"Backends failed: {', '.join(failed)}")

        # Notify client that tools are available
        if self.initialized and ready and self.config.notify_on_change:
            self._send_tools_list_changed()

        # Start config file watcher
        if self.config.config_path:
            asyncio.create_task(self._watch_config())

        # Start backend file watchers for ready backends
        for name, backend in self.backends.items():
            if backend.state == BackendState.READY and backend.config.watch:
                asyncio.create_task(self._watch_backend_files(backend))

        # Wait for serve to complete (shutdown)
        await serve_task

    async def _init_backend_safe(self, name: str, config: ServerConfig):
        """Initialize a backend, catching errors."""
        try:
            await self.start_backend(name, config)
            # Notify client if already initialized (late backend start)
            if self.initialized and self.config.notify_on_change:
                self._send_tools_list_changed()
        except Exception as e:
            self.log.error(f"Failed to start backend '{name}': {e}")

    async def start_backend(self, name: str, config: ServerConfig):
        """Start a single backend server."""
        command = config.command
        if isinstance(command, str):
            command = [command]
        if config.args:
            command = list(command) + list(config.args)

        env = {**os.environ, **config.env}

        self.log.debug(f"[{name}] Starting: {' '.join(command)}")

        # Start process in new process group for reliable cleanup
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            env=env,
            start_new_session=True,  # New process group
        )

        backend = Backend(name=name, config=config, process=proc, state=BackendState.STARTING)
        self.backends[name] = backend

        # Initialize MCP connection
        try:
            await self._initialize_backend(backend)

            # Fetch tools
            response = await self._backend_request(backend, "tools/list", {})
            backend.tools = response.get("result", {}).get("tools", [])
            backend.state = BackendState.READY

            tool_names = [t.get("name", "?") for t in backend.tools]
            self.log.info(f"[{name}] Started (pid:{proc.pid})")
            self.log.verbose(f"[{name}] Tools ({len(backend.tools)}): {', '.join(tool_names)}")
        except Exception as e:
            self.log.error(f"[{name}] Initialization failed: {e}")
            backend.state = BackendState.FAILED
            backend.error = str(e)
            self._terminate_process(proc)
            raise

    def _terminate_process(self, proc: subprocess.Popen, timeout: float = 2.0):
        """Terminate a process reliably."""
        if proc.poll() is not None:
            return  # Already dead

        # Try graceful termination first
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Force kill the process group
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                # Process already gone or no permission
                pass
            try:
                proc.kill()
                proc.wait(timeout=1)
            except Exception:
                pass

    async def stop_backend(self, name: str):
        """Stop a backend server."""
        if name not in self.backends:
            return

        backend = self.backends[name]
        self.log.debug(f"[{name}] Stopping (pid:{backend.process.pid})")

        self._terminate_process(backend.process)
        backend.state = BackendState.STOPPED

        del self.backends[name]
        self.log.info(f"[{name}] Stopped")

    async def restart_backend(self, name: str):
        """Restart a single backend."""
        if name not in self.backends:
            return

        config = self.backends[name].config
        self.log.info(f"[{name}] Restarting...")

        await self.stop_backend(name)
        await asyncio.sleep(0.1)

        try:
            await self.start_backend(name, config)
        except Exception as e:
            self.log.error(f"[{name}] Restart failed: {e}")

        # Notify client
        if self.config.notify_on_change and self.initialized:
            self._send_tools_list_changed()

    async def _initialize_backend(self, backend: Backend):
        """Send MCP initialize handshake to backend."""
        response = await self._backend_request(
            backend,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcpmon-gateway", "version": "1.0.0"},
            },
        )

        # Send initialized notification
        self._backend_notify(backend, "notifications/initialized", {})

        return response

    async def _backend_request(
        self, backend: Backend, method: str, params: dict
    ) -> dict:
        """Send JSON-RPC request to backend and wait for response."""
        self.request_id += 1
        request_id = self.request_id

        request = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}

        # Send request
        request_line = json.dumps(request) + "\n"
        backend.process.stdin.write(request_line.encode())
        backend.process.stdin.flush()

        # Read response (blocking, but backends should respond quickly)
        # For robustness, we read with a timeout
        response = await self._read_backend_response(backend, request_id)
        return response

    async def _read_backend_response(
        self, backend: Backend, expected_id: int, timeout: float = 30.0
    ) -> dict:
        """Read response from backend for a specific request ID."""
        loop = asyncio.get_event_loop()

        async def read_line():
            return await loop.run_in_executor(
                None, backend.process.stdout.readline
            )

        deadline = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < deadline:
            try:
                line = await asyncio.wait_for(
                    read_line(), timeout=deadline - asyncio.get_event_loop().time()
                )
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"[{backend.name}] Timeout waiting for response to request {expected_id}"
                )

            if not line:
                raise ConnectionError(f"[{backend.name}] Backend closed connection")

            line = line.decode().strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                self.log.debug(f"[{backend.name}] Invalid JSON: {line[:100]}")
                continue

            # Check if this is our response
            if msg.get("id") == expected_id:
                return msg

            # It's a notification or response to different request
            # For now, just log and continue
            if "method" in msg and "id" not in msg:
                self.log.debug(f"[{backend.name}] Notification: {msg.get('method')}")

        raise TimeoutError(f"[{backend.name}] Timeout waiting for response")

    def _backend_notify(self, backend: Backend, method: str, params: dict):
        """Send JSON-RPC notification to backend (no response expected)."""
        notification = {"jsonrpc": "2.0", "method": method, "params": params}
        line = json.dumps(notification) + "\n"
        backend.process.stdin.write(line.encode())
        backend.process.stdin.flush()

    def _aggregate_tools(self) -> list[dict]:
        """Aggregate tools from all ready backends with prefixed names."""
        all_tools = []

        # If single backend, pass tools through unmodified (like direct MCP)
        single_backend = len(self.backends) == 1

        for name, backend in self.backends.items():
            # Only include tools from ready backends
            if backend.state != BackendState.READY:
                continue

            for tool in backend.tools:
                if single_backend:
                    # Pass through unmodified
                    all_tools.append(tool)
                else:
                    prefixed_tool = {
                        **tool,
                        "name": f"{name}::{tool['name']}",
                        "description": f"[{name}] {tool.get('description', '')}",
                    }
                    all_tools.append(prefixed_tool)

        return all_tools

    async def _route_tool_call(self, prefixed_name: str, arguments: dict) -> dict:
        """Route a tool call to the correct backend."""
        # Single backend mode: tool name not prefixed
        if len(self.backends) == 1:
            backend_name = list(self.backends.keys())[0]
            tool_name = prefixed_name
        elif "::" not in prefixed_name:
            self.log.error(f"Invalid tool name format: {prefixed_name}")
            return {
                "content": [{"type": "text", "text": f"Invalid tool name: {prefixed_name}"}],
                "isError": True,
            }
        else:
            backend_name, tool_name = prefixed_name.split("::", 1)

        if backend_name not in self.backends:
            self.log.error(f"Unknown backend: {backend_name}")
            return {
                "content": [{"type": "text", "text": f"Unknown backend: {backend_name}"}],
                "isError": True,
            }

        backend = self.backends[backend_name]

        # Check backend state
        if backend.state == BackendState.STARTING:
            self.log.debug(f"[{backend_name}] Backend still initializing, waiting...")
            # Wait for init to complete (with timeout)
            if backend_name in self._backend_init_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.shield(self._backend_init_tasks[backend_name]),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    return {
                        "content": [{"type": "text", "text": f"Backend '{backend_name}' initialization timeout"}],
                        "isError": True,
                    }

        if backend.state == BackendState.FAILED:
            return {
                "content": [{"type": "text", "text": f"Backend '{backend_name}' failed to start: {backend.error}"}],
                "isError": True,
            }

        if backend.state != BackendState.READY:
            return {
                "content": [{"type": "text", "text": f"Backend '{backend_name}' not ready (state: {backend.state.value})"}],
                "isError": True,
            }

        self.log.verbose(f"[{backend_name}] Routing call to: {tool_name}")

        try:
            import time
            start = time.monotonic()
            response = await self._backend_request(
                backend, "tools/call", {"name": tool_name, "arguments": arguments}
            )
            elapsed = (time.monotonic() - start) * 1000
            self.log.debug(f"[{backend_name}] {tool_name} completed in {elapsed:.0f}ms")
            return response.get("result", {})
        except Exception as e:
            self.log.error(f"[{backend_name}] Tool call failed: {e}")
            return {
                "content": [{"type": "text", "text": f"Tool call failed: {e}"}],
                "isError": True,
            }

    async def _serve(self):
        """Handle incoming MCP requests from Claude Code.

        IMPORTANT: Uses synchronous stdin reading in a dedicated thread.
        The asyncio executor pattern (loop.run_in_executor + wait_for) causes
        Claude Code to hang after showing the tool permission prompt. The exact
        cause is unknown, but switching to sync reading with a queue fixes it.
        See ARCHITECTURE.md for details.
        """
        self.log.debug("Gateway ready, waiting for requests")

        import queue
        import threading

        # Queue for passing stdin lines from reader thread to async loop
        stdin_queue: queue.Queue[str | None] = queue.Queue()

        def stdin_reader():
            """Read stdin synchronously in a dedicated thread."""
            try:
                for line in sys.stdin:
                    if self._shutdown:
                        break
                    stdin_queue.put(line)
            except Exception:
                pass
            finally:
                stdin_queue.put(None)  # Signal EOF

        # Start stdin reader thread
        reader_thread = threading.Thread(target=stdin_reader, daemon=True)
        reader_thread.start()

        while not self._shutdown:
            try:
                # Non-blocking poll with async sleep to not block event loop
                try:
                    line = stdin_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)  # Yield to event loop
                    continue

                if line is None:  # EOF
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    self.log.debug(f"Invalid JSON from client: {e}")
                    continue

                response = await self._handle_request(request)

                if response:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

            except Exception as e:
                self.log.error(f"Error in serve loop: {e}")
                break

    async def _handle_request(self, request: dict) -> dict | None:
        """Handle a single MCP request from the client."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        self.log.debug(f"Request: {method}")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "mcpmon-gateway", "version": "1.0.0"},
                },
            }

        elif method == "notifications/initialized":
            self.initialized = True
            self.log.debug("Client initialized")
            # Send initial tools list changed to ensure client fetches tools
            if self.config.notify_on_change:
                self._send_tools_list_changed()
            return None

        elif method == "tools/list":
            tools = self._aggregate_tools()
            self.log.debug(f"Returning {len(tools)} tools")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools},
            }

        elif method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            self.log.debug(f"Tool call: {name}")
            result = await self._route_tool_call(name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}

        elif method == "gateway/status":
            # Return status of all backends
            status = {}
            for name, backend in self.backends.items():
                status[name] = {
                    "state": backend.state.value,
                    "pid": backend.process.pid if backend.process else None,
                    "tools": len(backend.tools),
                    "error": backend.error,
                }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"backends": status, "initialized": self.initialized},
            }

        else:
            self.log.debug(f"Unknown method: {method}")
            if request_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            return None

    def _send_tools_list_changed(self):
        """Send notification to Claude Code."""
        notification = json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}
        )
        sys.stdout.write(notification + "\n")
        sys.stdout.flush()
        self.log.info("Sent tools/list_changed notification")

    async def _watch_config(self):
        """Watch config file for changes."""
        if not self.config.config_path:
            return

        config_dir = self.config.config_path.parent
        config_name = self.config.config_path.name

        self.log.debug(f"Watching config: {self.config.config_path}")

        try:
            async for changes in awatch(config_dir):
                for change_type, path in changes:
                    # Handle both modified and added (atomic writes show as added)
                    if Path(path).name == config_name and change_type in (Change.modified, Change.added):
                        self.log.info("Config file changed, reloading...")
                        await self._reload_config()
        except Exception as e:
            self.log.error(f"Config watcher error: {e}")

    async def _reload_config(self):
        """Reload config and update backends."""
        try:
            new_config = load_config(self.config.config_path)
        except Exception as e:
            self.log.error(f"Failed to reload config: {e}")
            return

        current_names = set(self.backends.keys())
        new_names = set(new_config.servers.keys())

        # Start new backends
        for name in new_names - current_names:
            try:
                await self.start_backend(name, new_config.servers[name])
                self.log.info(f"[{name}] Added via config reload")
            except Exception as e:
                self.log.error(f"[{name}] Failed to add: {e}")

        # Stop removed backends
        for name in current_names - new_names:
            await self.stop_backend(name)
            self.log.info(f"[{name}] Removed via config reload")

        # Update config reference
        self.config = new_config

        # Notify client if anything changed
        if (new_names - current_names) or (current_names - new_names):
            if self.config.notify_on_change and self.initialized:
                self._send_tools_list_changed()

    async def _watch_backend_files(self, backend: Backend):
        """Watch a backend's files and restart on change."""
        if not backend.config.watch:
            return

        watch_path = Path(backend.config.watch).expanduser().resolve()
        extensions = {
            ext.strip().lstrip(".") for ext in backend.config.extensions.split(",")
        }

        self.log.debug(
            f"[{backend.name}] Watching {watch_path} for .{', .'.join(extensions)}"
        )

        try:
            async for changes in awatch(watch_path):
                # Check if any changes match our extensions
                should_restart = False
                for change_type, path in changes:
                    if change_type in (Change.added, Change.modified):
                        if Path(path).suffix.lstrip(".") in extensions:
                            rel_path = Path(path).relative_to(watch_path)
                            self.log.verbose(f"[{backend.name}] Changed: {rel_path}")
                            should_restart = True

                if should_restart:
                    await self.restart_backend(backend.name)
        except Exception as e:
            self.log.error(f"[{backend.name}] File watcher error: {e}")

    def shutdown(self):
        """Shutdown the gateway and all backends."""
        self._shutdown = True

        # Cancel any pending init tasks
        for name, task in self._backend_init_tasks.items():
            if not task.done():
                self.log.debug(f"[{name}] Cancelling init task...")
                task.cancel()

        # Stop all backends
        backend_count = len(self.backends)
        for name in list(self.backends.keys()):
            backend = self.backends[name]
            self.log.debug(f"[{name}] Terminating (pid:{backend.process.pid})...")
            self._terminate_process(backend.process)
            backend.state = BackendState.STOPPED

        self.backends.clear()
        self.log.info(f"Stopped {backend_count} backend(s)")


async def run_gateway_async(config: GatewayConfig, logger: Logger):
    """Run the gateway asynchronously."""
    gateway = Gateway(config, logger)

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler(sig_name: str):
        logger.info(f"Received {sig_name}, shutting down gateway...")
        gateway.shutdown()

    # Handle SIGINT (Ctrl+C), SIGTERM (kill), and SIGHUP (terminal disconnect)
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            loop.add_signal_handler(sig, lambda s=sig.name: signal_handler(s))
        except (ValueError, OSError):
            # Signal not supported on this platform
            pass

    try:
        await gateway.start()
    finally:
        gateway.shutdown()
        logger.info("Gateway shutdown complete")


def run_gateway(config_path: str | Path, logger: Logger):
    """Run the gateway (blocking)."""
    config = load_config(config_path)

    # Override log level from config
    level_map = {
        "quiet": LogLevel.QUIET,
        "info": LogLevel.NORMAL,
        "normal": LogLevel.NORMAL,
        "verbose": LogLevel.VERBOSE,
        "debug": LogLevel.DEBUG,
    }
    if config.log_level in level_map:
        logger.level = level_map[config.log_level]

    asyncio.run(run_gateway_async(config, logger))
