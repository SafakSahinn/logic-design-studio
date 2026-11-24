// Request policy for the vendor FPGA tools (Aşama 6k-1): Vivado, Quartus and ISE.
//
// All three tools run Tcl or read Tcl-like files, so the page never sends a script or a command line. It sends a
// short option line that names a step, a part, a top-level name and files:
//
//   vivado  --step build    --part xc7a35tcpg236-1 --top top --source top.v ... --constraints top.xdc
//   vivado  --step program  --part xc7a35tcpg236-1 --bitstream design.bit   (the only file sent: a .bit)
//   quartus --step compile  --part EP4CE22F17C6    --top top --source top.v ... --constraints top.qsf
//   quartus --step program  --part EP4CE22F17C6    --bitstream design.sof  (or a CPLD's design.pof; the only file)
//   ise     --step xst      --part xc6slx9-2-tqg144 --top top --source top.v ...
//   ise     --step ngdbuild --part ... --top top --constraints top.ucf      (reads top.ngc)
//   ise     --step map      --part ... --top top                            (reads top.ngd)
//   ise     --step par      --top top                                       (reads top_map.ncd, top.pcf)
//   ise     --step bitgen   --top top                                       (reads top.ncd, top.pcf)
//
// The main process turns that line into the real script and command line from fixed templates (vendorScripts.cjs).
// Every value that ends up inside a script is checked here against a character set with no Tcl, cmd or shell
// meaning (no spaces, quotes, braces, brackets, "$", ";", "\\", "%"), so no value can change a template's
// commands. The input files are an allowlist of types per tool; the constraint files, which the tools read as Tcl
// (.xdc, .qsf) or as their own language (.ucf), must consist only of the lines LogicDesign Studio writes
// (src/fpga/hdl/constraints.ts), each matched against an exact grammar.
'use strict';

const deny = (message) => ({ ok: false, message });
const OK = { ok: true };

/** Top-level module / entity / project name */
const IDENT_RE = /^[A-Za-z][A-Za-z0-9_]{0,63}$/;
/** A file of the run folder: one plain name, no folders */
const FILE_RE = /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}$/;
/** 7-series part with package and speed grade (the same rule as openxc7.cjs PART_RE) */
const VIVADO_PART_RE = /^xc7[aksz]\d{1,3}t?s?[a-z]{2,5}\d{3,4}-[1-3]L?$/;
/**
 * Altera / Intel device names: EP1C12Q240C8, EP4CE22F17C6, 5CSEMA5F31C6, 10CL016YF484C8G, 10M08SAU169C8G,
 * 5M570ZF256C5, EPM7128SLC84-7 ... Letters, digits and one optional "-speed" suffix.
 */
const QUARTUS_PART_RE = /^(?:EP[0-9A-Z]{4,20}|EPM[0-9A-Z]{4,20}(?:-[0-9]{1,2})?|5[A-Z][0-9A-Z]{4,20}|10[A-Z][0-9A-Z]{4,20})$/;
/** ISE device-speed-package: xc6slx9-2-tqg144, xc3s100e-4-cp132, xc3s5000-5-fg676, xc2c64a-5-vq44 */
const ISE_PART_RE = /^xc(?:3s[0-9]{2,4}(?:e|a|an|adsp)?|6slx[0-9]{1,3}t?|2c[0-9]{2,3}a?|95[0-9]{2,3}(?:xl|xv)?)-[1-5]l?-[a-z]{2,4}[0-9]{2,4}$/i;

const HDL_EXT = /\.(v|sv|vhd|vhdl)$/i;
/**
 * Per tool and step what the option line must hold. bitstream: the step loads that file onto a board and gets no
 * other file (vivado program: SRAM over JTAG through Vivado's own hw_server, see vendorScripts.vivadoProgram;
 * quartus program: quartus_pgm on the first JTAG cable, see vendorScripts.quartusProgram).
 */
const STEPS = {
  vivado: {
    build: { part: true, top: true, sources: true, constraints: /\.xdc$/i },
    program: { part: true, bitstream: /\.bit$/i },
  },
  quartus: {
    compile: { part: true, top: true, sources: true, constraints: /\.qsf$/i },
    program: { part: true, bitstream: /\.(sof|pof)$/i },
  },
  ise: {
    xst: { part: true, top: true, sources: true },
    ngdbuild: { part: true, top: true, constraints: /\.ucf$/i, reads: (top) => [`${top}.ngc`] },
    map: { part: true, top: true, reads: (top) => [`${top}.ngd`] },
    par: { top: true, reads: (top) => [`${top}_map.ncd`, `${top}.pcf`] },
    bitgen: { top: true, reads: (top) => [`${top}.ncd`, `${top}.pcf`] },
  },
};
const PART_RULE = { vivado: VIVADO_PART_RE, quartus: QUARTUS_PART_RE, ise: ISE_PART_RE };
/** Input file types per tool (the ISE intermediate netlists are the outputs of earlier steps) */
const INPUT_EXT = {
  vivado: /\.(v|sv|vh|svh|vhd|vhdl|xdc|hex|mem|txt)$/i,
  quartus: /\.(v|sv|vh|svh|vhd|vhdl|qsf|hex|mem|txt|mif)$/i,
  ise: /\.(v|vh|vhd|vhdl|ucf|hex|mem|txt|ngc|ngd|ncd|pcf)$/i,
};

const isVendorTool = (tool) => Object.prototype.hasOwnProperty.call(STEPS, tool);

/**
 * Parses a vendor option line into { step, part, top, sources, constraints } or a denial. Every option at most once
 * except --source; nothing positional; no value may start with "-".
 */
function parseVendorArgs(tool, args) {
  if (!isVendorTool(tool)) return deny('Not a vendor tool');
  if (!Array.isArray(args)) return deny(`${tool}: bad arguments`);
  const out = { step: null, part: null, top: null, sources: [], constraints: null, bitstream: null };
  const single = { '--step': 'step', '--part': 'part', '--top': 'top', '--constraints': 'constraints', '--bitstream': 'bitstream' };
  for (let i = 0; i < args.length; i++) {
    const opt = args[i];
    const value = args[i + 1];
    if (opt !== '--source' && !Object.prototype.hasOwnProperty.call(single, opt)) return deny(`${tool} option ${opt} is not allowed`);
    if (typeof value !== 'string' || value === '' || value.startsWith('-')) return deny(`${tool} ${opt}: missing value`);
    i++;
    if (opt === '--source') {
      out.sources.push(value);
      continue;
    }
    const key = single[opt];
    if (out[key] !== null) return deny(`${tool}: ${opt} given twice`);
    out[key] = value;
  }
  const spec = out.step && Object.prototype.hasOwnProperty.call(STEPS[tool], out.step) ? STEPS[tool][out.step] : null;
  if (!spec) return deny(`${tool}: unknown or missing --step`);
  if (spec.part ? !out.part || !PART_RULE[tool].test(out.part) : out.part !== null) {
    return deny(spec.part ? `${tool} --part: expects a ${tool} part name` : `${tool} ${out.step}: --part is not used`);
  }
  if (spec.top ? !out.top || !IDENT_RE.test(out.top) : out.top !== null) return deny(`${tool} --top: expects a plain name`);
  if (spec.sources) {
    if (out.sources.length === 0 || out.sources.length > 256) return deny(`${tool}: expects 1 to 256 --source files`);
    if (new Set(out.sources).size !== out.sources.length) return deny(`${tool}: a --source file is given twice`);
    for (const s of out.sources) if (!FILE_RE.test(s) || !HDL_EXT.test(s)) return deny(`${tool} --source ${s}: expects a Verilog or VHDL file name`);
  } else if (out.sources.length) return deny(`${tool} ${out.step}: --source is not used`);
  if (spec.constraints) {
    if (!out.constraints || !FILE_RE.test(out.constraints) || !spec.constraints.test(out.constraints)) return deny(`${tool} --constraints: expects a constraint file name`);
  } else if (out.constraints !== null) return deny(`${tool} ${out.step}: --constraints is not used`);
  if (spec.bitstream) {
    if (!out.bitstream || !FILE_RE.test(out.bitstream) || !spec.bitstream.test(out.bitstream)) return deny(`${tool} --bitstream: expects a bitstream file name`);
  } else if (out.bitstream !== null) return deny(`${tool} ${out.step}: --bitstream is not used`);
  // Quartus reads the settings of revision <top> from <top>.qsf
  if (tool === 'quartus' && spec.constraints && out.constraints !== `${out.top}.qsf`) return deny('quartus --constraints: must be <top>.qsf');
  out.reads = spec.reads ? spec.reads(out.top) : [];
  return { ok: true, request: out };
}

// --- constraint file grammars ---------------------------------------------------------------------------------

/** A comment line: any printable text, but no backslash (a Tcl comment ending in "\" swallows the next line) */
function isComment(line) {
  if (!line.startsWith('#') || line.includes('\\')) return false;
  for (let i = 0; i < line.length; i++) {
    const c = line.charCodeAt(i);
    if ((c < 32 && c !== 9) || c === 127) return false;
  }
  return true;
}
const PORT_RE = '[A-Za-z_][A-Za-z0-9_]*';
const NUM_RE = '[0-9]{1,6}(?:\\.[0-9]{1,6})?';

const XDC_PORT = `\\[get_ports \\{${PORT_RE}(?:\\[[0-9]{1,5}\\])?\\}\\]`;
const XDC_LINES = [
  new RegExp(`^set_property (?:PACKAGE_PIN [A-Za-z0-9]{1,8}|IOSTANDARD [A-Z0-9_]{2,24}|PULLUP TRUE|PULLDOWN TRUE|DRIVE [0-9]{1,2}) ${XDC_PORT}$`),
  new RegExp(`^create_clock -add -name ${PORT_RE} -period ${NUM_RE} -waveform \\{${NUM_RE} ${NUM_RE}\\} ${XDC_PORT}$`),
];

const QSF_GLOBAL_NAMES = new Set([
  'FAMILY', 'DEVICE', 'DEVICE_FILTER_PACKAGE', 'DEVICE_FILTER_PIN_COUNT', 'TOP_LEVEL_ENTITY', 'RESERVE_ALL_UNUSED_PINS',
  'FMAX_REQUIREMENT', 'RESERVE_NCEO_AFTER_CONFIGURATION', 'CYCLONEII_RESERVE_NCEO_AFTER_CONFIGURATION', 'VERILOG_FILE', 'VHDL_FILE',
]);
const QSF_VALUE = '(?:[A-Za-z0-9_.-]{1,64}|"[A-Za-z0-9 ._-]{1,64}")';
const QSF_PORT = `${PORT_RE}(?:\\[[0-9]{1,5}\\])?`;
const QSF_GLOBAL = new RegExp(`^set_global_assignment -name ([A-Z0-9_]{1,64}) (${QSF_VALUE})$`);
const QSF_LINES = [
  new RegExp(`^set_location_assignment [A-Za-z0-9_]{1,12} -to ${QSF_PORT}$`),
  new RegExp(`^set_instance_assignment -name (?:IO_STANDARD|WEAK_PULL_UP_RESISTOR|CURRENT_STRENGTH_NEW) ${QSF_VALUE} -to ${QSF_PORT}$`),
];

const UCF_PORT = `"${PORT_RE}(?:<[0-9]{1,5}>)?"`;
const UCF_LINES = [
  new RegExp(`^NET ${UCF_PORT} LOC = "[A-Za-z0-9]{1,8}"(?: \\| (?:PULLUP|PULLDOWN|DRIVE = [0-9]{1,2}|IOSTANDARD = [A-Z0-9_]{2,24}))* ;$`),
  new RegExp(`^NET "(${PORT_RE})" TNM_NET = "(${PORT_RE})" ;$`),
  new RegExp(`^TIMESPEC "TS_${PORT_RE}" = PERIOD "${PORT_RE}" ${NUM_RE}(?: (?:MHz|kHz|Hz))? HIGH 50 % ;$`),
];

const unquote = (v) => (v.startsWith('"') ? v.slice(1, -1) : v);

/** Lines of a text file, or null when it is not plain UTF-8 text */
function textLines(data) {
  const text = typeof data === 'string' ? data : Buffer.from(data).toString('utf8');
  if (text.includes('\0') || text.includes('�')) return null;
  return text.split(/\r?\n/);
}

/**
 * Checks a constraint file line by line. For .qsf it also checks that DEVICE and TOP_LEVEL_ENTITY match the request
 * and that every source the file lists is one of the request's sources.
 */
function checkConstraintFile(tool, name, data, request) {
  const lines = textLines(data);
  if (!lines) return deny(`${name}: not a text file`);
  let device = null;
  let topLevel = null;
  for (let n = 0; n < lines.length; n++) {
    const line = lines[n].trim();
    if (line === '' || isComment(line)) continue;
    const where = `${name} line ${n + 1}`;
    if (tool === 'vivado') {
      if (!XDC_LINES.some((re) => re.test(line))) return deny(`${where}: only pin and clock constraints are allowed`);
    } else if (tool === 'ise') {
      if (!UCF_LINES.some((re) => re.test(line))) return deny(`${where}: only pin and clock constraints are allowed`);
    } else {
      const g = QSF_GLOBAL.exec(line);
      if (g) {
        if (!QSF_GLOBAL_NAMES.has(g[1])) return deny(`${where}: the assignment ${g[1]} is not allowed`);
        const value = unquote(g[2]);
        if (g[1] === 'DEVICE') device = value;
        if (g[1] === 'TOP_LEVEL_ENTITY') topLevel = value;
        if ((g[1] === 'VERILOG_FILE' || g[1] === 'VHDL_FILE') && !request.sources.includes(value)) {
          return deny(`${where}: ${value} is not one of the --source files`);
        }
        continue;
      }
      if (!QSF_LINES.some((re) => re.test(line))) return deny(`${where}: only device, source, pin and IO assignments are allowed`);
    }
  }
  if (tool === 'quartus') {
    if (device === null || device.toUpperCase() !== request.part.toUpperCase()) return deny(`${name}: DEVICE must be ${request.part}`);
    if (topLevel !== request.top) return deny(`${name}: TOP_LEVEL_ENTITY must be ${request.top}`);
  }
  return OK;
}

/**
 * The header every .bit file starts with (a 9-byte field 0ff0 0ff0 0ff0 0ff0 00, then the "a" field); Vivado's
 * write_bitstream and xc7frames2bit both write it. Anything else is not loaded onto a board.
 */
const BIT_HEADER = Uint8Array.from([0x00, 0x09, 0x0f, 0xf0, 0x0f, 0xf0, 0x0f, 0xf0, 0x0f, 0xf0, 0x00, 0x00, 0x01, 0x61]);
const MAX_BIT_BYTES = 64 * 1024 * 1024;
function isXilinxBitFile(data) {
  if (!(data instanceof Uint8Array) || data.length < 64 || data.length > MAX_BIT_BYTES) return false;
  return BIT_HEADER.every((b, i) => data[i] === b);
}

/**
 * Quartus programming files start with their type: "SOF\0" (SRAM object file) or "POF\0" (programmer object file),
 * as Quartus Prime and Quartus II both write them; the file name's extension must say the same.
 */
function isQuartusProgrammingFile(name, data) {
  if (!(data instanceof Uint8Array) || data.length < 64 || data.length > MAX_BIT_BYTES) return false;
  const ext = /\.(sof|pof)$/i.exec(name);
  if (!ext) return false;
  const magic = ext[1].toUpperCase();
  return data[0] === magic.charCodeAt(0) && data[1] === magic.charCodeAt(1) && data[2] === magic.charCodeAt(2) && data[3] === 0;
}

/** Whether a programming run's file is what its tool loads onto a board */
const isProgrammingFile = (tool, name, data) => (tool === 'vivado' ? isXilinxBitFile(data) : tool === 'quartus' ? isQuartusProgrammingFile(name, data) : false);

/**
 * { ok: true, request } or a denial for a vendor tool request. files is the page's file map; it may hold only the
 * tool's file types, all as plain names in the run folder, and must hold every file the step reads.
 */
function checkVendorRequest(tool, args, files) {
  const parsed = parseVendorArgs(tool, args);
  if (!parsed.ok) return parsed;
  const request = parsed.request;
  const names = Object.keys(files || {});
  if (request.bitstream) {
    // A programming run gets the bitstream and nothing else, and it must be the tool's own file type
    if (names.length !== 1 || names[0] !== request.bitstream) return deny(`${tool} ${request.step}: only the file ${request.bitstream} is sent`);
    if (!isProgrammingFile(tool, request.bitstream, files[request.bitstream])) return deny(`${tool}: ${request.bitstream} is not a ${tool === 'vivado' ? 'Xilinx bitstream' : 'Quartus programming file'}`);
    return { ok: true, request };
  }
  for (const name of names) {
    if (!FILE_RE.test(name) || !INPUT_EXT[tool].test(name)) return deny(`${tool}: the file ${name} is not allowed`);
  }
  const have = new Set(names);
  for (const name of [...request.sources, ...(request.constraints ? [request.constraints] : []), ...request.reads]) {
    if (!have.has(name)) return deny(`${tool}: the file ${name} is missing`);
  }
  if (request.constraints) {
    const r = checkConstraintFile(tool, request.constraints, files[request.constraints], request);
    if (!r.ok) return r;
  }
  // Constraint files nobody named are refused too (Vivado would not read them, but there is no reason to send one)
  for (const name of names) {
    if (/\.(xdc|qsf|ucf)$/i.test(name) && name !== request.constraints) return deny(`${tool}: the file ${name} is not used`);
  }
  return { ok: true, request };
}

module.exports = {
  IDENT_RE,
  FILE_RE,
  VIVADO_PART_RE,
  QUARTUS_PART_RE,
  ISE_PART_RE,
  isVendorTool,
  parseVendorArgs,
  checkConstraintFile,
  checkVendorRequest,
  isQuartusProgrammingFile,
};
