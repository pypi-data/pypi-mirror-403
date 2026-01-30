"""Multi-server gateway mode for mcpmon."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from watchfiles import awatch, Change

from .config import GatewayConfig, ServerConfig, load_config
from .log import Logger, LogLevel


@dataclass
class Backend:
    """A running backend MCP server."""

    name: str
    config: ServerConfig
    process: subprocess.Popen
    tools: list[dict] = field(default_factory=list)
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

    async def start(self):
        """Start all backends and begin serving."""
        self.log.info(f"Gateway starting with {len(self.config.servers)} backend(s)")
        for name in self.config.servers:
            self.log.debug(f"  - {name}")

        # Start all configured backends
        for name, server_config in self.config.servers.items():
            try:
                await self.start_backend(name, server_config)
            except Exception as e:
                self.log.error(f"Failed to start backend '{name}': {e}")

        # Start config file watcher
        if self.config.config_path:
            asyncio.create_task(self._watch_config())

        # Start backend file watchers
        for name, backend in self.backends.items():
            if backend.config.watch:
                asyncio.create_task(self._watch_backend_files(backend))

        # Start main request handler
        await self._serve()

    async def start_backend(self, name: str, config: ServerConfig):
        """Start a single backend server."""
        command = config.command
        if isinstance(command, str):
            command = [command]
        if config.args:
            command = list(command) + list(config.args)

        env = {**os.environ, **config.env}

        self.log.debug(f"[{name}] Starting: {' '.join(command)}")

        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            env=env,
        )

        backend = Backend(name=name, config=config, process=proc)
        self.backends[name] = backend

        # Initialize MCP connection
        try:
            await self._initialize_backend(backend)

            # Fetch tools
            response = await self._backend_request(backend, "tools/list", {})
            backend.tools = response.get("result", {}).get("tools", [])

            tool_names = [t.get("name", "?") for t in backend.tools]
            self.log.info(f"[{name}] Started (pid:{proc.pid})")
            self.log.verbose(f"[{name}] Tools ({len(backend.tools)}): {', '.join(tool_names)}")
        except Exception as e:
            self.log.error(f"[{name}] Initialization failed: {e}")
            proc.terminate()
            del self.backends[name]
            raise

    async def stop_backend(self, name: str):
        """Stop a backend server."""
        if name not in self.backends:
            return

        backend = self.backends[name]
        self.log.debug(f"[{name}] Stopping (pid:{backend.process.pid})")

        backend.process.terminate()
        try:
            backend.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            backend.process.kill()
            backend.process.wait()

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
        await self.start_backend(name, config)

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
                "clientInfo": {"name": "mcpmon-gateway", "version": "0.5.0"},
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
        """Aggregate tools from all backends with prefixed names."""
        all_tools = []

        for name, backend in self.backends.items():
            for tool in backend.tools:
                prefixed_tool = {
                    **tool,
                    "name": f"{name}__{tool['name']}",
                    "description": f"[{name}] {tool.get('description', '')}",
                }
                all_tools.append(prefixed_tool)

        return all_tools

    async def _route_tool_call(self, prefixed_name: str, arguments: dict) -> dict:
        """Route a tool call to the correct backend."""
        if "__" not in prefixed_name:
            self.log.error(f"Invalid tool name format: {prefixed_name}")
            return {
                "content": [{"type": "text", "text": f"Invalid tool name: {prefixed_name}"}],
                "isError": True,
            }

        backend_name, tool_name = prefixed_name.split("__", 1)

        if backend_name not in self.backends:
            self.log.error(f"Unknown backend: {backend_name}")
            return {
                "content": [{"type": "text", "text": f"Unknown backend: {backend_name}"}],
                "isError": True,
            }

        backend = self.backends[backend_name]
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
        """Handle incoming MCP requests from Claude Code."""
        self.log.debug("Gateway ready, waiting for requests")

        # Use a thread to read stdin to avoid blocking the event loop
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_event_loop()

        while not self._shutdown:
            try:
                # Read with timeout to allow checking shutdown flag
                line = await asyncio.wait_for(
                    loop.run_in_executor(executor, sys.stdin.readline),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

            if not line:
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

        executor.shutdown(wait=False)

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
                    "serverInfo": {"name": "mcpmon-gateway", "version": "0.5.0"},
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
                    if Path(path).name == config_name and change_type == Change.modified:
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
        """Shutdown the gateway."""
        self._shutdown = True
        backend_count = len(self.backends)
        for name in list(self.backends.keys()):
            backend = self.backends[name]
            self.log.debug(f"[{name}] Terminating...")
            backend.process.terminate()
            try:
                backend.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.log.debug(f"[{name}] Force killing...")
                backend.process.kill()
        self.log.info(f"Stopped {backend_count} backend(s)")


async def run_gateway_async(config: GatewayConfig, logger: Logger):
    """Run the gateway asynchronously."""
    gateway = Gateway(config, logger)

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Shutting down gateway...")
        gateway.shutdown()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

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
