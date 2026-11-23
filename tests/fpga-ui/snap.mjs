// Saves the app's localStorage to OUT_DIR/ls_before.json, so restore_exact.mjs can put it back after the tests
// (the click tests change the language, the board mapping and the open sheet).
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { OUT_DIR, connect, sleep } from './cdp.mjs';

await sleep(Number(process.env.SNAP_DELAY ?? 3000));
const s = await connect('localhost');
const data = await s.ev(`JSON.stringify(Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)])))`);
writeFileSync(join(OUT_DIR, 'ls_before.json'), data);
const o = JSON.parse(data);
console.log(Object.keys(o).map((k) => `${k}: ${o[k].length}`).join('\n'));
console.log(`saved to ${join(OUT_DIR, 'ls_before.json')}`);
s.close();
