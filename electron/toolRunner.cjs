// Native ToolRunner backend (Aşama 6.0c): runs installed EDA programs for the page.
//
// Security boundary. The page sends only a tool id, arguments and input files. This module alone decides
// which executable an id means (TOOLS below, mirrored from src/tools/registry.ts), starts it without a
// shell, inside a fresh temporary directory, and returns only the output files the page named.
// Every value from the page is checked again here; nothing the page sends is trusted. The arguments and input
// files also pass the per-tool policy in toolPolicy.cjs.
//
// Executable lookup order for a tool:
//   1. settings.toolPaths[<id>]   absolute path to the executable (set by the app, not by the page)
//   2. settings.toolSearchDirs[]  directories searched in order (e.g. an OSS CAD Suite "bin" folder)
//   3. PATH
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { isSafeRelativePath } = require('./pathRules.cjs');
const { checkToolRequest, confirmationFor } = require('./toolPolicy.cjs');

const IS_WIN = process.platform === 'win32';

/** Allowlist: tool id -> executable base name and probe arguments */
const TOOLS = {
  ghdl: { executable: 'ghdl', versionArgs: ['--version'] },
  yosys: { executable: 'yosys', versionArgs: ['-V'] },
  'nextpnr-ecp5': { executable: 'nextpnr-ecp5', versionArgs: ['--version'] },
  ecppack: { executable: 'ecppack', versionArgs: ['--version'] },
  // Talks to a board over USB: one run at a time, since two programmers on the same cable would collide.
  openfpgaloader: { executable: 'openFPGALoader', versionArgs: ['--version'], exclusive: true },
};

const LIMITS = {
  args: 512,
  argLength: 64 * 1024,
  files: 512,
  inputBytes: 64 * 1024 * 1024,
  outputBytes: 128 * 1024 * 1024,
  streamBytes: 16 * 1024 * 1024, // per stream (stdout, stderr)
  timeoutMs: 30 * 60 * 1000, // ceiling for a requested timeout
  defaultTimeoutMs: 60 * 1000,
  probeTimeoutMs: 15 * 1000,
};

const toolError = (kind, message) => ({ error: { kind, message } });

/** Resolves a relative path inside dir and makes sure it stays inside */
function inside(dir, rel) {
  const full = path.resolve(dir, rel);
  const root = path.resolve(dir) + path.sep;
  return full.startsWith(root) ? full : null;
}

function isFile(p) {
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

/** Kills a process and its children (yosys starts yosys-abc, for example) */
function killTree(child) {
  if (!child || child.exitCode !== null || child.killed) return;
  if (IS_WIN && child.pid) {
    try {
      spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { windowsHide: true, shell: false, stdio: 'ignore' });
      return;
    } catch {
      /* fall through */
    }
  }
  try {
    child.kill('SIGKILL');
  } catch {
    /* already gone */
  }
}

/**
 * confirmRun(request): asked before a run that changes something outside the computer for good (a flash write,
 * see confirmationFor in toolPolicy.cjs). It must ask the user in the main process (a native dialog the page cannot
 * draw or click) and resolve to true only on an explicit yes. Without it such runs are refused.
 */
function createToolRunner({ readSettings, onProgress, confirmRun }) {
  const probeCache = new Map(); // tool id -> { available, version?, exe? }
  const running = new Map(); // run id -> { child, cancelled }
  const busyTools = new Set(); // exclusive tools with a run in progress (including its confirmation)
  const confirming = new Map(); // run id -> { cancelled } while the user is asked

  function candidates(id) {
    const def = TOOLS[id];
    const settings = readSettings() || {};
    const names = IS_WIN ? [`${def.executable}.exe`] : [def.executable];
    const list = [];
    const fixed = settings.toolPaths && settings.toolPaths[id];
    if (typeof fixed === 'string' && path.isAbsolute(fixed)) list.push(fixed);
    const dirs = [
      ...(Array.isArray(settings.toolSearchDirs) ? settings.toolSearchDirs : []),
      ...String(process.env.PATH || '').split(path.delimiter),
    ].filter((d) => typeof d === 'string' && d.trim() !== '' && path.isAbsolute(d.trim()));
    for (const d of dirs) for (const n of names) list.push(path.join(d.trim(), n));
    return list;
  }

  function resolveExecutable(id) {
    for (const c of candidates(id)) {
      // Only real executables: on Windows a .bat/.cmd would need a shell, which is never used here.
      if (IS_WIN && path.extname(c).toLowerCase() !== '.exe') continue;
      if (isFile(c)) return c;
    }
    return null;
  }

  /**
   * Environment for a tool: its own folder first on PATH so sibling programs (yosys-abc) and DLLs are found.
   * Distributions laid out as <root>/bin + <root>/lib (OSS CAD Suite) keep their DLLs in lib, so a sibling
   * lib folder goes on PATH too, as the suite's own environment.bat does.
   */
  function toolEnv(exe) {
    const env = { ...process.env };
    const key = Object.keys(env).find((k) => k.toUpperCase() === 'PATH') || 'PATH';
    const binDir = path.dirname(exe);
    const libDir = path.join(binDir, '..', 'lib');
    const extra = [binDir];
    try {
      if (fs.statSync(libDir).isDirectory()) extra.push(path.resolve(libDir));
    } catch {
      /* no lib folder */
    }
    env[key] = [...extra, env[key] || ''].join(path.delimiter);
    return env;
  }

  /** Runs exe with args in cwd; resolves when it exits (never rejects) */
  function execute(exe, args, cwd, { timeoutMs, runId, onLine, uninterruptible = false }) {
    return new Promise((resolve) => {
      let child;
      try {
        child = spawn(exe, args, { cwd, env: toolEnv(exe), shell: false, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
      } catch (err) {
        resolve({ spawnError: String(err && err.message ? err.message : err) });
        return;
      }
      const entry = { child, cancelled: false, uninterruptible };
      if (runId) running.set(runId, entry);

      const out = { stdout: [], stderr: [], bytes: { stdout: 0, stderr: 0 }, partial: { stdout: '', stderr: '' } };
      let overflow = false;
      let timedOut = false;

      const collect = (stream) => (chunk) => {
        if (overflow) return;
        out.bytes[stream] += chunk.length;
        if (out.bytes[stream] > LIMITS.streamBytes) {
          overflow = true;
          killTree(child);
          return;
        }
        out[stream].push(chunk);
        if (onLine) {
          const text = out.partial[stream] + chunk.toString('utf8');
          const lines = text.split(/\r?\n/);
          out.partial[stream] = lines.pop();
          for (const line of lines) onLine(stream, line);
        }
      };
      child.stdout.on('data', collect('stdout'));
      child.stderr.on('data', collect('stderr'));

      const timer = setTimeout(() => {
        timedOut = true;
        killTree(child);
      }, timeoutMs);

      let settled = false;
      const finish = (result) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        if (runId) running.delete(runId);
        if (onLine) for (const s of ['stdout', 'stderr']) if (out.partial[s]) onLine(s, out.partial[s]);
        resolve({
          ...result,
          stdout: Buffer.concat(out.stdout).toString('utf8'),
          stderr: Buffer.concat(out.stderr).toString('utf8'),
          overflow,
          timedOut,
          cancelled: entry.cancelled,
        });
      };
      child.on('error', (err) => finish({ spawnError: String(err && err.message ? err.message : err) }));
      child.on('close', (code, signal) => finish({ exitCode: code === null ? -1 : code, signal }));
    });
  }

  async function probe(id) {
    if (!Object.prototype.hasOwnProperty.call(TOOLS, id)) return { available: false, reason: 'not-installed' };
    if (probeCache.has(id)) return probeCache.get(id);
    const exe = resolveExecutable(id);
    let result = { available: false, reason: 'not-installed' };
    if (exe) {
      const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lds-probe-'));
      try {
        const r = await execute(exe, TOOLS[id].versionArgs, tmp, { timeoutMs: LIMITS.probeTimeoutMs });
        if (!r.spawnError && !r.timedOut) {
          const firstLine = `${r.stdout}\n${r.stderr}`.split(/\r?\n/).map((l) => l.trim()).find((l) => l !== '');
          result = { available: true, version: firstLine ? firstLine.slice(0, 200) : undefined };
        }
      } finally {
        fs.rmSync(tmp, { recursive: true, force: true });
      }
    }
    // Only a found tool is remembered: one installed later is picked up the next time the page asks
    if (result.available) probeCache.set(id, result);
    return result;
  }

  /** Forgets probe results (after the settings change) */
  function resetProbes() {
    probeCache.clear();
  }

  async function run(req) {
    // --- validate everything the page sent ---
    if (!req || typeof req !== 'object') return toolError('bad-request', 'Missing request');
    const { runId, tool, args, files, outputs } = req;
    if (typeof runId !== 'string' || runId.length === 0 || runId.length > 100) return toolError('bad-request', 'Bad run id');
    if (running.has(runId) || confirming.has(runId)) return toolError('bad-request', 'Run id already in use');
    if (!Object.prototype.hasOwnProperty.call(TOOLS, tool)) return toolError('bad-request', 'Unknown tool');
    if (!Array.isArray(args) || args.length > LIMITS.args) return toolError('bad-request', 'Bad arguments');
    for (const a of args) {
      if (typeof a !== 'string' || a.length > LIMITS.argLength || a.includes('\0')) return toolError('bad-request', 'Bad argument');
    }
    const fileEntries = files && typeof files === 'object' ? Object.entries(files) : [];
    if (fileEntries.length > LIMITS.files) return toolError('bad-request', 'Too many files');
    let inputBytes = 0;
    for (const [rel, data] of fileEntries) {
      if (!isSafeRelativePath(rel)) return toolError('bad-request', `Unsafe file path: ${rel}`);
      if (typeof data !== 'string' && !(data instanceof Uint8Array)) return toolError('bad-request', `Bad file data: ${rel}`);
      inputBytes += typeof data === 'string' ? Buffer.byteLength(data) : data.length;
    }
    if (inputBytes > LIMITS.inputBytes) return toolError('bad-request', 'Input files too large');
    const outputList = Array.isArray(outputs) ? outputs : [];
    if (outputList.length > LIMITS.files) return toolError('bad-request', 'Too many outputs');
    for (const rel of outputList) if (!isSafeRelativePath(rel)) return toolError('bad-request', `Unsafe output path: ${rel}`);
    // Per-tool argument policy: no program starts, no plugins load, no file outside the run folder is named.
    const policy = checkToolRequest(tool, args, files || {});
    if (!policy.ok) return toolError('bad-request', policy.message);
    const timeoutMs = Number.isFinite(req.timeoutMs) && req.timeoutMs > 0 ? Math.min(req.timeoutMs, LIMITS.timeoutMs) : LIMITS.defaultTimeoutMs;

    const exe = resolveExecutable(tool);
    if (!exe) return toolError('unavailable', `${tool} is not installed`);

    const exclusive = TOOLS[tool].exclusive === true;
    if (exclusive && busyTools.has(tool)) return toolError('busy', `${tool} is already running`);
    if (exclusive) busyTools.add(tool);
    try {
      const confirmation = confirmationFor(tool, args);
      if (confirmation) {
        // Cancelling the run while the question is open closes the question (as "no")
        const gate = { cancelled: false, abort: new AbortController() };
        confirming.set(runId, gate);
        let yes = false;
        try {
          const data = Object.prototype.hasOwnProperty.call(files || {}, confirmation.file) ? files[confirmation.file] : undefined;
          const bytes = typeof data === 'string' ? Buffer.byteLength(data) : data ? data.length : 0;
          yes = typeof confirmRun === 'function' && (await confirmRun({ tool, kind: confirmation.kind, file: confirmation.file, bytes, signal: gate.abort.signal })) === true;
        } catch {
          yes = false;
        } finally {
          confirming.delete(runId);
        }
        if (gate.cancelled) return toolError('cancelled', 'Cancelled');
        if (!yes) return toolError('cancelled', 'Declined by the user');
      }
      // A confirmed flash write is not killed by a cancel (page reload, Cancel): openFPGALoader stopped halfway would
      // leave the board's flash half written. Its timeout still applies.
      const uninterruptible = !!confirmation && confirmation.kind === 'flashWrite';
      return await runInFolder(exe, { runId, tool, args, fileEntries, outputList, timeoutMs, uninterruptible });
    } finally {
      if (exclusive) busyTools.delete(tool);
    }
  }

  /** Writes the inputs to a fresh temporary folder, runs the tool there and reads back the named outputs */
  async function runInFolder(exe, { runId, args, fileEntries, outputList, timeoutMs, uninterruptible }) {
    const started = Date.now();
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'lds-tool-'));
    try {
      for (const [rel, data] of fileEntries) {
        const full = inside(dir, rel);
        if (!full) return toolError('bad-request', `Unsafe file path: ${rel}`);
        fs.mkdirSync(path.dirname(full), { recursive: true });
        fs.writeFileSync(full, typeof data === 'string' ? data : Buffer.from(data));
      }
      // Tools rarely create missing folders, so the folders of the requested outputs exist before the run.
      for (const rel of outputList) {
        const full = inside(dir, rel);
        if (!full) return toolError('bad-request', `Unsafe output path: ${rel}`);
        fs.mkdirSync(path.dirname(full), { recursive: true });
      }

      // Lines go to the page in small batches so a chatty tool does not flood IPC.
      let pending = [];
      let flushTimer = null;
      const flush = () => {
        flushTimer = null;
        if (pending.length) onProgress(runId, { phase: 'run', lines: pending });
        pending = [];
      };
      const onLine = (stream, line) => {
        pending.push({ stream, line: line.slice(0, 2000) });
        if (!flushTimer) flushTimer = setTimeout(flush, 100);
      };

      const r = await execute(exe, args, dir, { timeoutMs, runId, onLine, uninterruptible });
      if (flushTimer) clearTimeout(flushTimer);
      flush();

      if (r.cancelled) return toolError('cancelled', 'Cancelled');
      if (r.timedOut) return toolError('timeout', `Stopped after ${timeoutMs} ms`);
      if (r.overflow) return toolError('output-limit', 'Too much output');
      if (r.spawnError) return toolError('internal', r.spawnError);

      const outFiles = {};
      let outBytes = 0;
      for (const rel of outputList) {
        const full = inside(dir, rel);
        if (!full || !isFile(full)) continue;
        const size = fs.statSync(full).size;
        outBytes += size;
        if (outBytes > LIMITS.outputBytes) return toolError('output-limit', 'Output files too large');
        outFiles[rel] = new Uint8Array(fs.readFileSync(full));
      }
      return { exitCode: r.exitCode, stdout: r.stdout, stderr: r.stderr, files: outFiles, durationMs: Date.now() - started };
    } catch (err) {
      return toolError('internal', String(err && err.message ? err.message : err));
    } finally {
      fs.rm(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }, () => {});
    }
  }

  function cancel(runId) {
    const gate = confirming.get(runId);
    if (gate) {
      gate.cancelled = true;
      gate.abort.abort();
      return true;
    }
    const entry = running.get(runId);
    if (!entry || entry.uninterruptible) return false;
    entry.cancelled = true;
    killTree(entry.child);
    return true;
  }

  function cancelAll() {
    for (const id of [...running.keys(), ...confirming.keys()]) cancel(id);
  }

  return { probe, run, cancel, cancelAll, resetProbes };
}

module.exports = { createToolRunner, TOOLS, isSafeRelativePath };
