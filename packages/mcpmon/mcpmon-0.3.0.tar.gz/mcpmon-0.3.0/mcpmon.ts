#!/usr/bin/env bun
/**
 * mcpmon: Hot reload for MCP servers. Like nodemon, but for MCP.
 */

import { watch, appendFileSync, type WatchListener } from "fs";
import { spawn, type Subprocess } from "bun";
import { parseArgs } from "util";

// =============================================================================
// Types
// =============================================================================

type LogLevel = "quiet" | "normal" | "verbose" | "debug";

interface Logger {
  level: LogLevel;
  showTimestamps: boolean;
  logFile: string | null;
  fileHandle: number | null;
}

// =============================================================================
// Logging
// =============================================================================

const LOG_LEVELS: Record<LogLevel, number> = {
  quiet: 0,
  normal: 1,
  verbose: 2,
  debug: 3,
};

const logger: Logger = {
  level: "normal",
  showTimestamps: false,
  logFile: null,
  fileHandle: null,
};

function getTimestamp(): string {
  const now = new Date();
  return now.toTimeString().slice(0, 8); // HH:MM:SS
}

function getFullTimestamp(): string {
  return new Date().toISOString().replace("T", " ").slice(0, 19);
}

function formatMessage(msg: string, pid?: number): string {
  const parts = ["[mcpmon"];

  if (logger.showTimestamps) {
    parts.push(getTimestamp());
  }

  if (pid !== undefined) {
    parts.push(`pid:${pid}`);
  }

  return `${parts.join(" ")}] ${msg}`;
}

function writeLog(msg: string): void {
  console.error(msg);

  if (logger.logFile) {
    const fileMsg = `[${getFullTimestamp()}] ${msg}\n`;
    try {
      appendFileSync(logger.logFile, fileMsg);
    } catch {
      // Ignore file write errors
    }
  }
}

const log = {
  error(msg: string, pid?: number): void {
    writeLog(formatMessage(`ERROR: ${msg}`, pid));
  },

  info(msg: string, pid?: number): void {
    if (LOG_LEVELS[logger.level] >= LOG_LEVELS.normal) {
      writeLog(formatMessage(msg, pid));
    }
  },

  verbose(msg: string, pid?: number): void {
    if (LOG_LEVELS[logger.level] >= LOG_LEVELS.verbose) {
      writeLog(formatMessage(msg, pid));
    }
  },

  debug(msg: string, pid?: number): void {
    if (LOG_LEVELS[logger.level] >= LOG_LEVELS.debug) {
      writeLog(formatMessage(`DEBUG: ${msg}`, pid));
    }
  },
};

// =============================================================================
// CLI
// =============================================================================

const HELP = `mcpmon - Hot reload for MCP servers

Usage: mcpmon [options] -- <command>

Options:
  -w, --watch <dir>     Directory to watch (default: .)
  -e, --ext <exts>      Extensions to watch, comma-separated (default: py)
  -q, --quiet           Only show errors
  -v, --verbose         Show file change details
  --debug               Show all debug output
  -t, --timestamps      Include timestamps in output
  -l, --log-file <file> Also write logs to file (always includes timestamps)
  -h, --help            Show this help

Logging levels:
  --quiet       Only errors
  (default)     Start, stop, restart events
  --verbose     + file change details
  --debug       + everything

Examples:
  mcpmon -- python server.py
  mcpmon --watch src/ --ext py,json -- python -m myserver
  mcpmon --timestamps --log-file mcpmon.log -- python server.py
`;

const { values, positionals } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    watch: { type: "string", short: "w", default: "." },
    ext: { type: "string", short: "e", default: "py" },
    quiet: { type: "boolean", short: "q", default: false },
    verbose: { type: "boolean", short: "v", default: false },
    debug: { type: "boolean", default: false },
    timestamps: { type: "boolean", short: "t", default: false },
    "log-file": { type: "string", short: "l" },
    help: { type: "boolean", short: "h", default: false },
  },
  allowPositionals: true,
  strict: false,
});

if (values.help) {
  console.log(HELP);
  process.exit(0);
}

// Configure logger
if (values.quiet) {
  logger.level = "quiet";
} else if (values.debug) {
  logger.level = "debug";
} else if (values.verbose) {
  logger.level = "verbose";
}

logger.showTimestamps = values.timestamps as boolean;
logger.logFile = values["log-file"] as string | null;

// Remove leading "--" if present
const command = positionals[0] === "--" ? positionals.slice(1) : positionals;

if (command.length === 0) {
  log.error("No command specified. Use: mcpmon --watch src/ -- <command>");
  process.exit(1);
}

const watchDir = values.watch as string;
const extensions = new Set(
  (values.ext as string).split(",").map((e) => e.trim().replace(/^\./, ""))
);

// =============================================================================
// Process Management
// =============================================================================

let proc: Subprocess | null = null;
let restartCount = 0;

function startServer(): void {
  log.debug(`Spawning: ${command.join(" ")}`);
  proc = spawn({
    cmd: command,
    stdout: "inherit",
    stderr: "inherit",
    stdin: "inherit",
  });
  log.info(`Started: ${command.join(" ")}`, proc.pid);
}

async function stopServer(): Promise<void> {
  if (!proc) return;

  const pid = proc.pid;

  if (proc.exitCode !== null) {
    log.debug(`Process already exited with code ${proc.exitCode}`, pid);
    return;
  }

  log.debug("Sending SIGTERM", pid);
  proc.kill("SIGTERM");

  // Wait up to 2 seconds for graceful shutdown
  const timeout = setTimeout(() => {
    if (proc && proc.exitCode === null) {
      log.debug("SIGTERM timeout, sending SIGKILL", pid);
      proc.kill("SIGKILL");
    }
  }, 2000);

  await proc.exited;
  clearTimeout(timeout);
  log.debug(`Process exited with code ${proc.exitCode}`, pid);
}

async function restartServer(): Promise<void> {
  const oldPid = proc?.pid;
  log.info("Restarting...", oldPid);
  await stopServer();
  startServer();
  restartCount++;
  log.info(`Restart #${restartCount} complete`, proc?.pid);
}

// =============================================================================
// File Watching
// =============================================================================

function shouldReload(filename: string | null): boolean {
  if (!filename) return false;
  const ext = filename.split(".").pop() || "";
  return extensions.has(ext);
}

function getChangeType(event: string): string {
  return event === "rename" ? "added/deleted" : "modified";
}

// =============================================================================
// Main
// =============================================================================

log.info(`Watching ${watchDir} for .${[...extensions].sort().join(", .")} changes`);
log.debug(`Log level: ${logger.level}`);
if (logger.logFile) {
  log.debug(`Log file: ${logger.logFile}`);
}

startServer();

// Watch for changes
const watcher = watch(
  watchDir,
  { recursive: true },
  async (event, filename) => {
    if (shouldReload(filename)) {
      log.verbose(`File ${getChangeType(event)}: ${filename}`);
      await restartServer();
    } else if (filename) {
      log.debug(`Ignored ${getChangeType(event)}: ${filename}`);
    }
  }
);

// Handle shutdown
async function shutdown(signal: string): Promise<void> {
  log.info(`Received ${signal}, shutting down...`);
  watcher.close();
  await stopServer();
  log.info(`Shutdown complete (restarts: ${restartCount})`);
  process.exit(0);
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
