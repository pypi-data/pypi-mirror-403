#!/usr/bin/env bun
/**
 * mcpmon: Hot reload for MCP servers. Like nodemon, but for MCP.
 */

import { watch } from "fs";
import { spawn, type Subprocess } from "bun";
import { parseArgs } from "util";

const { values, positionals } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    watch: { type: "string", short: "w", default: "." },
    ext: { type: "string", short: "e", default: "py" },
    help: { type: "boolean", short: "h", default: false },
  },
  allowPositionals: true,
  strict: false,
});

if (values.help || positionals.length === 0) {
  console.log(`mcpmon - Hot reload for MCP servers

Usage: mcpmon [options] -- <command>

Options:
  -w, --watch <dir>   Directory to watch (default: .)
  -e, --ext <exts>    Extensions to watch, comma-separated (default: py)
  -h, --help          Show this help

Examples:
  mcpmon -- python server.py
  mcpmon --watch src/ --ext py,json -- python -m myserver
  mcpmon --watch src/crucible/ -- crucible-mcp
`);
  process.exit(0);
}

// Remove leading "--" if present
const command = positionals[0] === "--" ? positionals.slice(1) : positionals;

if (command.length === 0) {
  console.error("[mcpmon] Error: No command specified");
  process.exit(1);
}

const watchDir = values.watch as string;
const extensions = new Set((values.ext as string).split(",").map(e => e.trim().replace(/^\./, "")));

let proc: Subprocess | null = null;

function startServer(): void {
  console.log(`[mcpmon] Starting: ${command.join(" ")}`);
  proc = spawn({
    cmd: command,
    stdout: "inherit",
    stderr: "inherit",
    stdin: "inherit",
  });
}

async function stopServer(): Promise<void> {
  if (!proc || proc.exitCode !== null) return;

  proc.kill("SIGTERM");

  // Wait up to 2 seconds for graceful shutdown
  const timeout = setTimeout(() => {
    if (proc && proc.exitCode === null) {
      proc.kill("SIGKILL");
    }
  }, 2000);

  await proc.exited;
  clearTimeout(timeout);
}

async function restartServer(): Promise<void> {
  await stopServer();
  startServer();
}

function shouldReload(filename: string | null): boolean {
  if (!filename) return false;
  const ext = filename.split(".").pop() || "";
  return extensions.has(ext);
}

// Start server
console.log(`[mcpmon] Watching ${watchDir} for .${[...extensions].join(", .")} changes`);
startServer();

// Watch for changes
const watcher = watch(watchDir, { recursive: true }, async (event, filename) => {
  if (event === "change" && shouldReload(filename)) {
    console.log(`[mcpmon] ${filename} changed, restarting...`);
    await restartServer();
  }
});

// Handle shutdown
process.on("SIGINT", async () => {
  console.log("\n[mcpmon] Shutting down...");
  watcher.close();
  await stopServer();
  process.exit(0);
});

process.on("SIGTERM", async () => {
  watcher.close();
  await stopServer();
  process.exit(0);
});
