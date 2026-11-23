// Puts localStorage back to OUT_DIR/ls_before.json exactly (extra keys removed) before the app's code runs,
// waits for the autosave, then compares.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { OUT_DIR, connect, sleep } from './cdp.mjs';

const before = JSON.parse(readFileSync(join(OUT_DIR, 'ls_before.json'), 'utf-8'));
let s = await connect('localhost');
const src = `(() => { const want = ${JSON.stringify(before)}; for (const k of Object.keys(localStorage)) if (!(k in want)) localStorage.removeItem(k); for (const [k, v] of Object.entries(want)) localStorage.setItem(k, v); })();`;
const r = await s.send('Page.addScriptToEvaluateOnNewDocument', { source: src });
await s.send('Page.reload', {});
await sleep(6000);
await s.send('Page.removeScriptToEvaluateOnNewDocument', { identifier: r.result.identifier });
s.close();
s = await connect('localhost');
await sleep(7000); // let the autosave run
const now = JSON.parse(await s.ev(`JSON.stringify(Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)])))`));
const keysSame = JSON.stringify(Object.keys(now).sort()) === JSON.stringify(Object.keys(before).sort());
const strip = (v) => {
  try {
    const o = JSON.parse(v);
    if (o && typeof o === 'object') delete o.timestamp;
    return JSON.stringify(o);
  } catch {
    return v;
  }
};
const diffs = Object.keys(before).filter((k) => strip(before[k]) !== strip(now[k]));
console.log('keys same:', keysSame, '| differing values (timestamp ignored):', diffs.join(',') || 'none');
for (const k of diffs) console.log(k, before[k].length, now[k]?.length);
s.close();
process.exit(keysSame && diffs.length === 0 ? 0 : 1);
