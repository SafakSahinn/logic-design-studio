// openXC7 package support for the native ToolRunner (Aşama 6j-6): the parts of a run the page never names.
//
// The openXC7 package (Apio's build: bin/, lib/python3.12/site-packages, libexec/, share/nextpnr/...) keeps the
// Project X-Ray database and the fasm2frames Python program next to its executables. The page sends only a part
// name and relative file names; this module turns them into the database paths, the Python interpreter and the
// fixed script path. Nothing here comes from the page except the part name, which is checked against PART_RE and
// must name a folder of the database.
'use strict';

const fs = require('fs');
const path = require('path');

/** A 7-series part with package and speed grade: xc7a35tcpg236-1, xc7z020clg400-1, xc7a200tfbg484-2L ... */
const PART_RE = /^xc7[aksz]\d{1,3}t?s?[a-z]{2,5}\d{3,4}-[1-3]L?$/;

/** Project X-Ray family folder of a part */
function partFamily(part) {
  if (typeof part !== 'string' || !PART_RE.test(part)) return null;
  return { a: 'artix7', k: 'kintex7', s: 'spartan7', z: 'zynq7' }[part[3]] || null;
}

function isDir(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function isFile(p) {
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

/**
 * The openXC7 package around one of its executables (bin/xc7frames2bit.exe), or null when the folder does not
 * look like the package.
 */
function locatePackage(exe) {
  if (typeof exe !== 'string' || !path.isAbsolute(exe)) return null;
  const root = path.resolve(path.dirname(exe), '..');
  const pkg = {
    root,
    dbRoot: path.join(root, 'share', 'nextpnr', 'external', 'prjxray-db'),
    site: path.join(root, 'lib', 'python3.12', 'site-packages'),
    script: path.join(root, 'libexec', 'fasm2frames'),
  };
  if (!isDir(pkg.dbRoot) || !isDir(pkg.site) || !isFile(pkg.script)) return null;
  return pkg;
}

/** part.yaml of a part in the package's database, or null for a part the database does not have */
function partFile(pkg, part) {
  const family = partFamily(part);
  if (!pkg || !family) return null;
  const file = path.join(pkg.dbRoot, family, part, 'part.yaml');
  return isFile(file) ? file : null;
}

/** The database folder of a part's family (fasm2frames --db-root), or null */
function familyRoot(pkg, part) {
  const family = partFamily(part);
  if (!pkg || !family) return null;
  const dir = path.join(pkg.dbRoot, family);
  return isDir(dir) ? dir : null;
}

/**
 * Runs a Python file in isolated mode (-I: no PYTHON* variables, no user site, the current folder is not on
 * sys.path, so files the page wrote to the run folder are never imported). The package's site-packages folder
 * is put first on sys.path. The script and site paths come from argv, never from the code string.
 */
const PY_RUN = "import sys,runpy;s=sys.argv[1];sys.path.insert(0,sys.argv[2]);sys.argv=[s]+sys.argv[3:];runpy.run_path(s,run_name='__main__')";
/** Prints one version line when the interpreter can import fasm and prjxray from the package */
const PY_PROBE = "import sys;sys.path.insert(0,sys.argv[1]);import fasm,prjxray;print('fasm2frames (Project X-Ray), Python %d.%d.%d' % sys.version_info[:3])";

/** Command line of an isolated fasm2frames run: python -I -c PY_RUN script site --db-root <family> <page args> */
function fasm2framesArgs(pkg, dbFamilyRoot, pageArgs) {
  return ['-I', '-c', PY_RUN, pkg.script, pkg.site, '--db-root', dbFamilyRoot, ...pageArgs];
}

function probeArgs(pkg) {
  return ['-I', '-c', PY_PROBE, pkg.site];
}

/**
 * Python interpreters to try, best first: settings.toolPaths.python, the Python of the OSS CAD Suite that provides
 * yosys (its lib folder has python3.exe), then python3 / python on the search folders. Microsoft Store aliases
 * (WindowsApps) are skipped: they only open the Store.
 */
function pythonCandidates({ settings, yosysExe, dirs, isWin }) {
  const names = isWin ? ['python3.exe', 'python.exe'] : ['python3', 'python'];
  const list = [];
  const fixed = settings && settings.toolPaths && settings.toolPaths.python;
  if (typeof fixed === 'string' && path.isAbsolute(fixed)) list.push(fixed);
  if (yosysExe) {
    const bin = path.dirname(yosysExe);
    for (const d of [path.join(bin, '..', 'lib'), bin]) for (const n of names) list.push(path.resolve(d, n));
  }
  for (const d of dirs) {
    if (/[\\/]WindowsApps([\\/]|$)/i.test(d)) continue;
    for (const n of names) list.push(path.join(d, n));
  }
  // As every other tool: only real executables on Windows (a .bat/.cmd shim would need a shell)
  return [...new Set(list)].filter((p) => isFile(p) && (!isWin || path.extname(p).toLowerCase() === '.exe'));
}

module.exports = { PART_RE, partFamily, locatePackage, partFile, familyRoot, fasm2framesArgs, probeArgs, pythonCandidates };
