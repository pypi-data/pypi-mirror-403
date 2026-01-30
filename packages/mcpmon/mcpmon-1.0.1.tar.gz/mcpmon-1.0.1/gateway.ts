#!/usr/bin/env bun
/**
 * mcpmon gateway mode: Aggregate multiple MCP servers behind one gateway.
 */

import { watch } from "fs";
import { spawn, type Subprocess } from "bun";
import { parse as parseYaml } from "yaml";

// =============================================================================
// Types
// =============================================================================

interface ServerConfig {
  command: string | string[];
  args?: string[];
  watch?: string;
  extensions?: string;
  env?: Record<string, string>;
}

interface GatewayConfig {
  servers: Record<string, ServerConfig>;
  settings?: {
    log_level?: string;
    notify_on_change?: boolean;
  };
}

interface Tool {
  name: string;
  description?: string;
  inputSchema?: unknown;
  [key: string]: unknown;
}

interface Backend {
  name: string;
  config: ServerConfig;
  process: Subprocess;
  tools: Tool[];
  pendingRequests: Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>;
  buffer: string;
}

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id?: number;
  method: string;
  params?: Record<string, unknown>;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id?: number;
  result?: unknown;
  error?: { code: number; message: string };
}

// =============================================================================
// Logging
// =============================================================================

type LogLevel = "quiet" | "normal" | "verbose" | "debug";

const LOG_LEVELS: Record<LogLevel, number> = {
  quiet: 0,
  normal: 1,
  verbose: 2,
  debug: 3,
};

let logLevel: LogLevel = "normal";

function log(level: LogLevel, msg: string, prefix?: string): void {
  if (LOG_LEVELS[logLevel] >= LOG_LEVELS[level]) {
    const tag = prefix ? `[mcpmon ${prefix}]` : "[mcpmon]";
    console.error(`${tag} ${msg}`);
  }
}

// =============================================================================
// Gateway
// =============================================================================

export class Gateway {
  private config: GatewayConfig;
  private configPath: string;
  private backends: Map<string, Backend> = new Map();
  private requestId = 0;
  private initialized = false;
  private shutdown = false;

  constructor(configPath: string) {
    this.configPath = configPath;
    this.config = this.loadConfig();

    // Set log level from config
    const level = this.config.settings?.log_level;
    if (level && level in LOG_LEVELS) {
      logLevel = level as LogLevel;
    }
  }

  private loadConfig(): GatewayConfig {
    const content = Bun.file(this.configPath).text();
    return parseYaml(content as unknown as string) as GatewayConfig;
  }

  async start(): Promise<void> {
    log("normal", `Gateway starting with ${Object.keys(this.config.servers).length} backend(s)`);

    // Start all backends
    for (const [name, serverConfig] of Object.entries(this.config.servers)) {
      try {
        await this.startBackend(name, serverConfig);
      } catch (e) {
        log("quiet", `Failed to start backend '${name}': ${e}`, name);
      }
    }

    // Start config watcher
    this.watchConfig();

    // Start serving
    await this.serve();
  }

  private async startBackend(name: string, config: ServerConfig): Promise<void> {
    let cmd: string[];
    if (typeof config.command === "string") {
      cmd = [config.command];
    } else {
      cmd = [...config.command];
    }
    if (config.args) {
      cmd = [...cmd, ...config.args];
    }

    const env = { ...process.env, ...(config.env || {}) };

    log("debug", `Starting: ${cmd.join(" ")}`, name);

    const proc = spawn({
      cmd,
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
      env,
    });

    const backend: Backend = {
      name,
      config,
      process: proc,
      tools: [],
      pendingRequests: new Map(),
      buffer: "",
    };

    this.backends.set(name, backend);

    // Start reading stdout
    this.readBackendOutput(backend);

    // Initialize MCP connection
    await this.initializeBackend(backend);

    // Fetch tools
    const response = await this.backendRequest(backend, "tools/list", {});
    backend.tools = (response as { tools?: Tool[] }).tools || [];

    const toolNames = backend.tools.map((t) => t.name).join(", ");
    log("normal", `Started (pid:${proc.pid})`, name);
    log("verbose", `Tools (${backend.tools.length}): ${toolNames}`, name);

    // Start file watcher if configured
    if (config.watch) {
      this.watchBackendFiles(backend);
    }
  }

  private async readBackendOutput(backend: Backend): Promise<void> {
    if (!backend.process.stdout) return;

    const reader = backend.process.stdout.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        backend.buffer += decoder.decode(value, { stream: true });

        // Process complete lines
        let newlineIndex;
        while ((newlineIndex = backend.buffer.indexOf("\n")) !== -1) {
          const line = backend.buffer.slice(0, newlineIndex);
          backend.buffer = backend.buffer.slice(newlineIndex + 1);

          if (line.trim()) {
            this.handleBackendMessage(backend, line);
          }
        }
      }
    } catch {
      // Process terminated
    }
  }

  private handleBackendMessage(backend: Backend, line: string): void {
    try {
      const msg = JSON.parse(line) as JsonRpcResponse;

      // Check if it's a response to a pending request
      if (msg.id !== undefined) {
        const pending = backend.pendingRequests.get(msg.id);
        if (pending) {
          backend.pendingRequests.delete(msg.id);
          if (msg.error) {
            pending.reject(new Error(msg.error.message));
          } else {
            pending.resolve(msg.result);
          }
        }
      } else if ("method" in msg) {
        // It's a notification from the backend
        log("debug", `Notification: ${(msg as unknown as JsonRpcRequest).method}`, backend.name);
      }
    } catch {
      log("debug", `Invalid JSON from backend: ${line.slice(0, 100)}`, backend.name);
    }
  }

  private async initializeBackend(backend: Backend): Promise<void> {
    await this.backendRequest(backend, "initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "mcpmon-gateway", version: "1.0.0" },
    });

    this.backendNotify(backend, "notifications/initialized", {});
  }

  private backendRequest(backend: Backend, method: string, params: Record<string, unknown>): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const id = ++this.requestId;
      backend.pendingRequests.set(id, { resolve, reject });

      const request = JSON.stringify({ jsonrpc: "2.0", id, method, params });
      backend.process.stdin!.write(request + "\n");

      // Timeout after 30 seconds
      setTimeout(() => {
        if (backend.pendingRequests.has(id)) {
          backend.pendingRequests.delete(id);
          reject(new Error(`Request timeout: ${method}`));
        }
      }, 30000);
    });
  }

  private backendNotify(backend: Backend, method: string, params: Record<string, unknown>): void {
    const notification = JSON.stringify({ jsonrpc: "2.0", method, params });
    backend.process.stdin!.write(notification + "\n");
  }

  private aggregateTools(): Tool[] {
    const allTools: Tool[] = [];
    const singleBackend = this.backends.size === 1;

    for (const [name, backend] of this.backends) {
      for (const tool of backend.tools) {
        if (singleBackend) {
          // Pass through unmodified for single backend
          allTools.push(tool);
        } else {
          allTools.push({
            ...tool,
            name: `${name}::${tool.name}`,
            description: `[${name}] ${tool.description || ""}`,
          });
        }
      }
    }

    return allTools;
  }

  private async routeToolCall(prefixedName: string, args: Record<string, unknown>): Promise<unknown> {
    let backendName: string;
    let toolName: string;

    // Single backend mode: tool name not prefixed
    if (this.backends.size === 1) {
      backendName = this.backends.keys().next().value!;
      toolName = prefixedName;
    } else if (!prefixedName.includes("::")) {
      log("quiet", `Invalid tool name format: ${prefixedName}`);
      return {
        content: [{ type: "text", text: `Invalid tool name: ${prefixedName}` }],
        isError: true,
      };
    } else {
      const separatorIndex = prefixedName.indexOf("::");
      backendName = prefixedName.slice(0, separatorIndex);
      toolName = prefixedName.slice(separatorIndex + 2);
    }

    const backend = this.backends.get(backendName);
    if (!backend) {
      log("quiet", `Unknown backend: ${backendName}`);
      return {
        content: [{ type: "text", text: `Unknown backend: ${backendName}` }],
        isError: true,
      };
    }

    log("verbose", `Routing call to: ${toolName}`, backendName);

    try {
      const start = performance.now();
      const result = await this.backendRequest(backend, "tools/call", {
        name: toolName,
        arguments: args,
      });
      const elapsed = performance.now() - start;
      log("debug", `${toolName} completed in ${elapsed.toFixed(0)}ms`, backendName);
      return result;
    } catch (e) {
      log("quiet", `Tool call failed: ${e}`, backendName);
      return {
        content: [{ type: "text", text: `Tool call failed: ${e}` }],
        isError: true,
      };
    }
  }

  private async serve(): Promise<void> {
    log("debug", "Gateway ready, waiting for requests");

    const decoder = new TextDecoder();
    const reader = Bun.stdin.stream().getReader();
    let buffer = "";

    while (!this.shutdown) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      let newlineIndex;
      while ((newlineIndex = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 1);

        if (line.trim()) {
          const response = await this.handleRequest(line);
          if (response) {
            process.stdout.write(JSON.stringify(response) + "\n");
          }
        }
      }
    }
  }

  private async handleRequest(line: string): Promise<JsonRpcResponse | null> {
    let request: JsonRpcRequest;
    try {
      request = JSON.parse(line);
    } catch {
      log("debug", `Invalid JSON from client: ${line.slice(0, 100)}`);
      return null;
    }

    const { method, params, id } = request;
    log("debug", `Request: ${method}`);

    if (method === "initialize") {
      return {
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: { listChanged: true } },
          serverInfo: { name: "mcpmon-gateway", version: "1.0.0" },
        },
      };
    }

    if (method === "notifications/initialized") {
      this.initialized = true;
      log("debug", "Client initialized");
      if (this.config.settings?.notify_on_change !== false) {
        this.sendToolsListChanged();
      }
      return null;
    }

    if (method === "tools/list") {
      const tools = this.aggregateTools();
      log("debug", `Returning ${tools.length} tools`);
      return {
        jsonrpc: "2.0",
        id,
        result: { tools },
      };
    }

    if (method === "tools/call") {
      const name = (params as { name: string }).name;
      const args = (params as { arguments?: Record<string, unknown> }).arguments || {};
      log("debug", `Tool call: ${name}`);
      const result = await this.routeToolCall(name, args);
      return {
        jsonrpc: "2.0",
        id,
        result,
      };
    }

    if (method === "ping") {
      return { jsonrpc: "2.0", id, result: {} };
    }

    log("debug", `Unknown method: ${method}`);
    if (id !== undefined) {
      return {
        jsonrpc: "2.0",
        id,
        error: { code: -32601, message: `Method not found: ${method}` },
      };
    }

    return null;
  }

  private sendToolsListChanged(): void {
    const notification = JSON.stringify({
      jsonrpc: "2.0",
      method: "notifications/tools/list_changed",
    });
    process.stdout.write(notification + "\n");
    log("normal", "Sent tools/list_changed notification");
  }

  private watchConfig(): void {
    const watcher = watch(this.configPath, async (event) => {
      // Handle both 'change' and 'rename' (atomic writes may trigger rename)
      if (event === "change" || event === "rename") {
        log("normal", "Config file changed, reloading...");
        await this.reloadConfig();
      }
    });

    process.on("exit", () => watcher.close());
  }

  private async reloadConfig(): Promise<void> {
    try {
      const newConfig = parseYaml(await Bun.file(this.configPath).text()) as GatewayConfig;

      const currentNames = new Set(this.backends.keys());
      const newNames = new Set(Object.keys(newConfig.servers));

      // Start new backends
      for (const name of newNames) {
        if (!currentNames.has(name)) {
          try {
            await this.startBackend(name, newConfig.servers[name]);
            log("normal", `Added via config reload`, name);
          } catch (e) {
            log("quiet", `Failed to add: ${e}`, name);
          }
        }
      }

      // Stop removed backends
      for (const name of currentNames) {
        if (!newNames.has(name)) {
          await this.stopBackend(name);
          log("normal", `Removed via config reload`, name);
        }
      }

      this.config = newConfig;

      // Notify client
      if (this.initialized && this.config.settings?.notify_on_change !== false) {
        this.sendToolsListChanged();
      }
    } catch (e) {
      log("quiet", `Failed to reload config: ${e}`);
    }
  }

  private async stopBackend(name: string): Promise<void> {
    const backend = this.backends.get(name);
    if (!backend) return;

    log("debug", `Terminating...`, name);
    backend.process.kill("SIGTERM");

    // Wait up to 2 seconds
    const timeout = setTimeout(() => {
      if (backend.process.exitCode === null) {
        log("debug", `Force killing...`, name);
        backend.process.kill("SIGKILL");
      }
    }, 2000);

    await backend.process.exited;
    clearTimeout(timeout);

    this.backends.delete(name);
    log("normal", `Stopped`, name);
  }

  private watchBackendFiles(backend: Backend): void {
    if (!backend.config.watch) return;

    const extensions = new Set(
      (backend.config.extensions || "py").split(",").map((e) => e.trim().replace(/^\./, ""))
    );

    log("debug", `Watching ${backend.config.watch} for .${[...extensions].join(", .")}`, backend.name);

    const watcher = watch(backend.config.watch, { recursive: true }, async (event, filename) => {
      if (!filename) return;
      const ext = filename.split(".").pop() || "";
      if (extensions.has(ext)) {
        log("verbose", `File changed: ${filename}`, backend.name);
        await this.restartBackend(backend.name);
      }
    });

    backend.process.exited.then(() => watcher.close());
  }

  private async restartBackend(name: string): Promise<void> {
    const backend = this.backends.get(name);
    if (!backend) return;

    log("normal", `Restarting...`, name);

    const config = backend.config;
    await this.stopBackend(name);
    await Bun.sleep(100);
    await this.startBackend(name, config);

    if (this.initialized && this.config.settings?.notify_on_change !== false) {
      this.sendToolsListChanged();
    }
  }

  stop(): void {
    this.shutdown = true;
    const count = this.backends.size;
    for (const [name, backend] of this.backends) {
      log("debug", `Terminating...`, name);
      backend.process.kill("SIGTERM");
    }
    log("normal", `Stopped ${count} backend(s)`);
  }
}

// =============================================================================
// Main (when run directly)
// =============================================================================

if (import.meta.main) {
  const configPath = process.argv[2];
  if (!configPath) {
    console.error("Usage: bun gateway.ts <config.yaml>");
    process.exit(1);
  }

  const gateway = new Gateway(configPath);

  process.on("SIGINT", () => {
    log("normal", "Shutting down gateway...");
    gateway.stop();
    process.exit(0);
  });

  process.on("SIGTERM", () => {
    log("normal", "Shutting down gateway...");
    gateway.stop();
    process.exit(0);
  });

  await gateway.start();
}
