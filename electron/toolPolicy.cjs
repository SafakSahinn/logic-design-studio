// Argument policy for the native ToolRunner (Aşama 6.0c).
//
// The tool allowlist alone is not enough: the tools themselves can run programs and touch any file.
// yosys has `exec`, `shell`, `tcl`, `connect_rpc -exec`, `abc -exe`, `-m <plugin>`; nextpnr runs Python files
// (--run, --pre-pack, ...); ghdl -r runs a simulation that can write files through textio. A page that got
// script injection must not reach any of that, so every request is checked here before a process starts.
//
// Everything is an ALLOWLIST: options, yosys commands, input file types and frontends. Anything unknown is
// refused, so a newer tool version or a forgotten command cannot open a hole. In addition:
//   - every value that names a file must be a safe relative path, so tools read and write only the run folder;
//   - yosys scripts are lexed strictly: quotes, backslashes, here-documents and "#" inside a token are refused,
//     so this lexer can never see different command boundaries than yosys itself;
//   - HDL sources may reference other files (`include, $readmem, $fopen, init_file parameters, VHDL file) only
//     through a plain relative string literal, never through a macro, a constant or file_open (hdlFileRefs.cjs
//     tokenizes the source first, so comments and macros cannot hide a reference);
//   - macro definitions on a yosys command line are plain words, so a macro cannot stand for a file task.
//
// The run folder is a fresh temporary directory, so relative paths cannot reach anything else.
'use strict';

const { isSafeRelativePath } = require('./pathRules.cjs');
const { PART_RE } = require('./openxc7.cjs');
const { checkVendorRequest, parseVendorArgs } = require('./vendorPolicy.cjs');
const { checkVerilog, checkVhdl, isPlainDefine } = require('./hdlFileRefs.cjs');

const deny = (message) => ({ ok: false, message });
const OK = { ok: true };

/** Looks like a file system path (a separator, a drive prefix or a home prefix) */
function isPathLike(token) {
  return /[\\/]/.test(token) || /^[A-Za-z]:/.test(token) || token.startsWith('~');
}

/** A plain value (part name, number, unit name) or a safe relative path; never a response file */
function checkPlainOrRelative(value, what) {
  if (typeof value !== 'string') return deny(`${what}: missing value`);
  if (value.startsWith('@')) return deny(`${what}: response files are not allowed`);
  if (value.split(/[\\/]/).includes('..')) return deny(`${what}: ".." is not allowed`);
  if (isPathLike(value) && !isSafeRelativePath(value)) return deny(`${what}: only relative paths inside the run folder are allowed`);
  return OK;
}

function checkRelativePath(value, what) {
  if (typeof value !== 'string' || !isSafeRelativePath(value)) return deny(`${what}: must be a relative path inside the run folder`);
  return OK;
}

// --- yosys ------------------------------------------------------------------------------------------

/**
 * Yosys commands a script may use: frontends, synthesis and optimisation passes, mapping, checks and writers.
 * Left out on purpose: everything that starts programs or loads code (exec, shell, tcl, script, plugin,
 * connect_rpc, bugpoint, show, viz, opensta, qbfsat, abc9_exe, verific, read_slang), that runs another command
 * given as its argument (tee, debug, trace, equiv_opt), that reads file lists (read_verilog_file_list, sdc, libcache),
 * that changes the environment (setenv), and the test_* commands.
 */
const YOSYS_COMMANDS = new Set([
  // frontends and design handling
  'read', 'read_verilog', 'read_rtlil', 'read_json', 'read_blif', 'read_liberty', 'read_aiger', 'verilog_defaults', 'verilog_defines',
  'hierarchy', 'design', 'blackbox', 'keep_hierarchy', 'uniquify', 'flatten', 'submod', 'chparam', 'setparam', 'setattr', 'setundef',
  'attrmap', 'attrmvcp', 'printattrs', 'rename', 'autoname', 'delete', 'copy', 'add', 'connect', 'expose', 'select', 'cd', 'ls',
  'portlist', 'rmports', 'splitnets', 'splitcells', 'chtype', 'wrapcell', 'scratchpad', 'echo', 'log', 'help', 'license',
  // generic synthesis and optimisation
  'synth', 'prep', 'proc', 'proc_clean', 'proc_rmdead', 'proc_prune', 'proc_init', 'proc_arst', 'proc_rom', 'proc_mux', 'proc_dlatch',
  'proc_dff', 'proc_memwr', 'opt', 'opt_expr', 'opt_clean', 'opt_merge', 'opt_muxtree', 'opt_reduce', 'opt_share', 'opt_dff',
  'opt_lut', 'opt_lut_ins', 'opt_mem', 'opt_mem_feedback', 'opt_mem_priority', 'opt_mem_widen', 'opt_demorgan', 'opt_ffinv',
  'opt_hier', 'opt_balance_tree', 'clean', 'check', 'check_mem', 'stat', 'wreduce', 'peepopt', 'share', 'alumacc', 'maccmap',
  'booth', 'pmuxtree', 'pmux2shiftx', 'muxpack', 'muxcover', 'bmuxmap', 'demuxmap', 'bwmuxmap', 'freduce', 'extract',
  'extract_fa', 'extract_reduce', 'extract_counter', 'extractinv', 'tribuf', 'deminout', 'async2sync', 'clk2fflogic', 'zinit',
  'dffinit', 'dfflegalize', 'dffunmap', 'dfflibmap', 'clkbufmap', 'iopadmap', 'insbuf', 'hilomap', 'constmap', 'lut2mux',
  'shregmap', 'onehot', 'torder', 'scc', 'sort', 'edgetypes', 'cutpoint', 'formalff', 'chformal', 'assertpmux', 'xprop',
  'fsm', 'fsm_detect', 'fsm_extract', 'fsm_opt', 'fsm_expand', 'fsm_recode', 'fsm_info', 'fsm_map',
  'memory', 'memory_dff', 'memory_collect', 'memory_share', 'memory_map', 'memory_bram', 'memory_libmap', 'memory_memx',
  'memory_narrow', 'memory_nordff', 'memory_unpack', 'memory_bmux2rom',
  'techmap', 'simplemap', 'aigmap', 'abc', 'abc9', 'abc_new', 'abc9_ops', 'eval', 'sat', 'miter', 'equiv_make', 'equiv_simple',
  'equiv_induct', 'equiv_status', 'equiv_purge', 'equiv_mark', 'equiv_struct', 'equiv_remove', 'equiv_add', 'equiv_miter',
  'timeest', 'sta', 'synthprop',
  // vendor flows
  'synth_ecp5', 'synth_ice40', 'synth_lattice', 'synth_nexus', 'synth_gowin', 'synth_xilinx', 'synth_intel', 'synth_intel_alm',
  'synth_gatemate', 'synth_anlogic', 'synth_efinix', 'synth_quicklogic', 'synth_microchip', 'synth_sf2', 'synth_achronix',
  'synth_easic', 'synth_nanoxplore', 'synth_fabulous', 'synth_analogdevices',
  // writers
  'write_verilog', 'write_json', 'write_rtlil', 'write_blif', 'write_edif', 'write_aiger', 'write_btor', 'write_smt2',
  'write_smv', 'write_spice', 'write_table', 'write_firrtl', 'write_cxxrtl', 'write_simplec', 'write_intersynth', 'write_file',
]);
// Options that make an allowed command start a program or run a script outside the run folder's rules
const YOSYS_DENIED_TOKENS = new Set(['-exe', '-viewer', '-yosys', '-script']);
const YOSYS_FLAGS = new Set(['-q', '--quiet', '-Q', '-T', '-V', '--version', '-S', '--synth', '-H', '-t', '--timestamp', '-d', '--detailed-timing', '-g', '--debug', '--no-color', '--no-version', '--git-hash']);
// option -> how its value is checked
const YOSYS_VALUE_OPTIONS = {
  '-p': 'script', '--commands': 'script',
  '-s': 'scriptfile', '--scriptfile': 'scriptfile',
  '-f': 'frontend', '--frontend': 'frontend',
  '-r': 'plain', '--top': 'plain', '-D': 'define', '--define': 'define', '-b': 'backend', '--backend': 'backend',
  '-v': 'plain', '--verbose': 'plain', '-W': 'plain', '--warning-as-warning': 'plain', '-w': 'plain',
  '--warning-as-message': 'plain', '-e': 'plain', '--warning-as-error': 'plain', '-x': 'plain', '--experimental': 'plain',
};
const YOSYS_FRONTENDS = new Set(['verilog', 'rtlil', 'ilang', 'json', 'blif', 'liberty', 'aiger']);
const YOSYS_BACKENDS = new Set(['verilog', 'rtlil', 'ilang', 'json', 'blif', 'edif', 'aiger', 'btor', 'smt2', 'smv', 'spice', 'table', 'firrtl']);
// Input files on the command line; yosys picks the frontend from the extension (and would unpack .gz first)
const YOSYS_INPUT_EXT = /\.(v|sv|vh|svh|il|rtlil|json|blif|lib|aig|ys)$/i;

/**
 * Splits a yosys script into commands (lists of tokens). Throws on any syntax whose meaning in yosys is not
 * plain whitespace / ";" / newline splitting: quotes, backslashes, here-documents, "#" not starting a token,
 * control characters. This lexer splits on every ";" and newline, so it sees at least every command start
 * that yosys sees.
 */
function yosysCommands(script) {
  // Control characters are matched on purpose: yosys may treat them as separators where this lexer would not.
  // oxlint-disable-next-line no-control-regex
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(script)) throw new Error('control characters are not allowed');
  if (/["\\`]/.test(script)) throw new Error('quotes and backslashes are not allowed');
  const commands = [];
  for (const line of script.split(/\r?\n|\r/)) {
    let tokens = [];
    for (const raw of line.split(/[ \t]+/)) {
      if (raw === '') continue;
      if (raw.startsWith('#')) break; // comment to the end of the line, as in yosys
      if (raw.includes('#')) throw new Error(`"#" inside "${raw}" is not allowed`);
      if (raw.startsWith('<<')) throw new Error('here-documents are not allowed');
      const parts = raw.split(';');
      parts.forEach((part, i) => {
        if (part !== '') tokens.push(part);
        if (i < parts.length - 1 && tokens.length) {
          commands.push(tokens);
          tokens = [];
        }
      });
    }
    if (tokens.length) commands.push(tokens);
  }
  return commands;
}

/** A token that names a file outside the run folder (absolute, drive, home, "..") */
function leavesRunFolder(token) {
  // Yosys's own data folder ("+/ecp5/cells_sim.v") is fine as long as it does not climb out.
  const t = token.startsWith('+/') ? token.slice(2) : token;
  if (t.split(/[\\/]/).includes('..')) return true;
  // Absolute forms, also after "=" or "," as in -DNAME=/x or -map a,/b
  if (/(^|[=,:])\//.test(t) || /(^|[=,])~/.test(t)) return true;
  // "X:..." is a drive path on Windows ("D:secret.v" is relative to D:'s current folder). Yosys selections use the
  // same shape ("w:clk", "t:$dff", "c:*"), so those are allowed when the letter is a selection prefix and the rest
  // is a plain name or pattern without dots or separators.
  for (const m of t.matchAll(/(?:^|[=,])([A-Za-z]):([^=,]*)/g)) {
    if (!/^[wioxsmnartpc]$/.test(m[1]) || !/^[\w$*%]+$/.test(m[2])) return true;
  }
  return false;
}

// Commands that take read_verilog's -D NAME=VALUE: a macro there could expand to $readmemh or a path
const YOSYS_DEFINE_COMMANDS = new Set(['read_verilog', 'read', 'verilog_defines', 'verilog_defaults']);

function checkYosysScript(script, where) {
  if (typeof script !== 'string') return deny(`${where}: not text`);
  let commands;
  try {
    commands = yosysCommands(script);
  } catch (err) {
    return deny(`${where}: ${err.message}`);
  }
  for (const tokens of commands) {
    const name = tokens[0];
    if (!YOSYS_COMMANDS.has(name)) return deny(`${where}: the yosys command "${name}" is not allowed`);
    if (YOSYS_DEFINE_COMMANDS.has(name)) {
      for (let i = 1; i < tokens.length; i++) {
        const value = tokens[i] === '-D' ? tokens[++i] : tokens[i].startsWith('-D') ? tokens[i].slice(2) : null;
        if (value !== null && !isPlainDefine(value)) return deny(`${where}: "${name} -D ${value ?? ''}": a macro may only be NAME or NAME=word`);
      }
    }
    for (const token of tokens) {
      if (YOSYS_DENIED_TOKENS.has(token)) return deny(`${where}: "${name} ${token}" is not allowed`);
      if (leavesRunFolder(token)) return deny(`${where}: "${token}" names a file outside the run folder`);
    }
  }
  return OK;
}

function checkYosys(args, files) {
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (YOSYS_FLAGS.has(arg)) continue;
    const kind = YOSYS_VALUE_OPTIONS[arg];
    if (kind) {
      const value = args[++i];
      if (value === undefined) return deny(`${arg} needs a value`);
      let r = OK;
      if (kind === 'script') r = checkYosysScript(value, arg);
      else if (kind === 'scriptfile') {
        if (!isSafeRelativePath(value) || !/\.ys$/i.test(value)) return deny(`${arg}: must name a .ys file in the run folder`);
        r = checkYosysScript(fileText(files, value), value);
      } else if (kind === 'frontend') r = YOSYS_FRONTENDS.has(value) ? OK : deny(`${arg} ${value} is not allowed`);
      else if (kind === 'backend') r = YOSYS_BACKENDS.has(value) ? OK : deny(`${arg} ${value} is not allowed`);
      else if (kind === 'define') r = isPlainDefine(value) ? OK : deny(`${arg} ${value}: a macro may only be NAME or NAME=word`);
      else r = checkPlainOrRelative(value, arg);
      if (!r.ok) return r;
      continue;
    }
    if (arg.startsWith('-')) return deny(`yosys option ${arg} is not allowed`);
    if (!isSafeRelativePath(arg)) return deny(`input file ${arg}: only relative paths inside the run folder are allowed`);
    if (!YOSYS_INPUT_EXT.test(arg)) return deny(`input file ${arg}: this file type is not allowed`);
    if (/\.ys$/i.test(arg)) {
      const r = checkYosysScript(fileText(files, arg), arg);
      if (!r.ok) return r;
    }
  }
  return OK;
}

// --- ghdl -------------------------------------------------------------------------------------------

// Commands that only analyse, elaborate (mcode: checks only) or synthesize. Running a design (-r, -c, --elab-run)
// is refused because a simulation can write files through textio and load VPI libraries.
const GHDL_COMMANDS = new Set(['-a', '--synth', '-s', '-e', '-i', '--version', '-v', '--help', '-h', '--dir', '--disp-standard']);
// Option prefixes allowed after the command (values without a path)
const GHDL_OPTION_PREFIXES = ['--std=', '--ieee=', '--work=', '--out=', '-f', '-W', '--warn-', '-g', '--no-', '--latches', '-C', '--mb-comments', '--max-', '--top=', '--expect-failure', '--keep-hierarchy', '--vendor-library=', '-O', '--syn-binding', '--format=', '-v', '--assert-'];
// Option prefixes whose value is a path
const GHDL_PATH_PREFIXES = ['--workdir=', '-P'];

function checkGhdl(args) {
  if (args.length === 0) return OK;
  if (!GHDL_COMMANDS.has(args[0])) return deny(`ghdl command ${args[0]} is not allowed`);
  for (const arg of args.slice(1)) {
    if (arg.startsWith('@')) return deny('response files are not allowed');
    const pathPrefix = GHDL_PATH_PREFIXES.find((p) => arg.startsWith(p));
    if (pathPrefix) {
      const r = checkRelativePath(arg.slice(pathPrefix.length), pathPrefix);
      if (!r.ok) return r;
      continue;
    }
    if (arg === '-e') continue; // "--synth files -e top"
    if (arg.startsWith('-')) {
      if (!GHDL_OPTION_PREFIXES.some((p) => arg.startsWith(p))) return deny(`ghdl option ${arg} is not allowed`);
      if (/[\\/:]/.test(arg)) return deny(`ghdl option ${arg}: paths are not allowed here`);
      continue;
    }
    // A source file or a design unit name
    const r = checkPlainOrRelative(arg, 'argument');
    if (!r.ok) return r;
  }
  return OK;
}

// --- boost::program_options tools (nextpnr-ecp5, ecppack) --------------------------------------------

/**
 * Checks a command line against an allowlist of exact option names:
 *   flags: options without a value; plain: values that are words or numbers; paths: values that are files;
 *   checked: option name -> a checker for its value (nextpnr-xilinx -o / --vopt).
 * Positional arguments must be safe relative paths. Abbreviated option names are refused because they are not
 * in the list. The walk consumes values exactly as boost::program_options does, and a value may never start
 * with "-": a check that pairs options and values differently from the tool could otherwise let a refused option
 * through as some other option's value (6j-6 security review).
 */
function checkOptionLine(tool, args, { flags, plain, paths, positional, checked = {} }) {
  for (let i = 0; i < args.length; i++) {
    let arg = args[i];
    let inline;
    const eq = arg.startsWith('--') ? arg.indexOf('=') : -1;
    if (eq > 0) {
      inline = arg.slice(eq + 1);
      arg = arg.slice(0, eq);
    }
    if (flags.has(arg)) {
      if (inline !== undefined) return deny(`${tool} option ${arg} takes no value`);
      continue;
    }
    const isChecked = Object.prototype.hasOwnProperty.call(checked, arg);
    if (plain.has(arg) || paths.has(arg) || isChecked) {
      const value = inline ?? args[++i];
      if (typeof value === 'string' && value.startsWith('-')) return deny(`${arg}: a value may not start with "-"`);
      if (isChecked) {
        const c = checked[arg](value);
        if (!c.ok) return c;
        continue;
      }
      const r = paths.has(arg) ? checkRelativePath(value, arg) : checkPlainOrRelative(value, arg);
      if (!r.ok) return r;
      if (plain.has(arg) && isPathLike(value)) return deny(`${arg}: expects a plain value`);
      continue;
    }
    if (arg.startsWith('-') || arg.startsWith('@')) return deny(`${tool} option ${arg} is not allowed`);
    if (!positional) return deny(`${tool} takes no positional arguments`);
    const r = checkRelativePath(arg, 'argument');
    if (!r.ok) return r;
  }
  return OK;
}

// Python hooks (--run, --pre-*, --post-route, --on-failure), the GUI and --test are not in these lists.
const NEXTPNR_ECP5 = {
  flags: new Set(['-h', '--help', '-v', '--verbose', '-q', '--quiet', '--debug', '--debug-placer', '--debug-router', '-f', '--force',
    '-r', '--randomize-seed', '--pack-only', '--no-route', '--no-place', '--no-pack', '--ignore-loops', '--ignore-rel-clk', '-V',
    '--version', '--timing-allow-fail', '--no-tmdriv', '--sdf-cvc', '--no-print-critical-path-source', '--placer-heap-no-ctrl-set',
    '--parallel-refine', '--tmg-ripup', '--router2-tmg-ripup', '--router2-alt-weights', '--detailed-timing-report', '--12k', '--25k',
    '--45k', '--85k', '--um-25k', '--um-45k', '--um-85k', '--um5g-25k', '--um5g-45k', '--um5g-85k', '--lpf-allow-unconstrained',
    '--no-promote-globals', '--out-of-context', '--disable-router-lutperm', '--allow-fabric-eclk']),
  plain: new Set(['--threads', '--top', '--seed', '--placer', '--router', '--cstrweight', '--starttemp', '--freq', '--placer-heap-alpha',
    '--placer-heap-beta', '--placer-heap-critexp', '--placer-heap-timingweight', '--placer-heap-cell-placement-timeout', '--package', '--speed']),
  paths: new Set(['-l', '--log', '--json', '--write', '--sdc', '--sdf', '--report', '--placed-svg', '--routed-svg', '--basecfg',
    '--override-basecfg', '--textcfg', '--lpf', '--router2-heatmap']),
  positional: false,
};

// --db (an outside chip database folder) is not in these lists.
const ECPPACK = {
  flags: new Set(['-h', '--help', '-v', '--verbose', '--compress', '--background', '--version']),
  plain: new Set(['--usercode', '--idcode', '--freq', '--svf-rowsize', '--spimode', '--bootaddr']),
  paths: new Set(['--svf', '--delta', '--input', '--bit']),
  positional: true,
};

// --- openXC7 (nextpnr-xilinx, fasm2frames, xc7frames2bit) ------------------------------------------

// As nextpnr-ecp5, plus --device (checked against PART_RE). Left out: --chipdb (a database outside the run folder), --test, --list-uarch and
// the Python hooks. -o / --vopt is checked on its own (checkNextpnrXilinx).
const NEXTPNR_XILINX = {
  flags: new Set(['-h', '--help', '-v', '--verbose', '-q', '--quiet', '--Werror', '--debug', '--debug-placer', '--debug-router', '-f',
    '--force', '-r', '--randomize-seed', '--pack-only', '--no-route', '--no-place', '--no-pack', '--ignore-loops', '--ignore-rel-clk',
    '-V', '--version', '--timing-allow-fail', '--no-tmdriv', '--sdf-cvc', '--no-print-critical-path-source', '--placer-heap-no-ctrl-set',
    '--parallel-refine', '--tmg-ripup', '--router2-tmg-ripup', '--router2-alt-weights', '--detailed-timing-report']),
  plain: new Set(['--threads', '--top', '--seed', '--placer', '--router', '--cstrweight', '--starttemp', '--freq',
    '--placer-heap-alpha', '--placer-heap-beta', '--placer-heap-critexp', '--placer-heap-timingweight', '--placer-heap-cell-placement-timeout']),
  paths: new Set(['-l', '--log', '--json', '--write', '--sdc', '--sdf', '--report', '--placed-svg', '--routed-svg']),
  positional: false,
};
/**
 * nextpnr-xilinx's -o / --vopt values that are allowed: the constraints it reads and the FASM it writes, both in
 * the run folder. Refused: placement / preplaced / prerouted / holdbufs (more files), delay-matrix (a cache path),
 * and the tuning options (not needed by the app).
 */
const XILINX_VOPTS = new Set(['fasm', 'xdc']);

function checkXilinxVopt(value) {
  const m = typeof value === 'string' ? /^([a-z-]+)=(.*)$/.exec(value) : null;
  if (!m || !XILINX_VOPTS.has(m[1])) return deny(`nextpnr-xilinx -o ${value ?? ''}: only fasm= and xdc= are allowed`);
  return checkRelativePath(m[2], `-o ${m[1]}`);
}

const checkXilinxDevice = (value) => (typeof value === 'string' && PART_RE.test(value) ? OK : deny('--device: expects a 7-series part name'));

// -o / --vopt / --device go through the same walk as every other option, so values pair up as boost pairs them
const checkNextpnrXilinx = (args) =>
  checkOptionLine('nextpnr-xilinx', args, { ...NEXTPNR_XILINX, checked: { '-o': checkXilinxVopt, '--vopt': checkXilinxVopt, '--device': checkXilinxDevice } });

/**
 * Exact command lines of the two bitstream tools. The main process adds the database paths (openxc7.cjs), so the
 * page may not name them: fasm2frames is an argparse program (it would take --db-root, abbreviations like --db,
 * --roi with a file), xc7frames2bit a gflags program (it would take -part_file, -flagfile, -fromenv ...). Each
 * accepts one exact option spelling plus file names, nothing else.
 */
function checkExactLine(tool, args, valueOptions, positional) {
  const seen = new Set();
  const files = [];
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (Object.prototype.hasOwnProperty.call(valueOptions, arg)) {
      if (seen.has(arg)) return deny(`${tool}: ${arg} given twice`);
      seen.add(arg);
      const value = args[++i];
      const kind = valueOptions[arg];
      if (kind === 'part') {
        if (typeof value !== 'string' || !PART_RE.test(value)) return deny(`${tool} ${arg}: expects a 7-series part name`);
      } else {
        const r = checkRelativePath(value, arg);
        if (!r.ok) return r;
        if (!kind.test(value)) return deny(`${tool} ${arg}: this file type is not allowed`);
      }
      continue;
    }
    if (arg.startsWith('-') || arg.startsWith('@')) return deny(`${tool} option ${arg} is not allowed`);
    files.push(arg);
  }
  for (const name of Object.keys(valueOptions)) if (!seen.has(name)) return deny(`${tool}: ${name} is required`);
  if (files.length !== positional.length) return deny(`${tool}: expects ${positional.length} file names`);
  for (let i = 0; i < files.length; i++) {
    const r = checkRelativePath(files[i], 'argument');
    if (!r.ok) return r;
    if (!positional[i].test(files[i])) return deny(`${tool} ${files[i]}: this file type is not allowed`);
  }
  return OK;
}

const checkFasm2frames = (args) => checkExactLine('fasm2frames', args, { '--part': 'part' }, [/\.fasm$/i, /\.frames$/i]);
const checkXc7frames2bit = (args) =>
  checkExactLine('xc7frames2bit', args, { '--part_name': 'part', '--frm_file': /\.frames$/i, '--output_file': /\.bit$/i }, []);

// --- openFPGALoader ---------------------------------------------------------------------------------

/**
 * openFPGALoader writes a bitstream to a board. Allowed: choosing the cable or board, SRAM or flash, detecting the
 * chain, listing, and one bitstream that the page sent as an input file. Refused because they write files, touch
 * flash beyond a plain write, reach the network or load other code: --dump-flash (writes a file), --bulk-erase,
 * --protect-flash / --unprotect-flash, -o / --offset, --flash-sector, --target-flash, --external-flash,
 * --enable-quad / --disable-quad, --file-type, --ip / --port (remote cables), -d / --device (a device path),
 * --pins, --probe-firmware, --mcufw, --user-flash, --secondary-bitstream, --misc-device, -B / --bridge,
 * --skip-load-bridge, --spi, --dfu and the rest. A flash write additionally needs the user's yes in the main process
 * (confirmationFor below). That decision must not depend on anything but -f, so:
 *   - only .bit files are accepted: an .svf file is a raw JTAG script that can erase and write the flash by itself;
 *   - a run with a bitstream must say -m (SRAM) or -f (flash) explicitly: some boards write flash by default;
 *   - -b names only boards listed in LOADER_BOARDS (mirrors src/fpga/flow/program.ts), for the same reason;
 *   - -c names only cables listed in LOADER_CABLES: some cable types (xvc-client, remote-bitbang) open a network
 *     connection instead of using USB.
 */
const OPENFPGALOADER = {
  flags: new Set(['-h', '--help', '-V', '--version', '--Version', '-v', '--verbose', '--quiet', '-f', '--write-flash', '-m',
    '--write-sram', '--detect', '--verify', '-r', '--reset', '--skip-reset', '--list-boards', '--list-cables', '--list-fpga',
    '--scan-usb', '--invert-read-edge']),
  plain: new Set(['-b', '--board', '-c', '--cable', '--freq', '--cable-index', '--ftdi-channel', '--index-chain', '--fpga-part',
    '--vid', '--pid', '--usb-serial-num', '--verbose-level']),
  paths: new Set(['--bitstream']),
  positional: true,
};
const OPENFPGALOADER_FLASH = new Set(['-f', '--write-flash']);
// Board, cable and part names ("ecp5_evn", "ft2232", "LFE5U-85F-6BG381C"), numbers ("6000000", "0x0403") and serials
const LOADER_VALUE = /^[A-Za-z0-9][A-Za-z0-9_.+-]{0,63}$/;
const BITSTREAM_EXT = /\.bit$/i;
const OPENFPGALOADER_SRAM = new Set(['-m', '--write-sram']);
// openFPGALoader board names the app may pass with -b / --board (mirrors PROGRAMMER_ARGS in src/fpga/flow/program.ts;
// GECKO5 uses the default cable)
const LOADER_BOARDS = new Set(['basys3', 'nexys_a7_100', 'alchitry_au', 'pynq_z2']);
// openFPGALoader cable names the app may pass with -c / --cable: USB cables only (the Zybo's Digilent FT2232)
const LOADER_CABLES = new Set(['digilent']);

/** The bitstream files of an openFPGALoader command line (positional or --bitstream) */
function loaderBitstreams(args) {
  const found = [];
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--bitstream') found.push(args[++i]);
    else if (arg.startsWith('--bitstream=')) found.push(arg.slice('--bitstream='.length));
    else if (OPENFPGALOADER.plain.has(arg)) i++;
    else if (!arg.startsWith('-')) found.push(arg);
  }
  return found;
}

function checkOpenFpgaLoader(args, files) {
  const r = checkOptionLine('openFPGALoader', args, OPENFPGALOADER);
  if (!r.ok) return r;
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const eq = arg.startsWith('--') ? arg.indexOf('=') : -1;
    const name = eq > 0 ? arg.slice(0, eq) : arg;
    if (!OPENFPGALOADER.plain.has(name)) continue;
    const value = eq > 0 ? arg.slice(eq + 1) : args[++i];
    if (!LOADER_VALUE.test(value)) return deny(`${name}: expects a plain name or number`);
    if ((name === '-b' || name === '--board') && !LOADER_BOARDS.has(value)) return deny(`${name} ${value}: this board is not allowed`);
    if ((name === '-c' || name === '--cable') && !LOADER_CABLES.has(value)) return deny(`${name} ${value}: this cable is not allowed`);
  }
  const bitstreams = loaderBitstreams(args);
  if (bitstreams.length > 1) return deny('openFPGALoader takes one bitstream');
  for (const b of bitstreams) {
    if (!BITSTREAM_EXT.test(b)) return deny(`bitstream ${b}: this file type is not allowed`);
    // Only a file the page sent: the tool reads nothing else from the run folder
    if (!files || !Object.prototype.hasOwnProperty.call(files, b)) return deny(`bitstream ${b}: not one of the input files`);
  }
  const flash = args.some((a) => OPENFPGALOADER_FLASH.has(a));
  const sram = args.some((a) => OPENFPGALOADER_SRAM.has(a));
  if (flash && sram) return deny('choose either -m (SRAM) or -f (flash)');
  if (bitstreams.length > 0 && !flash && !sram) return deny('a bitstream needs -m (SRAM) or -f (flash) explicitly');
  if (flash && bitstreams.length === 0 && !args.includes('--detect')) return deny('a flash write needs a bitstream');
  return OK;
}

/**
 * A run that needs the user's explicit yes in the main process before it starts, or null. A flash write survives a
 * power cycle and replaces what was on the board, so a page (even one with injected script) must not do it alone.
 * "--detect -f" only lists the flash and is not a write.
 */
function confirmationFor(tool, args) {
  // quartus_pgm writing a .pof: a CPLD's own non-volatile memory (it keeps the design and replaces the old one)
  if (tool === 'quartus') {
    const parsed = parseVendorArgs('quartus', args);
    if (parsed.ok && parsed.request.step === 'program' && /\.pof$/i.test(parsed.request.bitstream)) return { kind: 'cpldWrite', file: parsed.request.bitstream };
    return null;
  }
  // iMPACT writing a .jed: a CoolRunner / XC9500 CPLD's own memory, the same way
  if (tool === 'ise') {
    const parsed = parseVendorArgs('ise', args);
    if (parsed.ok && parsed.request.step === 'program' && /\.jed$/i.test(parsed.request.bitstream)) return { kind: 'cpldWrite', file: parsed.request.bitstream };
    return null;
  }
  if (tool !== 'openfpgaloader' || !Array.isArray(args)) return null;
  if (!args.some((a) => OPENFPGALOADER_FLASH.has(a))) return null;
  const bitstreams = loaderBitstreams(args);
  if (bitstreams.length === 0) return null;
  return { kind: 'flashWrite', file: bitstreams[0] };
}

// --- input files ------------------------------------------------------------------------------------

function fileText(files, name) {
  const data = files && Object.prototype.hasOwnProperty.call(files, name) ? files[name] : undefined;
  if (typeof data === 'string') return data;
  if (data instanceof Uint8Array) return Buffer.from(data).toString('utf8');
  return '';
}

const VERILOG_EXT = /\.(v|sv|vh|svh)$/i;
const VHDL_EXT = /\.(vhd|vhdl)$/i;

/**
 * HDL sources may read other files only through a plain relative string literal: `include "x.vh",
 * $readmemh("rom.hex", ...), (* ram_init_file = "rom.mif" *), VHDL `file f : text open read_mode is "rom.txt";`.
 * A macro, a constant, a concatenation or VHDL file_open could name any file on the computer, so they are refused
 * (hdlFileRefs.cjs).
 */
function checkInputFiles(files) {
  for (const [name, data] of Object.entries(files || {})) {
    const verilog = VERILOG_EXT.test(name);
    const vhdl = VHDL_EXT.test(name);
    if (!verilog && !vhdl) continue;
    const text = typeof data === 'string' ? data : Buffer.from(data).toString('utf8');
    const r = verilog ? checkVerilog(name, text) : checkVhdl(name, text);
    if (!r.ok) return r;
  }
  return OK;
}

const CHECKERS = {
  yosys: checkYosys,
  ghdl: checkGhdl,
  'nextpnr-ecp5': (args) => checkOptionLine('nextpnr-ecp5', args, NEXTPNR_ECP5),
  ecppack: (args) => checkOptionLine('ecppack', args, ECPPACK),
  'nextpnr-xilinx': checkNextpnrXilinx,
  fasm2frames: checkFasm2frames,
  xc7frames2bit: checkXc7frames2bit,
  openfpgaloader: checkOpenFpgaLoader,
  // Vendor tools (6k-1): an option line the main process turns into a fixed script (vendorPolicy.cjs, vendorScripts.cjs)
  vivado: (args, files) => checkVendorRequest('vivado', args, files),
  quartus: (args, files) => checkVendorRequest('quartus', args, files),
  ise: (args, files) => checkVendorRequest('ise', args, files),
};

/** { ok: true } or { ok: false, message } for a validated-shape request (tool known, args strings) */
function checkToolRequest(tool, args, files) {
  const checker = Object.prototype.hasOwnProperty.call(CHECKERS, tool) ? CHECKERS[tool] : null;
  if (!checker) return deny('No argument policy for this tool');
  const r = checker(args, files);
  if (!r.ok) return r;
  return checkInputFiles(files);
}

module.exports = { checkToolRequest, confirmationFor, yosysCommands, checkYosysScript };
