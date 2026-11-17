// Path rule shared by the native ToolRunner and its argument policy (Aşama 6.0c).
// Same rule as isSafeRelativePath in src/tools/registry.ts: a relative path inside the run folder, with no drive
// letter or colon, no leading separator, no "..", no empty or "." segments and no NUL.
'use strict';

function isSafeRelativePath(p) {
  if (typeof p !== 'string' || p.length === 0 || p.length > 260) return false;
  if (p.includes('\0') || p.includes(':')) return false;
  if (p.startsWith('/') || p.startsWith('\\')) return false;
  return p.split(/[\\/]/).every((s) => s !== '' && s !== '.' && s !== '..');
}

module.exports = { isSafeRelativePath };
