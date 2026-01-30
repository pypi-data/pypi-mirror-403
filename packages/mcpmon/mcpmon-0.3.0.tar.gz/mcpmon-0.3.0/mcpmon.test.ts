/**
 * Unit and integration tests for mcpmon (Bun/TypeScript version).
 *
 * Run with: bun test
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { spawn, type Subprocess } from "bun";
import { mkdtempSync, writeFileSync, rmSync, mkdirSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

// =============================================================================
// Test Utilities
// =============================================================================

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createTempDir(): string {
  return mkdtempSync(join(tmpdir(), "mcpmon-test-"));
}

function createDummyServer(dir: string): string {
  const serverPath = join(dir, "server.py");
  writeFileSync(
    serverPath,
    `
import sys
import time
import signal

print(f"[test-server] Started (pid={__import__('os').getpid()})", file=sys.stderr)
sys.stderr.flush()

def handle_term(sig, frame):
    print("[test-server] Received SIGTERM", file=sys.stderr)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_term)

while True:
    time.sleep(0.1)
`
  );
  return serverPath;
}

// =============================================================================
// Unit Tests - Logging
// =============================================================================

describe("Logging", () => {
  test("help shows all options", async () => {
    const proc = spawn({
      cmd: ["bun", "mcpmon.ts", "--help"],
      stdout: "pipe",
      stderr: "pipe",
    });

    const output = await new Response(proc.stdout).text();
    await proc.exited;

    expect(output).toContain("--watch");
    expect(output).toContain("--ext");
    expect(output).toContain("--quiet");
    expect(output).toContain("--verbose");
    expect(output).toContain("--debug");
    expect(output).toContain("--timestamps");
    expect(output).toContain("--log-file");
  });

  test("help shows logging levels", async () => {
    const proc = spawn({
      cmd: ["bun", "mcpmon.ts", "--help"],
      stdout: "pipe",
      stderr: "pipe",
    });

    const output = await new Response(proc.stdout).text();
    await proc.exited;

    expect(output).toContain("Logging levels:");
    expect(output).toContain("--quiet");
    expect(output).toContain("--verbose");
    expect(output).toContain("--debug");
  });

  test("help shows examples", async () => {
    const proc = spawn({
      cmd: ["bun", "mcpmon.ts", "--help"],
      stdout: "pipe",
      stderr: "pipe",
    });

    const output = await new Response(proc.stdout).text();
    await proc.exited;

    expect(output).toContain("Examples:");
  });
});

// =============================================================================
// Unit Tests - CLI Arguments
// =============================================================================

describe("CLI Arguments", () => {
  test("errors without command", async () => {
    const proc = spawn({
      cmd: ["bun", "mcpmon.ts", "--watch", ".", "--"],
      stdout: "pipe",
      stderr: "pipe",
    });

    const stderr = await new Response(proc.stderr).text();
    const code = await proc.exited;

    // Should exit with error when no command after --
    expect(code).not.toBe(0);
    expect(stderr.toLowerCase()).toContain("error");
  });

  test("accepts -- separator", async () => {
    const proc = spawn({
      cmd: ["bun", "mcpmon.ts", "--help", "--"],
      stdout: "pipe",
      stderr: "pipe",
    });

    const output = await new Response(proc.stdout).text();
    const code = await proc.exited;

    expect(code).toBe(0);
    expect(output).toContain("Usage:");
  });
});

// =============================================================================
// Integration Tests
// =============================================================================

describe("Integration", () => {
  let tempDir: string;
  let proc: Subprocess | null = null;

  beforeEach(() => {
    tempDir = createTempDir();
  });

  afterEach(async () => {
    if (proc && proc.exitCode === null) {
      proc.kill("SIGTERM");
      await proc.exited;
    }
    try {
      rmSync(tempDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  test("starts server and shows startup message", async () => {
    const serverPath = createDummyServer(tempDir);
    const logFile = join(tempDir, "mcpmon.log");

    proc = spawn({
      cmd: [
        "bun",
        "mcpmon.ts",
        "--watch",
        tempDir,
        "--log-file",
        logFile,
        "--",
        "python",
        serverPath,
      ],
      stdout: "pipe",
      stderr: "pipe",
    });

    // Wait for startup
    await sleep(2000);

    // Should still be running
    expect(proc.exitCode).toBeNull();

    // Check log file
    const logContent = await Bun.file(logFile).text();
    expect(logContent).toContain("Watching");
    expect(logContent).toContain("Started:");
  });

  test("restarts on file change", async () => {
    const serverPath = createDummyServer(tempDir);
    const watchedFile = join(tempDir, "watched.py");
    writeFileSync(watchedFile, "# initial");

    const logFile = join(tempDir, "mcpmon.log");

    proc = spawn({
      cmd: [
        "bun",
        "mcpmon.ts",
        "--watch",
        tempDir,
        "--ext",
        "py",
        "--log-file",
        logFile,
        "--",
        "python",
        serverPath,
      ],
      stdout: "pipe",
      stderr: "pipe",
    });

    // Wait for startup
    await sleep(2000);

    // Trigger reload
    writeFileSync(watchedFile, "# modified");

    // Wait for restart
    await sleep(2000);

    const logContent = await Bun.file(logFile).text();
    expect(logContent).toContain("Restart #1");
  });

  test("ignores non-matching extensions", async () => {
    const serverPath = createDummyServer(tempDir);
    const otherFile = join(tempDir, "readme.txt");
    writeFileSync(otherFile, "initial");

    const logFile = join(tempDir, "mcpmon.log");

    proc = spawn({
      cmd: [
        "bun",
        "mcpmon.ts",
        "--watch",
        tempDir,
        "--ext",
        "py",
        "--debug",
        "--log-file",
        logFile,
        "--",
        "python",
        serverPath,
      ],
      stdout: "pipe",
      stderr: "pipe",
    });

    // Wait for startup
    await sleep(2000);

    // Modify non-matching file
    writeFileSync(otherFile, "modified");

    // Wait
    await sleep(2000);

    const logContent = await Bun.file(logFile).text();
    expect(logContent).not.toContain("Restart #1");
  });

  test("handles graceful shutdown", async () => {
    const serverPath = createDummyServer(tempDir);
    const logFile = join(tempDir, "mcpmon.log");

    proc = spawn({
      cmd: [
        "bun",
        "mcpmon.ts",
        "--watch",
        tempDir,
        "--log-file",
        logFile,
        "--",
        "python",
        serverPath,
      ],
      stdout: "pipe",
      stderr: "pipe",
    });

    // Wait for startup
    await sleep(2000);

    // Send SIGTERM
    proc.kill("SIGTERM");

    // Wait for shutdown
    const code = await proc.exited;

    const logContent = await Bun.file(logFile).text();
    expect(logContent).toContain("Shutdown complete");
  });

  test("tracks restart count", async () => {
    const serverPath = createDummyServer(tempDir);
    const watchedFile = join(tempDir, "watched.py");
    writeFileSync(watchedFile, "# v1");

    const logFile = join(tempDir, "mcpmon.log");

    proc = spawn({
      cmd: [
        "bun",
        "mcpmon.ts",
        "--watch",
        tempDir,
        "--ext",
        "py",
        "--log-file",
        logFile,
        "--",
        "python",
        serverPath,
      ],
      stdout: "pipe",
      stderr: "pipe",
    });

    // Wait for startup
    await sleep(2500);

    // Trigger first restart
    writeFileSync(watchedFile, "# v2");
    await sleep(2500);

    // Verify first restart happened before triggering second
    let logContent = await Bun.file(logFile).text();
    expect(logContent).toContain("Restart #1");

    // Trigger second restart
    writeFileSync(watchedFile, "# v3");
    await sleep(2500);

    logContent = await Bun.file(logFile).text();
    expect(logContent).toContain("Restart #2");
  }, 15000); // Increase timeout to 15s

  test("verbose mode shows file details", async () => {
    const serverPath = createDummyServer(tempDir);
    const watchedFile = join(tempDir, "mymodule.py");
    writeFileSync(watchedFile, "# initial");

    const logFile = join(tempDir, "mcpmon.log");

    proc = spawn({
      cmd: [
        "bun",
        "mcpmon.ts",
        "--watch",
        tempDir,
        "--ext",
        "py",
        "--verbose",
        "--log-file",
        logFile,
        "--",
        "python",
        serverPath,
      ],
      stdout: "pipe",
      stderr: "pipe",
    });

    // Wait for startup
    await sleep(2000);

    // Trigger reload
    writeFileSync(watchedFile, "# modified");
    await sleep(2000);

    const logContent = await Bun.file(logFile).text();
    expect(logContent).toContain("File");
    expect(logContent).toContain("mymodule.py");
  });
});

// =============================================================================
// Timestamp Tests
// =============================================================================

describe("Timestamps", () => {
  let tempDir: string;
  let proc: Subprocess | null = null;

  beforeEach(() => {
    tempDir = createTempDir();
  });

  afterEach(async () => {
    if (proc && proc.exitCode === null) {
      proc.kill("SIGTERM");
      await proc.exited;
    }
    try {
      rmSync(tempDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  test("log file always has full timestamps", async () => {
    const serverPath = createDummyServer(tempDir);
    const logFile = join(tempDir, "mcpmon.log");

    proc = spawn({
      cmd: [
        "bun",
        "mcpmon.ts",
        "--watch",
        tempDir,
        "--log-file",
        logFile,
        "--",
        "python",
        serverPath,
      ],
      stdout: "pipe",
      stderr: "pipe",
    });

    await sleep(2000);

    proc.kill("SIGTERM");
    await proc.exited;

    const logContent = await Bun.file(logFile).text();
    // Full timestamp format: YYYY-MM-DD HH:MM:SS
    expect(logContent).toMatch(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/);
  });
});
