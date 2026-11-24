// Installed vendor FPGA tools (Aşama 6k-1): where Vivado, Quartus and ISE are, how to start them.
//
// Four kinds of installs are told apart:
//   vivado         AMD/Xilinx Vivado (7-series)               bin/vivado.bat
//   quartus        Intel Quartus Prime (Lite/Standard)        quartus/bin64/quartus_sh.exe
//   quartusLegacy  Altera Quartus II up to 13.0 (Cyclone I-III, MAX 3000/7000; Prime no longer has them)
//   ise            Xilinx ISE 14.x (Spartan-3/6, CoolRunner)  ISE_DS/ISE/bin/nt64/xst.exe
//
// Lookup per kind: settings.vendorPaths[kind] (set only by the main process, from a folder the user picked in a
// native dialog), then the installers' environment variables and default folders, newest version first. The page
// never names a path; it names a tool id and a part, and this module decides which program runs.
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const KINDS = ['vivado', 'quartus', 'quartusLegacy', 'ise'];
const ISE_PROGRAMS = ['xst', 'ngdbuild', 'map', 'par', 'bitgen'];

function isFile(p) {
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

function listDirs(dir) {
  try {
    return fs.readdirSync(dir, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name);
  } catch {
    return [];
  }
}

/** "2026.1" -> [2026, 1]; "25.1std" -> [25, 1]; "13.0sp1" -> [13, 0, 1]; anything else -> null */
function parseVersion(text) {
  const m = /^(\d{1,4})\.(\d{1,2})(?:\.(\d{1,2}))?(?:sp(\d{1,2}))?(?:std|pro|lite)?$/i.exec(String(text || '').trim());
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3] || m[4] || 0)];
}

function compareVersions(a, b) {
  if (!a || !b) return a ? 1 : b ? -1 : 0;
  for (let i = 0; i < 3; i++) if (a[i] !== b[i]) return a[i] - b[i];
  return 0;
}

/** The version of an install, from the folder names on its path (C:\altera_lite\25.1std\quartus\bin64 -> 25.1std) */
function versionFromPath(exe) {
  const parts = path.resolve(exe).split(/[\\/]/).reverse();
  for (const p of parts) if (parseVersion(p)) return p;
  return null;
}

/** Quartus II up to 13.0 (sp1) is the last with Cyclone I/II/III and MAX 3000/7000 */
const isLegacyQuartus = (version) => {
  const v = parseVersion(version);
  return !!v && compareVersions(v, [13, 1, 0]) < 0;
};

/** Executable file name of a kind (the one the user's folder must contain) */
function exeName(kind, isWin) {
  if (kind === 'vivado') return isWin ? 'vivado.bat' : 'vivado';
  if (kind === 'ise') return isWin ? 'xst.exe' : 'xst';
  return isWin ? 'quartus_sh.exe' : 'quartus_sh';
}

/** Folders below an install root where the executable of a kind can be */
function binFolders(kind, root, isWin) {
  if (kind === 'vivado') return [root, path.join(root, 'bin'), path.join(root, 'Vivado', 'bin')];
  if (kind === 'ise') {
    const arch = isWin ? 'nt64' : 'lin64';
    return [root, path.join(root, 'bin', arch), path.join(root, 'ISE', 'bin', arch), path.join(root, 'ISE_DS', 'ISE', 'bin', arch)];
  }
  const bins = isWin ? ['bin64', 'bin'] : ['bin', 'linux64'];
  return [root, ...bins.map((b) => path.join(root, b)), ...bins.map((b) => path.join(root, 'quartus', b))];
}

/** Install roots to scan: [{ kind, root }] for every kind; "quartus" roots hold Prime and II alike */
function defaultRoots({ env, isWin, home }) {
  const out = [];
  const add = (kind, root) => out.push({ kind, root });
  const versioned = (base, sub) => listDirs(base).filter((d) => parseVersion(d)).map((v) => path.join(base, v, ...sub));
  // Set by the installers (Quartus sets QUARTUS_ROOTDIR, ISE's settings script XILINX, Vivado's XILINX_VIVADO)
  if (env.XILINX_VIVADO) add('vivado', env.XILINX_VIVADO);
  if (env.QUARTUS_ROOTDIR) add('quartus', env.QUARTUS_ROOTDIR);
  if (env.XILINX) add('ise', env.XILINX);
  if (isWin) {
    const drive = (env.SystemDrive || 'C:') + path.sep;
    for (const base of ['AMDDesignTools', 'Xilinx']) for (const r of versioned(path.join(drive, base), ['Vivado'])) add('vivado', r);
    for (const r of versioned(path.join(drive, 'Xilinx', 'Vivado'), [])) add('vivado', r);
    for (const base of ['altera_lite', 'intelFPGA_lite', 'intelFPGA', 'altera']) for (const r of versioned(path.join(drive, base), ['quartus'])) add('quartus', r);
    for (const r of versioned(path.join(drive, 'Xilinx'), ['ISE_DS'])) add('ise', r);
  } else {
    for (const base of ['/opt/Xilinx', '/tools/Xilinx', path.join(home, 'Xilinx')]) {
      for (const r of versioned(base, ['Vivado'])) add('vivado', r);
      for (const r of versioned(path.join(base, 'Vivado'), [])) add('vivado', r);
      for (const r of versioned(base, ['ISE_DS'])) add('ise', r);
    }
    for (const base of ['/opt/intelFPGA_lite', '/opt/intelFPGA', '/opt/altera', path.join(home, 'intelFPGA_lite'), path.join(home, 'intelFPGA'), path.join(home, 'altera')]) {
      for (const r of versioned(base, ['quartus'])) add('quartus', r);
    }
  }
  return out;
}

/** The kind of a found executable: Quartus II up to 13.0 is "quartusLegacy" */
function kindOf(rootKind, version) {
  if (rootKind !== 'quartus') return rootKind;
  return isLegacyQuartus(version) ? 'quartusLegacy' : 'quartus';
}

/**
 * An executable of rootKind under root ({ exe, version, kind }) or null. A version that the folder names do not
 * show stays null (the caller may ask the program).
 */
function locateUnder(rootKind, root, isWin) {
  if (typeof root !== 'string' || !path.isAbsolute(root)) return null;
  for (const dir of binFolders(rootKind, root, isWin)) {
    const exe = path.join(dir, exeName(rootKind, isWin));
    if (!isFile(exe)) continue;
    // ISE: the whole chain must be there
    if (rootKind === 'ise' && !ISE_PROGRAMS.every((p) => isFile(path.join(dir, isWin ? `${p}.exe` : p)))) continue;
    const version = versionFromPath(exe);
    return { exe: path.resolve(exe), version, kind: kindOf(rootKind, version) };
  }
  return null;
}

/**
 * Every install found, per kind, best first: { vivado: [{ exe, version, source }], ... }. A path from the settings
 * comes first ("settings"); the scan finds the rest ("auto"), newest version first.
 */
function findInstalls({ settings = {}, env = process.env, isWin = process.platform === 'win32', home = os.homedir() } = {}) {
  const result = Object.fromEntries(KINDS.map((k) => [k, []]));
  const seen = new Set();
  const push = (hit, source) => {
    const key = hit.exe.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    result[hit.kind].push({ exe: hit.exe, version: hit.version, source });
  };
  const fixed = settings.vendorPaths && typeof settings.vendorPaths === 'object' ? settings.vendorPaths : {};
  for (const kind of KINDS) {
    const entry = fixed[kind];
    const exe = entry && typeof entry === 'object' ? entry.exe : null;
    if (typeof exe !== 'string' || !path.isAbsolute(exe) || path.basename(exe).toLowerCase() !== exeName(kind === 'quartusLegacy' ? 'quartus' : kind, isWin)) continue;
    if (!isFile(exe)) continue;
    push({ exe: path.resolve(exe), version: typeof entry.version === 'string' ? entry.version : versionFromPath(exe), kind }, 'settings');
  }
  const auto = [];
  for (const { kind, root } of defaultRoots({ env, isWin, home })) {
    const hit = locateUnder(kind, root, isWin);
    if (hit) auto.push(hit);
  }
  auto.sort((a, b) => compareVersions(parseVersion(b.version), parseVersion(a.version)));
  for (const hit of auto) push(hit, 'auto');
  return result;
}

/**
 * Quartus kinds that can build a part, preferred first. Quartus Prime has no Cyclone I/II/III and no MAX 3000/7000;
 * Quartus II 13.0 has everything up to Cyclone IV / MAX V, so it is the fallback for those.
 */
function quartusKindsFor(part) {
  const p = String(part || '').toUpperCase();
  if (/^EP(1C|2C|3C)/.test(p) || /^EPM(3|7|9)\d{3}/.test(p) || /^EP(1S|2S|1K|20K)/.test(p)) return ['quartusLegacy'];
  if (/^EP4C/.test(p) || /^EPM(240|570|1270|2210)/.test(p) || /^5M/.test(p)) return ['quartus', 'quartusLegacy'];
  return ['quartus'];
}

/** The tool id of the page that runs a kind */
const toolOfKind = (kind) => (kind === 'quartusLegacy' ? 'quartus' : kind);

/** The PATH key of an environment object (Windows keeps "Path") */
const pathKey = (env) => Object.keys(env).find((k) => k.toUpperCase() === 'PATH') || 'PATH';

/**
 * The environment of a vendor run. ISE gets what its settings64.bat sets (XILINX and the bin/lib folders on PATH),
 * without running the batch file. Vivado's license file is passed on: XILINXD_LICENSE_FILE from the environment,
 * else the default file the license manager writes (%USERPROFILE%\.Xilinx\Xilinx.lic), which Vivado 2026.1 does
 * not look for by itself.
 */
function vendorEnv(kind, exe, { env = process.env, isWin = process.platform === 'win32', home = os.homedir() } = {}) {
  const out = { ...env };
  const key = pathKey(out);
  const extra = [];
  if (kind === 'ise') {
    const arch = isWin ? 'nt64' : 'lin64';
    const iseRoot = path.resolve(path.dirname(exe), '..', '..');
    const dsRoot = path.dirname(iseRoot);
    out.XILINX = iseRoot;
    out.XILINX_DSP = iseRoot;
    extra.push(path.join(iseRoot, 'bin', arch), path.join(iseRoot, 'lib', arch), path.join(dsRoot, 'common', 'bin', arch), path.join(dsRoot, 'common', 'lib', arch));
  } else {
    extra.push(path.dirname(exe));
  }
  if (kind === 'vivado' || kind === 'ise') {
    const lic = path.join(home, '.Xilinx', 'Xilinx.lic');
    if (!out.XILINXD_LICENSE_FILE && isFile(lic)) out.XILINXD_LICENSE_FILE = lic;
  }
  out[key] = [...extra, out[key] || ''].join(path.delimiter);
  return out;
}

/** Characters that would mean something to cmd.exe even inside quotes, or end the quotes */
const CMD_UNSAFE = /["%!^&|<>\r\n\0]/;

/**
 * How to start a program: { file, args, verbatim }. A Windows batch file (vivado.bat) cannot start without cmd.exe;
 * it is run as cmd /d /s /c ""<bat>" <args>" with every part checked to hold nothing cmd would interpret, and with
 * the command line passed verbatim (Node's quoting is for programs, not for cmd). cmd returns the batch file's
 * exit code (vivado.bat ends with "exit /b %errorlevel%").
 */
function launchSpec(exe, args, isWin = process.platform === 'win32') {
  if (!(isWin && /\.(bat|cmd)$/i.test(exe))) return { file: exe, args, verbatim: false };
  if (CMD_UNSAFE.test(exe)) return { error: `The tool path holds a character cmd.exe would interpret: ${exe}` };
  for (const a of args) if (CMD_UNSAFE.test(a) || /\s/.test(a) || a === '') return { error: `Argument refused for a batch file: ${a}` };
  const comspec = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'cmd.exe');
  return { file: comspec, args: ['/d', '/s', '/c', `""${exe}" ${args.join(' ')}"`], verbatim: true };
}

/**
 * The install a folder the user picked holds: { kind, exe, version } or null. Looks for every kind's executable
 * in the usual sub folders (the user may pick C:\altera_lite\25.1std, its quartus folder or its bin64 folder).
 */
function locateInFolder(folder, isWin = process.platform === 'win32') {
  for (const rootKind of ['vivado', 'quartus', 'ise']) {
    const hit = locateUnder(rootKind, folder, isWin);
    if (hit) return hit;
  }
  return null;
}

module.exports = {
  KINDS,
  ISE_PROGRAMS,
  parseVersion,
  compareVersions,
  isLegacyQuartus,
  findInstalls,
  quartusKindsFor,
  toolOfKind,
  vendorEnv,
  launchSpec,
  locateInFolder,
  exeName,
};
