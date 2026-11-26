// HDL file references (6k-6): which files a Verilog / VHDL source makes the tool open.
//
// A tool that compiles a source also opens the files the source names: `include, $readmemh / $readmemb, $fopen,
// memory init parameters and attributes (init_file, MEMORY_INIT_FILE, ram_init_file...) and VHDL file
// declarations. The page may only name files inside the run folder, and only as a plain string literal: anything
// computed (a macro, a constant, a concatenation) could name any file on the computer and is refused.
//
// The 6k-1 check used regular expressions over the raw text; a comment between the name and "(", a `define body or
// a token paste got past it. This module tokenizes first (comments, strings, escaped identifiers, VHDL character
// literals), so every check below sees what the tool sees, and refuses what it cannot follow:
//   - file tasks and `include take one plain relative literal;
//   - a file parameter / generic / attribute (FILE_PARAM) is only set by name to a plain relative literal, and a
//     parameter or generic list given by position may hold numbers only (a position could be a file parameter);
//   - macros may not contain file tasks, `include, file parameter names, "#(" or token pastes;
//   - altera_attribute (any Quartus assignment) is refused, and so is a comment that names a file parameter
//     (Quartus and XST read "synthesis" directives from comments);
//   - a literal that is an absolute path, a drive, or climbs out with ".." is refused wherever it is.
// What stays out of reach of a token check: a file parameter of a vendor primitive set from a value built out of
// numbers ({8'h43, 8'h3A, ...}) where the name is not visible. Named and positional forms are covered above.
'use strict';

const { isSafeRelativePath } = require('./pathRules.cjs');

const deny = (message) => ({ ok: false, message });
const OK = { ok: true };

const VERILOG_HEADER_EXT = /\.(v|sv|vh|svh)$/i;
// System tasks that open, read or write a file by name
const FILE_TASK = /^\$(readmem|writemem|sreadmem|fopen|dumpfile|fdumpfile)/i;
// System tasks that are never allowed (run a program)
const DENIED_TASK = /^\$system$/i;
// Parameter / attribute / generic names whose value is a file the tool reads (Quartus init_file, lpm_file,
// ram_init_file, mif_file; Vivado XPM MEMORY_INIT_FILE; Xilinx INIT_FILE)
const FILE_PARAM = /^(?:\w*_)?(?:init_file|init_filename|lpm_file|mif_file)$/i;
// Names that may never appear: altera_attribute carries any Quartus assignment (also file settings)
const DENIED_NAME = /^altera_attribute$/i;
// A comment that is (or could be) a synthesis directive about files
const DIRECTIVE_COMMENT = /init_file|init_filename|lpm_file|mif_file|altera_attribute/i;

class LexError extends Error {}

/**
 * A file name given as a string literal: relative, inside the run folder, and only letters, digits, "_", ".", "-",
 * " " and "/" (no escapes, quotes, control or format characters)
 */
function isPlainRelativeName(value) {
  if (!/^[A-Za-z0-9_. /-]+$/.test(value)) return false;
  return isSafeRelativePath(value);
}

// VHDL operator symbols are written as strings ("/" in function "/" (a, b : t)); they are not paths
const VHDL_OPERATOR_SYMBOLS = new Set(['/', '/=', '?/=']);

/**
 * A string that looks like a path outside the run folder, or a piece of one, wherever it is: starts with a separator
 * or "~", is a drive ("C:", "C:/x"), starts with ":" (a drive split over a concatenation), or has a ".." part. It
 * catches literal paths in places the name-based checks do not know about (a vendor primitive parameter). A
 * message such as "t: %d" is not one.
 */
function isOutsidePath(value) {
  if (VHDL_OPERATOR_SYMBOLS.has(value)) return false;
  if (/^[\\/~:]/.test(value) || /^[A-Za-z]:(?:[\\/]|$)/.test(value)) return true;
  return value.split(/[\\/]/).includes('..');
}

const isP = (tok, v) => !!tok && tok.t === 'p' && tok.v === v;

/**
 * The items of a list that opens at tokens[k] ("("): arrays of tokens split at its own commas, and the index of its
 * ")", or null when it does not close.
 */
function listItems(tokens, k) {
  const items = [[]];
  let depth = 0;
  for (let j = k + 1; j < tokens.length; j++) {
    const tok = tokens[j];
    if (tok.t === 'p' && (tok.v === '(' || tok.v === '[' || tok.v === '{' || tok.v === '(*')) depth++;
    if (tok.t === 'p' && (tok.v === ')' || tok.v === ']' || tok.v === '}' || tok.v === '*)')) {
      if (depth === 0) return tok.v === ')' ? { items, end: j } : null;
      depth--;
    }
    if (depth === 0 && isP(tok, ',')) items.push([]);
    else items[items.length - 1].push(tok);
  }
  return null;
}

/** A value given by position: numbers only (with signs and the ":" of a min:typ:max delay) */
const isNumericItem = (item) => item.length > 0 && item.every((tok) => tok.t === 'num' || (tok.t === 'p' && ['-', '+', ':', '.'].includes(tok.v)));

// --- Verilog / SystemVerilog -------------------------------------------------------------------------

const isIdStart = (c) => /[A-Za-z_]/.test(c);
const isIdChar = (c) => /[A-Za-z0-9_$]/.test(c);

/**
 * Tokens of a Verilog text: { t: 'id' | 'sys' | 'dir' | 'str' | 'num' | 'esc' | 'p', v, line, define }, and the
 * comments' text. A `define body (to the first newline not escaped by "\") is tokenized too and its tokens carry
 * define: true. Throws on what the tool might read differently: an unterminated string or comment, a triple-quoted
 * string, a line comment continued inside a macro.
 */
function verilogTokens(text) {
  const tokens = [];
  const comments = [];
  let i = 0;
  let line = 1;
  let inDefine = false; // inside a `define body
  const n = text.length;
  const push = (t, v) => tokens.push({ t, v, line, define: inDefine });
  while (i < n) {
    const c = text[i];
    if (c === '\n') {
      line++;
      i++;
      inDefine = false;
      continue;
    }
    if (c === '\\' && (text[i + 1] === '\n' || (text[i + 1] === '\r' && text[i + 2] === '\n'))) {
      // Line continuation: a `define body goes on; elsewhere it is only white space
      i += text[i + 1] === '\r' ? 3 : 2;
      line++;
      continue;
    }
    if (/\s/.test(c)) {
      i++;
      continue;
    }
    if (c === '/' && text[i + 1] === '/') {
      // To the end of the line. Inside a `define a "\" before the newline does not continue a comment the same way
      // for every tool, so a continued line comment inside a macro is refused.
      let j = text.indexOf('\n', i);
      if (j < 0) j = n;
      const body = text.slice(i, j).replace(/\r$/, '');
      if (inDefine && body.endsWith('\\')) throw new LexError(`line ${line}: a // comment that continues a \`define`);
      comments.push({ v: body, line });
      i = j;
      continue;
    }
    if (c === '/' && text[i + 1] === '*') {
      const j = text.indexOf('*/', i + 2);
      if (j < 0) throw new LexError(`line ${line}: unterminated /* comment`);
      comments.push({ v: text.slice(i, j + 2), line });
      for (let k = i; k < j; k++) if (text[k] === '\n') line++;
      i = j + 2;
      continue;
    }
    if (c === '"') {
      if (text[i + 1] === '"' && text[i + 2] === '"') throw new LexError(`line ${line}: triple-quoted strings are not allowed`);
      let j = i + 1;
      let value = '';
      for (;;) {
        if (j >= n || text[j] === '\n' || text[j] === '\r') throw new LexError(`line ${line}: unterminated string`);
        if (text[j] === '"') break;
        if (text[j] === '\\') {
          // An escape: kept with its backslash so a file name with any escape is refused
          if (j + 1 >= n || text[j + 1] === '\n' || text[j + 1] === '\r') throw new LexError(`line ${line}: a string continued on the next line`);
          value += text.slice(j, j + 2);
          j += 2;
          continue;
        }
        value += text[j];
        j++;
      }
      push('str', value);
      i = j + 1;
      continue;
    }
    if (c === '\\') {
      // Escaped identifier: to the next white space; it may contain any character, also quotes
      let j = i + 1;
      while (j < n && !/\s/.test(text[j])) j++;
      push('esc', text.slice(i, j));
      i = j;
      continue;
    }
    if (c === '`') {
      if (text[i + 1] === '`' || text[i + 1] === '"' || text[i + 1] === '\\') {
        // Token paste ``, stringify `" and `\`" (SystemVerilog macro operators)
        push('p', text[i + 1] === '\\' ? '`\\' : `\`${text[i + 1]}`);
        i += 2;
        continue;
      }
      let j = i + 1;
      while (j < n && isIdChar(text[j])) j++;
      const name = text.slice(i + 1, j);
      push('dir', name);
      i = j;
      if (name === 'define') inDefine = true;
      continue;
    }
    if (c === '$') {
      let j = i + 1;
      while (j < n && isIdChar(text[j])) j++;
      push('sys', text.slice(i, j));
      i = j;
      continue;
    }
    if (isIdStart(c)) {
      let j = i + 1;
      while (j < n && isIdChar(text[j])) j++;
      push('id', text.slice(i, j));
      i = j;
      continue;
    }
    if (/[0-9']/.test(c)) {
      let j = i + 1;
      while (j < n && /[0-9a-zA-Z_'?]/.test(text[j])) j++;
      push('num', text.slice(i, j));
      i = j;
      continue;
    }
    // Punctuation; "(*" / "*)" attribute brackets kept as one token
    const two = text.slice(i, i + 2);
    if (two === '(*' && text[i + 2] !== ')') {
      push('p', '(*');
      i += 2;
      continue;
    }
    if (two === '*)') {
      push('p', '*)');
      i += 2;
      continue;
    }
    push('p', c);
    i++;
  }
  return { tokens, comments };
}

/** tokens[k] is "(" then a plain relative string literal, then "," or ")" */
function literalCallArgument(tokens, k) {
  const lit = tokens[k + 1];
  const after = tokens[k + 2];
  if (!isP(tokens[k], '(')) return null;
  if (!lit || lit.t !== 'str' || !isPlainRelativeName(lit.v)) return null;
  if (!after || after.t !== 'p' || (after.v !== ',' && after.v !== ')')) return null;
  return lit.v;
}

/**
 * A file parameter / attribute (FILE_PARAM name at tokens[k]) is set by name to a plain relative literal that ends
 * the clause: (* ram_init_file = "x.mif" *), .init_file("x.hex"), defparam u.init_file = "x";
 * parameter MEMORY_INIT_FILE = "x.mem". Anything else (the name on its own, as a macro argument, a signal of that
 * name) is refused: the value could come from elsewhere.
 */
function verilogFileParamOk(tokens, k) {
  const next = tokens[k + 1];
  if (isP(next, '(')) return literalCallArgument(tokens, k + 1) !== null;
  if (isP(next, '=')) {
    const lit = tokens[k + 2];
    const end = tokens[k + 3];
    if (!lit || lit.t !== 'str' || !isPlainRelativeName(lit.v)) return false;
    return !end || (end.t === 'p' && [',', ';', ')', '*)'].includes(end.v));
  }
  return false;
}

/**
 * "#" at tokens[k]: a delay (#5, #(1:2:3)) or a parameter override. A list given by position may hold numbers only;
 * a named list (#(.a(1), ...)) is checked name by name. "#" before a macro or a name could be a positional
 * override in disguise and is refused, as is "##".
 */
function verilogHashOk(tokens, k) {
  const next = tokens[k + 1];
  if (!next) return false;
  // The parameter declarations of a module header (module m #(parameter N = 2, ...)): no override, nothing to check
  const head = tokens[k - 2];
  if (tokens[k - 1] && tokens[k - 1].t === 'id' && head && head.t === 'id' && DECLARES_PARAMETERS.has(head.v)) return true;
  if (next.t === 'num') return true;
  if (!isP(next, '(')) return false;
  const list = listItems(tokens, k + 1);
  if (!list) return false;
  if (list.items.length === 1 && list.items[0].length === 0) return true; // #()
  // Named: ".NAME(" with a plain name (a macro there could join into a file parameter name at its use)
  const named = (item) => isP(item[0], '.') && item[1] && (item[1].t === 'id' || item[1].t === 'esc') && isP(item[2], '(');
  return list.items.every((item) => named(item) || isNumericItem(item));
}

// Keywords whose header may declare parameters with "#(": module m #(parameter ...)
const DECLARES_PARAMETERS = new Set(['module', 'macromodule', 'interface', 'program', 'package', 'class', 'checker']);

const nameOf = (tok) => (tok.t === 'esc' ? tok.v.slice(1) : tok.v);

function checkVerilog(name, text) {
  let lexed;
  try {
    lexed = verilogTokens(text);
  } catch (err) {
    if (err instanceof LexError) return deny(`${name}: ${err.message}`);
    throw err;
  }
  const { tokens, comments } = lexed;
  for (const c of comments) {
    if (DIRECTIVE_COMMENT.test(c.v)) return deny(`${name}: line ${c.line}: a comment may not name a memory init file setting (synthesis directive)`);
  }
  for (let k = 0; k < tokens.length; k++) {
    const tok = tokens[k];
    if (tok.t === 'str' && isOutsidePath(tok.v)) return deny(`${name}: line ${tok.line}: "${tok.v}" names a file outside the run folder`);
    const isName = tok.t === 'id' || tok.t === 'esc';
    if (isName && DENIED_NAME.test(nameOf(tok))) return deny(`${name}: line ${tok.line}: ${tok.v} is not allowed`);
    if (tok.define) {
      // A macro could be the name of a file task, an `include, a file parameter or a positional override at its
      // use, out of sight of the checks below. Token pastes could build those names, so they are refused as well.
      if (tok.t === 'sys' && (FILE_TASK.test(tok.v) || DENIED_TASK.test(tok.v) || tok.v === '$')) return deny(`${name}: line ${tok.line}: a \`define may not contain ${tok.v}`);
      if (tok.t === 'dir' && tok.v === 'include') return deny(`${name}: line ${tok.line}: a \`define may not contain \`include`);
      if (tok.t === 'p' && tok.v === '``') return deny(`${name}: line ${tok.line}: token pasting (\`\`) is not allowed`);
      if (isName && FILE_PARAM.test(nameOf(tok))) return deny(`${name}: line ${tok.line}: a \`define may not contain ${tok.v}`);
      if (isP(tok, '#') && !(tokens[k + 1] && tokens[k + 1].define && tokens[k + 1].t === 'num')) return deny(`${name}: line ${tok.line}: a \`define may only use "#" with a number`);
    }
    if (tok.t === 'sys') {
      if (tok.v === '$') return deny(`${name}: line ${tok.line}: a lone "$" is not allowed`);
      if (DENIED_TASK.test(tok.v)) return deny(`${name}: line ${tok.line}: ${tok.v} is not allowed`);
      if (FILE_TASK.test(tok.v) && literalCallArgument(tokens, k + 1) === null) return deny(`${name}: line ${tok.line}: ${tok.v} must name a relative file as a plain string`);
    }
    if (tok.t === 'dir' && tok.v === 'include' && !tok.define) {
      const lit = tokens[k + 1];
      if (!lit || lit.t !== 'str' || !isPlainRelativeName(lit.v)) return deny(`${name}: line ${tok.line}: \`include must name a relative file as a plain string`);
      // Only another source the policy also reads: a .hex / .txt data file is never checked as Verilog
      if (!VERILOG_HEADER_EXT.test(lit.v)) return deny(`${name}: line ${tok.line}: \`include may only name a Verilog file (.v, .sv, .vh, .svh)`);
    }
    if (isName && FILE_PARAM.test(nameOf(tok)) && !verilogFileParamOk(tokens, k)) {
      return deny(`${name}: line ${tok.line}: ${tok.v} must be set to a relative file as a plain string`);
    }
    if (isP(tok, '#') && !tok.define && !verilogHashOk(tokens, k)) {
      return deny(`${name}: line ${tok.line}: parameters given by position may only be numbers; name them (#(.NAME(value)))`);
    }
  }
  return OK;
}

// --- VHDL ----------------------------------------------------------------------------------------------

// VHDL-2008 reserved words: a quote after one of them starts a character literal, never an attribute tick
const VHDL_RESERVED = new Set(('abs access after alias all and architecture array assert assume assume_guarantee attribute begin block body ' +
  'buffer bus case component configuration constant context cover default disconnect downto else elsif end entity exit fairness file for ' +
  'force function generate generic group guarded if impure in inertial inout is label library linkage literal loop map mod nand new next ' +
  'nor not null of on open or others out package parameter port postponed procedure process property protected pure range record register ' +
  'reject release rem report restrict restrict_guarantee return rol ror select sequence severity shared signal sla sll sra srl strong ' +
  'subtype then to transport type unaffected units until use variable vmode vprop vunit wait when while with xnor xor').split(' '));

/**
 * Tokens of a VHDL text: { t: 'id' | 'ext' | 'str' | 'chr' | 'num' | 'p', v (identifiers lower case), line }, and
 * the comments' text. A character literal is told from an attribute tick by the token before it, as the VHDL
 * grammar does: a tick only follows a name or a closing bracket, never a reserved word.
 */
function vhdlTokens(text) {
  const tokens = [];
  const comments = [];
  let i = 0;
  let line = 1;
  const n = text.length;
  const push = (t, v) => tokens.push({ t, v, line });
  while (i < n) {
    const c = text[i];
    if (c === '\n') {
      line++;
      i++;
      continue;
    }
    if (/\s/.test(c)) {
      i++;
      continue;
    }
    if (c === '-' && text[i + 1] === '-') {
      let j = text.indexOf('\n', i);
      if (j < 0) j = n;
      comments.push({ v: text.slice(i, j), line });
      i = j;
      continue;
    }
    if (c === '/' && text[i + 1] === '*') {
      const j = text.indexOf('*/', i + 2);
      if (j < 0) throw new LexError(`line ${line}: unterminated /* comment`);
      comments.push({ v: text.slice(i, j + 2), line });
      for (let k = i; k < j; k++) if (text[k] === '\n') line++;
      i = j + 2;
      continue;
    }
    if (c === '"' || c === '%') {
      // String ("" is a quote inside); "%" is the old replacement string delimiter
      let j = i + 1;
      let value = '';
      for (;;) {
        if (j >= n || text[j] === '\n' || text[j] === '\r') throw new LexError(`line ${line}: unterminated string`);
        if (text[j] === c) {
          if (text[j + 1] === c) {
            value += c;
            j += 2;
            continue;
          }
          break;
        }
        value += text[j];
        j++;
      }
      push('str', value);
      i = j + 1;
      continue;
    }
    if (c === '\\') {
      // Extended identifier: \name\ with \\ as a backslash inside
      let j = i + 1;
      for (;;) {
        if (j >= n || text[j] === '\n') throw new LexError(`line ${line}: unterminated extended identifier`);
        if (text[j] === '\\') {
          if (text[j + 1] === '\\') {
            j += 2;
            continue;
          }
          break;
        }
        j++;
      }
      push('ext', text.slice(i, j + 1));
      i = j + 1;
      continue;
    }
    if (c === "'") {
      const prev = tokens[tokens.length - 1];
      const tick =
        !!prev && ((prev.t === 'id' && !VHDL_RESERVED.has(prev.v)) || prev.t === 'ext' || (prev.t === 'p' && (prev.v === ')' || prev.v === ']')));
      if (!tick && i + 2 < n && text[i + 2] === "'") {
        push('chr', text[i + 1]);
        i += 3;
        continue;
      }
      push('p', "'");
      i++;
      continue;
    }
    if (/[A-Za-z]/.test(c)) {
      let j = i + 1;
      while (j < n && /[A-Za-z0-9_]/.test(text[j])) j++;
      // Bit string literal: X"FF", B"0101", O"7", UX"F"...: the string is the next token
      if (text[j] === '"' && /^(b|o|x|d|ub|uo|ux|sb|so|sx)$/i.test(text.slice(i, j))) {
        i = j;
        continue;
      }
      push('id', text.slice(i, j).toLowerCase());
      i = j;
      continue;
    }
    if (/[0-9]/.test(c)) {
      let j = i + 1;
      while (j < n && /[0-9a-zA-Z_#.]/.test(text[j])) j++;
      push('num', text.slice(i, j));
      i = j;
      continue;
    }
    const two = text.slice(i, i + 2);
    if (two === '=>' || two === ':=' || two === '<=' || two === '/=' || two === '>=' || two === '**') {
      push('p', two);
      i += 2;
      continue;
    }
    push('p', c);
    i++;
  }
  return { tokens, comments };
}

const isId = (tok, v) => !!tok && tok.t === 'id' && tok.v === v;
const plainLiteral = (tok) => !!tok && tok.t === 'str' && isPlainRelativeName(tok.v);

/**
 * A file declaration from tokens[k] ("file"): file a, b : type_mark [open mode] is ["in"|"out"] "name";
 * or no file name at all (then only file_open could open it, and that is refused). In a subprogram parameter
 * list the declaration ends at ")" or ";". "attribute x of all : file is ..." names the entity class "file".
 */
function vhdlFileDeclOk(tokens, k) {
  if (isP(tokens[k - 1], ':') && isId(tokens[k + 1], 'is')) return true; // entity class in an attribute specification
  let j = k + 1;
  // identifier list
  for (;;) {
    if (!tokens[j] || (tokens[j].t !== 'id' && tokens[j].t !== 'ext')) return false;
    j++;
    if (isP(tokens[j], ',')) j++;
    else break;
  }
  if (!isP(tokens[j], ':')) return false;
  j++;
  // type mark: a name, maybe selected (std.textio.text)
  for (;;) {
    if (!tokens[j] || tokens[j].t !== 'id') return false;
    j++;
    if (isP(tokens[j], '.')) j++;
    else break;
  }
  if (isP(tokens[j], ';') || isP(tokens[j], ')')) return true;
  if (isId(tokens[j], 'open')) {
    j++;
    if (!tokens[j] || tokens[j].t !== 'id') return false; // read_mode / write_mode / append_mode
    j++;
    if (!isId(tokens[j], 'is')) return false;
  } else if (!isId(tokens[j], 'is')) return false;
  j++;
  if (isId(tokens[j], 'in') || isId(tokens[j], 'out')) j++;
  return plainLiteral(tokens[j]) && isP(tokens[j + 1], ';');
}

/**
 * A file generic / attribute (FILE_PARAM name at tokens[k]): its value must be a plain relative literal that ends
 * the clause. Forms: generic map (init_file => "x.mif"); init_file : string := "x.mif" (also in an identifier list
 * "a, init_file : string := ..."); attribute ram_init_file of mem : signal is "x.mif"; attribute ram_init_file :
 * string; a declaration without a value. The name as an actual or on the left of "<=" is refused.
 */
function vhdlFileParamOk(tokens, k) {
  const ends = (tok) => isP(tok, ';') || isP(tok, ',') || isP(tok, ')');
  const valueAt = (j) => plainLiteral(tokens[j]) && (!tokens[j + 1] || ends(tokens[j + 1]));
  let j = k + 1;
  // In an identifier list the declaration's ":" comes after the other names
  while (isP(tokens[j], ',') && tokens[j + 1] && (tokens[j + 1].t === 'id' || tokens[j + 1].t === 'ext')) j += 2;
  const next = tokens[j];
  if (isP(next, '=>')) return valueAt(j + 1);
  if (isP(next, ':')) {
    // a declaration: mode / type mark (maybe selected), then := value
    j++;
    while (tokens[j] && (tokens[j].t === 'id' || isP(tokens[j], '.'))) j++;
    if (!tokens[j] || isP(tokens[j], ';') || isP(tokens[j], ')')) return true;
    if (isP(tokens[j], ':=')) return valueAt(j + 1);
    return false;
  }
  if (isId(next, 'of')) {
    // attribute specification: of <names> : <entity class> is <value>;
    j++;
    while (tokens[j] && !isId(tokens[j], 'is')) {
      if (isP(tokens[j], ';')) return false;
      j++;
    }
    return plainLiteral(tokens[j + 1]) && isP(tokens[j + 2], ';');
  }
  return false;
}

/** "generic map" at tokens[k]: every element given by position holds numbers only (a position could be a file generic) */
function vhdlGenericMapOk(tokens, k) {
  if (!isId(tokens[k + 1], 'map') || !isP(tokens[k + 2], '(')) return true;
  const list = listItems(tokens, k + 2);
  if (!list) return false;
  // Named: exactly "formal => actual" (the formal a plain name, "=>" its second token; an aggregate or a call with
  // named arguments inside a positional item is not a name)
  const named = (item) => item.length >= 3 && (item[0].t === 'id' || item[0].t === 'ext') && isP(item[1], '=>');
  return list.items.every((item) => named(item) || isNumericItem(item));
}

function checkVhdl(name, text) {
  let lexed;
  try {
    lexed = vhdlTokens(text);
  } catch (err) {
    if (err instanceof LexError) return deny(`${name}: ${err.message}`);
    throw err;
  }
  const { tokens, comments } = lexed;
  for (const c of comments) {
    if (DIRECTIVE_COMMENT.test(c.v)) return deny(`${name}: line ${c.line}: a comment may not name a memory init file setting (synthesis directive)`);
  }
  for (let k = 0; k < tokens.length; k++) {
    const tok = tokens[k];
    if (tok.t === 'str' && isOutsidePath(tok.v)) return deny(`${name}: line ${tok.line}: "${tok.v}" names a file outside the run folder`);
    if (tok.t !== 'id' && tok.t !== 'ext') continue;
    const id = tok.t === 'ext' ? tok.v.slice(1, -1).toLowerCase() : tok.v;
    // file_open can take any computed string; an alias or a call of it is refused alike
    if (id === 'file_open') return deny(`${name}: line ${tok.line}: file_open is not allowed; declare the file with a relative string instead`);
    if (DENIED_NAME.test(id)) return deny(`${name}: line ${tok.line}: ${id} is not allowed`);
    if (tok.t === 'id' && id === 'file' && !vhdlFileDeclOk(tokens, k)) return deny(`${name}: line ${tok.line}: a VHDL file must be declared with a relative file name as a plain string`);
    if (FILE_PARAM.test(id) && !vhdlFileParamOk(tokens, k)) return deny(`${name}: line ${tok.line}: ${id} must be set to a relative file as a plain string`);
    if (tok.t === 'id' && id === 'generic' && !vhdlGenericMapOk(tokens, k)) {
      return deny(`${name}: line ${tok.line}: generics given by position may only be numbers; name them (NAME => value)`);
    }
  }
  return OK;
}

// --- yosys macro definitions -------------------------------------------------------------------------

/** A macro definition given on a command line (yosys -D, read_verilog -D, verilog_defines -D): NAME or NAME=word */
function isPlainDefine(value) {
  return typeof value === 'string' && /^[A-Za-z_]\w*(=[\w.]*)?$/.test(value);
}

module.exports = { checkVerilog, checkVhdl, verilogTokens, vhdlTokens, isPlainDefine, isOutsidePath, FILE_PARAM };
