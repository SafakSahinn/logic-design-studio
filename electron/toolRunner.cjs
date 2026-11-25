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
const openxc7 = require('./openxc7.cjs');
const vendor = require('./vendorTools.cjs');
const { parseVendorArgs } = require('./vendorPolicy.cjs');
const { scriptFor } = require('./vendorScripts.cjs');

const IS_WIN = process.platform === 'win32';

/** Allowlist: tool id -> executable base name and probe arguments */
const TOOLS = {
  ghdl: { executable: 'ghdl', versionArgs: ['--version'] },
  yosys: { executable: 'yosys', versionArgs: ['-V'] },
  'nextpnr-ecp5': { executable: 'nextpnr-ecp5', versionArgs: ['--version'] },
  ecppack: { executable: 'ecppack', versionArgs: ['--version'] },
  // Xilinx 7-series through openXC7 (6j-6). The database paths are added here, never sent by the page (openxc7.cjs).
  'nextpnr-xilinx': { executable: 'nextpnr-xilinx', versionArgs: ['--version'] },
  xc7frames2bit: { executable: 'xc7frames2bit', versionArgs: ['--version'], launch: 'xc7frames2bit' },
  // A Python program of the openXC7 package: found through the package's xc7frames2bit, run by a Python 3
  fasm2frames: { executable: 'xc7frames2bit', versionArgs: [], launch: 'fasm2frames' },
  // Talks to a board over USB: one run at a time, since two programmers on the same cable would collide.
  openfpgaloader: { executable: 'openFPGALoader', versionArgs: ['--version'], exclusive: true },
  // Vendor FPGA tools (6k-1): found by vendorTools.cjs (installs, not PATH), started from fixed templates
  // (vendorScripts.cjs). The page sends an option line (vendorPolicy.cjs), never a script. executable is informative
  // (the same as src/tools/registry.ts); vendorTools.cjs decides the real program.
  vivado: { vendor: true, executable: 'vivado', versionArgs: [] },
  quartus: { vendor: true, executable: 'quartus_sh', versionArgs: [] },
  ise: { vendor: true, executable: 'xst', versionArgs: [] },
};

/** Arguments that print a vendor install's version (the "check" button); xst -help also shows the ISE start-up hang */
const VENDOR_CHECK = { vivado: ['-version'], quartus: ['--version'], quartusLegacy: ['--version'], ise: ['-help'] };

const BASE_LIMITS = {
  args: 512,
  argLength: 64 * 1024,
  files: 512,
  inputBytes: 64 * 1024 * 1024,
  outputBytes: 128 * 1024 * 1024,
  streamBytes: 16 * 1024 * 1024, // per stream (stdout, stderr)
  timeoutMs: 30 * 60 * 1000, // ceiling for a requested timeout
  defaultTimeoutMs: 60 * 1000,
  probeTimeoutMs: 15 * 1000,
  // A vendor tool that prints nothing at all for this long has hung at start-up (ISE: a network provider, see
  // the "stalled" hint); a working one prints its banner within seconds
  vendorFirstOutputMs: 90 * 1000,
  vendorCheckTimeoutMs: 120 * 1000,
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
function createToolRunner({ readSettings, onProgress, confirmRun, limits }) {
  // limits: test-only overrides of BASE_LIMITS (the app never passes it)
  const LIMITS = { ...BASE_LIMITS, ...(limits && typeof limits === 'object' ? limits : {}) };
  const probeCache = new Map(); // tool id -> { available, version?, exe? }
  const running = new Map(); // run id -> { child, cancelled }
  const busyTools = new Set(); // exclusive tools with a run in progress (including its confirmation)
  const confirming = new Map(); // run id -> { cancelled } while the user is asked

  /** settings.toolSearchDirs, then PATH: absolute folders only */
  function searchDirs(settings) {
    return [
      ...(Array.isArray(settings.toolSearchDirs) ? settings.toolSearchDirs : []),
      ...String(process.env.PATH || '').split(path.delimiter),
    ]
      .filter((d) => typeof d === 'string' && d.trim() !== '' && path.isAbsolute(d.trim()))
      .map((d) => d.trim());
  }

  function candidates(id) {
    const def = TOOLS[id];
    const settings = readSettings() || {};
    const names = IS_WIN ? [`${def.executable}.exe`] : [def.executable];
    const list = [];
    // fasm2frames is found through the package's xc7frames2bit, so it shares that tool's fixed path
    const fixed = settings.toolPaths && settings.toolPaths[def.launch === 'fasm2frames' ? 'xc7frames2bit' : id];
    if (typeof fixed === 'string' && path.isAbsolute(fixed)) list.push(fixed);
    for (const d of searchDirs(settings)) for (const n of names) list.push(path.join(d, n));
    return list;
  }

  function resolveExecutable(id) {
    const def = TOOLS[id];
    for (const c of candidates(id)) {
      // Only real executables: on Windows a .bat/.cmd would need a shell, which is never used here.
      if (IS_WIN && path.extname(c).toLowerCase() !== '.exe') continue;
      if (!isFile(c)) continue;
      // The openXC7 bitstream tools need their package around them; another xc7frames2bit (a plain Project X-Ray
      // build) earlier on PATH is passed over
      if (def.launch && !openxc7.locatePackage(c)) continue;
      return c;
    }
    return null;
  }

  // The interpreter search for fasm2frames, per package + settings: { key, promise } resolving to
  // { exe, version } or null. A miss is remembered too (resetProbes forgets it), and callers share one search.
  let pythonCache = null;

  /** A Python 3 that imports the package's fasm and prjxray modules, or null */
  function packagePython(pkg) {
    const settings = readSettings() || {};
    const key = JSON.stringify([pkg.root, settings.toolPaths && settings.toolPaths.python, settings.toolSearchDirs, process.env.PATH]);
    if (pythonCache && pythonCache.key === key) return pythonCache.promise;
    const search = async () => {
      const yosysExe = resolveExecutable('yosys');
      for (const exe of openxc7.pythonCandidates({ settings, yosysExe, dirs: searchDirs(settings), isWin: IS_WIN })) {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lds-probe-'));
        try {
          const r = await execute(exe, openxc7.probeArgs(pkg), tmp, { timeoutMs: LIMITS.probeTimeoutMs });
          if (!r.spawnError && !r.timedOut && r.exitCode === 0) return { exe, version: r.stdout.trim().split(/\r?\n/)[0] };
        } finally {
          fs.rmSync(tmp, { recursive: true, force: true });
        }
      }
      return null;
    };
    pythonCache = { key, promise: search() };
    return pythonCache.promise;
  }

  /** Vendor installs found now, per kind, best first (vendorTools.findInstalls) */
  function vendorInstalls() {
    return vendor.findInstalls({ settings: readSettings() || {} });
  }

  /** The install a vendor request runs on ({ kind, exe, version }) or a tool error naming what is missing */
  function pickVendorInstall(tool, request) {
    const installs = vendorInstalls();
    const kinds = tool === 'quartus' ? vendor.quartusKindsFor(request.part) : [tool];
    for (const kind of kinds) if (installs[kind].length) return { kind, ...installs[kind][0] };
    const names = { vivado: 'Vivado', quartus: 'Quartus Prime', quartusLegacy: 'Quartus II 13.0sp1', ise: 'ISE 14.7' };
    return toolError('unavailable', `${kinds.map((k) => names[k]).join(' or ')} is not installed (needed for ${request.part || tool})`);
  }

  /**
   * A vendor request's launch: the program (an ISE step's executable, or the batch file through cmd.exe), its
   * command line and the generated files, all from fixed templates; the page's option line only fills them in.
   */
  function resolveVendorLaunch(tool, args) {
    const parsed = parseVendorArgs(tool, args);
    if (!parsed.ok) return toolError('bad-request', parsed.message);
    const install = pickVendorInstall(tool, parsed.request);
    if (install.error) return install;
    let script;
    try {
      script = scriptFor(tool, parsed.request);
    } catch (err) {
      return toolError('bad-request', String(err && err.message ? err.message : err));
    }
    const exe = script.program ? path.join(path.dirname(install.exe), IS_WIN ? `${script.program}.exe` : script.program) : install.exe;
    if (!isFile(exe)) return toolError('unavailable', `${tool}: ${exe} is missing`);
    const spec = vendor.launchSpec(exe, script.args, IS_WIN);
    if (spec.error) return toolError('bad-request', spec.error);
    return {
      exe: spec.file,
      args: spec.args,
      verbatim: spec.verbatim,
      env: vendor.vendorEnv(install.kind, install.exe),
      extraFiles: script.files,
      appendFiles: script.append,
      firstOutputMs: LIMITS.vendorFirstOutputMs,
      install: { kind: install.kind, version: install.version },
      // A board-programming step holds the JTAG cable: one at a time, like openFPGALoader
      exclusiveKey: parsed.request.bitstream ? `${tool}:${parsed.request.step}` : null,
    };
  }

  /**
   * The vendor installs for the settings panel: per kind the one a run uses and the others found, with where it
   * came from ("settings": picked by the user, "auto": found).
   */
  function vendorStatus() {
    const installs = vendorInstalls();
    return Object.fromEntries(vendor.KINDS.map((k) => [k, installs[k].map(({ exe, version, source }) => ({ exe, version, source }))]));
  }

  /**
   * Runs an install's version command: { ok, version?, stalled?, exitCode?, output? }. Shows a broken install
   * (ISE hanging at start-up) before a build does.
   */
  async function vendorCheck(kind) {
    if (!vendor.KINDS.includes(kind)) return { ok: false, message: 'Unknown kind' };
    const install = vendorInstalls()[kind][0];
    if (!install) return { ok: false, notInstalled: true };
    const spec = vendor.launchSpec(install.exe, VENDOR_CHECK[kind], IS_WIN);
    if (spec.error) return { ok: false, message: spec.error };
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lds-probe-'));
    try {
      const r = await execute(spec.file, spec.args, tmp, {
        timeoutMs: LIMITS.vendorCheckTimeoutMs,
        env: vendor.vendorEnv(kind, install.exe),
        verbatim: spec.verbatim,
        firstOutputMs: LIMITS.vendorFirstOutputMs,
      });
      const output = `${r.stdout}\n${r.stderr}`.trim().slice(0, 4000);
      if (r.stalled) return { ok: false, stalled: true, exe: install.exe };
      if (r.spawnError || r.timedOut) return { ok: false, exe: install.exe, message: r.spawnError || 'timeout', output };
      // vivado -version (2026.1) exits with 1 and xst -help with a non-zero code on some versions: the banner
      // proves the program starts
      const ok = r.exitCode === 0 || (kind === 'ise' && /Release\s+14\./i.test(output)) || (kind === 'vivado' && /^vivado v\d{4}\.\d/im.test(output));
      const first = output.split(/\r?\n/).map((l) => l.trim()).find((l) => l !== '');
      return { ok, exe: install.exe, version: install.version, exitCode: r.exitCode, output: ok ? first : output };
    } finally {
      fs.rm(tmp, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }, () => {});
    }
  }

  /**
   * The install in a folder the user picked in the main process's own dialog: { kind, exe, version } or null.
   * Quartus folders that do not show the version are asked (quartus_sh --version), since Quartus II 13.0 and
   * Quartus Prime cover different families.
   */
  async function locateVendorFolder(folder) {
    const hit = vendor.locateInFolder(folder, IS_WIN);
    if (!hit || hit.version || hit.kind === 'vivado' || hit.kind === 'ise') return hit;
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lds-probe-'));
    try {
      const r = await execute(hit.exe, ['--version'], tmp, { timeoutMs: LIMITS.vendorCheckTimeoutMs, env: vendor.vendorEnv(hit.kind, hit.exe) });
      // "Version 13.0.1 Build 232 06/12/2013 Service Pack 1 SJ Web Edition", "Version 25.1std.0 Build 1129 ..."
      const m = /Version\s+(\d{1,4}\.\d{1,2}(?:\.\d{1,2})?)/i.exec(r.stdout || '');
      if (!m) return hit;
      return { ...hit, version: m[1], kind: vendor.isLegacyQuartus(m[1]) ? 'quartusLegacy' : 'quartus' };
    } finally {
      fs.rm(tmp, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }, () => {});
    }
  }

  /**
   * The program and command line a request really runs, or a tool error. Most tools run their executable with the
   * page's arguments. The openXC7 bitstream tools also get their database paths here, from the part name the
   * policy already checked (toolPolicy.cjs): the page never names a file outside the run folder.
   */
  async function resolveLaunch(id, args) {
    const def = TOOLS[id];
    if (def.vendor) return resolveVendorLaunch(id, args);
    const exe = resolveExecutable(id);
    if (!exe) return toolError('unavailable', `${id} is not installed`);
    if (!def.launch) return { exe, args };
    const pkg = openxc7.locatePackage(exe);
    if (!pkg) return toolError('unavailable', `${id}: the openXC7 package around ${exe} is incomplete`);
    const at = args.indexOf(def.launch === 'fasm2frames' ? '--part' : '--part_name');
    const part = at >= 0 ? args[at + 1] : undefined;
    if (def.launch === 'xc7frames2bit') {
      const yaml = openxc7.partFile(pkg, part);
      if (!yaml) return toolError('bad-request', `The openXC7 database has no part ${part}`);
      return { exe, args: [...args, '--part_file', yaml] };
    }
    const dbFamily = openxc7.familyRoot(pkg, part);
    if (!dbFamily || !openxc7.partFile(pkg, part)) return toolError('bad-request', `The openXC7 database has no part ${part}`);
    const python = await packagePython(pkg);
    if (!python) return toolError('unavailable', 'fasm2frames needs Python 3 with the openXC7 modules; none was found (the OSS CAD Suite ships one)');
    return { exe: python.exe, args: openxc7.fasm2framesArgs(pkg, dbFamily, args) };
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

  /**
   * Runs exe with args in cwd; resolves when it exits (never rejects). env replaces the default tool environment;
   * verbatim passes the command line as is (cmd.exe, see vendorTools.launchSpec); firstOutputMs stops a program
   * that has printed nothing at all by then ("stalled").
   */
  function execute(exe, args, cwd, { timeoutMs, runId, onLine, uninterruptible = false, env, verbatim = false, firstOutputMs }) {
    return new Promise((resolve) => {
      let child;
      try {
        child = spawn(exe, args, {
          cwd,
          env: env || toolEnv(exe),
          shell: false,
          windowsHide: true,
          windowsVerbatimArguments: verbatim,
          stdio: ['ignore', 'pipe', 'pipe'],
        });
      } catch (err) {
        resolve({ spawnError: String(err && err.message ? err.message : err) });
        return;
      }
      const entry = { child, cancelled: false, uninterruptible };
      if (runId) running.set(runId, entry);

      const out = { stdout: [], stderr: [], bytes: { stdout: 0, stderr: 0 }, partial: { stdout: '', stderr: '' } };
      let overflow = false;
      let timedOut = false;
      let stalled = false;
      let stallTimer = null;
      if (firstOutputMs) {
        stallTimer = setTimeout(() => {
          stalled = true;
          killTree(child);
        }, firstOutputMs);
      }

      const collect = (stream) => (chunk) => {
        if (stallTimer) {
          clearTimeout(stallTimer);
          stallTimer = null;
        }
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
        if (stallTimer) clearTimeout(stallTimer);
        if (runId) running.delete(runId);
        if (onLine) for (const s of ['stdout', 'stderr']) if (out.partial[s]) onLine(s, out.partial[s]);
        resolve({
          ...result,
          stdout: Buffer.concat(out.stdout).toString('utf8'),
          stderr: Buffer.concat(out.stderr).toString('utf8'),
          overflow,
          timedOut,
          stalled,
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
    if (TOOLS[id].vendor) {
      // Found on disk is enough here: starting Vivado only to print its version takes many seconds (vendorCheck
      // does that on request). Quartus counts Prime and II alike; the run picks one per part.
      const installs = vendorInstalls();
      const found = (id === 'quartus' ? ['quartus', 'quartusLegacy'] : [id]).flatMap((k) => installs[k]);
      if (!found.length) return { available: false, reason: 'not-installed' };
      return { available: true, version: found.map((f) => f.version || path.basename(path.dirname(f.exe))).join(', ').slice(0, 200) };
    }
    const exe = resolveExecutable(id);
    let result = { available: false, reason: 'not-installed' };
    if (exe && TOOLS[id].launch === 'fasm2frames') {
      const pkg = openxc7.locatePackage(exe);
      const python = pkg ? await packagePython(pkg) : null;
      if (python) result = { available: true, version: python.version ? python.version.slice(0, 200) : undefined };
    } else if (exe) {
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
    pythonCache = null;
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

    // The launch can take a while (the first fasm2frames run looks for a Python): the run id is reserved meanwhile,
    // so a cancel (Cancel, page reload) during that time is not lost
    const reserve = { cancelled: false, abort: new AbortController() };
    confirming.set(runId, reserve);
    let launch;
    try {
      launch = await resolveLaunch(tool, args);
    } finally {
      confirming.delete(runId);
    }
    if (reserve.cancelled) return toolError('cancelled', 'Cancelled');
    if (launch.error) return launch;

    // Exclusive tools (openFPGALoader) run one at a time; a vendor tool only for its programming step
    const busyKey = TOOLS[tool].exclusive === true ? tool : launch.exclusiveKey || null;
    const exclusive = busyKey !== null;
    if (exclusive && busyTools.has(busyKey)) return toolError('busy', `${busyKey} is already running`);
    if (exclusive) busyTools.add(busyKey);
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
      // A confirmed flash or CPLD write is not killed by a cancel (page reload, Cancel): a programmer stopped halfway
      // would leave the board's flash (or the CPLD) half written. Its timeout still applies.
      const uninterruptible = !!confirmation && (confirmation.kind === 'flashWrite' || confirmation.kind === 'cpldWrite');
      return await runInFolder(launch.exe, {
        runId,
        tool,
        args: launch.args,
        fileEntries,
        outputList,
        timeoutMs,
        uninterruptible,
        env: launch.env,
        verbatim: launch.verbatim,
        extraFiles: launch.extraFiles,
        appendFiles: launch.appendFiles,
        firstOutputMs: launch.firstOutputMs,
      });
    } finally {
      if (exclusive) busyTools.delete(busyKey);
    }
  }

  /** Writes the inputs to a fresh temporary folder, runs the tool there and reads back the named outputs */
  async function runInFolder(exe, { runId, args, fileEntries, outputList, timeoutMs, uninterruptible, env, verbatim, extraFiles, appendFiles, firstOutputMs }) {
    const started = Date.now();
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'lds-tool-'));
    try {
      for (const [rel, data] of fileEntries) {
        const full = inside(dir, rel);
        if (!full) return toolError('bad-request', `Unsafe file path: ${rel}`);
        fs.mkdirSync(path.dirname(full), { recursive: true });
        fs.writeFileSync(full, typeof data === 'string' ? data : Buffer.from(data));
      }
      // Files of the main process's own templates (a vendor tool's script): never one of the page's files
      for (const [rel, text] of Object.entries(extraFiles || {})) {
        const full = inside(dir, rel);
        if (!full || fileEntries.some(([name]) => name.toLowerCase() === rel.toLowerCase())) return toolError('bad-request', `Reserved file name: ${rel}`);
        fs.writeFileSync(full, text);
      }
      // Fixed lines of a template added to one of the page's (already checked) files: the Quartus .qsf
      for (const [rel, text] of Object.entries(appendFiles || {})) {
        const full = inside(dir, rel);
        if (!full || !fileEntries.some(([name]) => name === rel)) return toolError('bad-request', `Missing file: ${rel}`);
        fs.appendFileSync(full, text);
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

      const r = await execute(exe, args, dir, { timeoutMs, runId, onLine, uninterruptible, env, verbatim, firstOutputMs });
      if (flushTimer) clearTimeout(flushTimer);
      flush();

      if (r.cancelled) return toolError('cancelled', 'Cancelled');
      if (r.stalled) return toolError('stalled', `No output for ${Math.round(firstOutputMs / 1000)} s after the start: the program hung while starting`);
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

  // One hw_server check at a time: concurrent callers share it
  let hwServerCheck = null;
  const hwServer = () => {
    if (!hwServerCheck) hwServerCheck = hwServerRunning().finally(() => (hwServerCheck = null));
    return hwServerCheck;
  };

  return { probe, run, cancel, cancelAll, resetProbes, vendorStatus, vendorCheck, locateVendorFolder, hwServerRunning: hwServer };
}

/**
 * Whether Vivado's hardware server (hw_server.exe or cs_server.exe) is running: Vivado leaves both behind when it
 * exits, and hw_server keeps the JTAG cable open, so openFPGALoader finds no cable. true / false, or null when it
 * cannot be told (not Windows, tasklist failed). Only looks: it never stops a process.
 */
function hwServerRunning({ timeoutMs = 5000 } = {}) {
  if (!IS_WIN) return Promise.resolve(null);
  // tasklist from System32 by its full path, not from the PATH
  const tasklist = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tasklist.exe');
  return new Promise((resolve) => {
    let out = '';
    let done = false;
    const end = (value) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      resolve(value);
    };
    let child;
    try {
      // CSV without a header: one '"name.exe","pid",...' line per process; the "no tasks" text is localized, so only
      // the image names are looked at
      child = spawn(tasklist, ['/FO', 'CSV', '/NH'], { windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'] });
    } catch {
      resolve(null);
      return;
    }
    const timer = setTimeout(() => {
      try {
        child.kill();
      } catch {
        // already gone
      }
      end(null);
    }, timeoutMs);
    child.stdout.on('data', (d) => {
      if (out.length < 4 * 1024 * 1024) out += d.toString('latin1');
    });
    child.on('error', () => end(null));
    child.on('close', (code) => {
      if (code !== 0) return end(null);
      end(/^"(?:hw_server|cs_server)\.exe",/im.test(out));
    });
  });
}

module.exports = { createToolRunner, hwServerRunning, TOOLS, isSafeRelativePath };
