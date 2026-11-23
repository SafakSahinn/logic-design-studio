// Click-through of the Xilinx 7-series (openXC7) path of the "build and program" panel (Aşama 6j-6).
// Desktop: BASYS3 is built with yosys + nextpnr-xilinx + fasm2frames + xc7frames2bit, detection fails with the
// "no cable" message (no board here), and on a Zynq board (PYNQ-Z2) the flash target is disabled. Web: the panel
// explains that openXC7 runs only in the desktop app. See README.md for how to start the app.
//
// usage: CDP_PORT=9345 [OPEN_URL=...] [OUT_DIR=...] node xc7_click.mjs <tr|en> <desktop|web> [prefix]
import { OUT_DIR, connect, sleep, waiter } from './cdp.mjs';

const [lang = 'tr', mode = 'desktop', prefix = 'x'] = process.argv.slice(2);
const { ev, send, shot, close } = await connect('localhost');
const waitFor = waiter(ev);
let pass = 0;
let fail = 0;
const ok = (c, what, d) => {
  if (c) pass++;
  else {
    fail++;
    console.log('FAIL', what, d === undefined ? '' : JSON.stringify(d).slice(0, 900));
  }
};
const q = (sel) => `document.querySelector(${JSON.stringify(sel)})`;
const click = (sel) => ev(`(() => { const e = ${q(sel)}; if (!e || e.disabled) return false; e.click(); return true; })()`);
const text = (sel) => ev(`${q(sel)}?.textContent ?? null`);
const T = lang === 'tr';
const desktop = mode === 'desktop';
const steps = () => ev(`[...document.querySelectorAll('[data-fpga-build-step]')].map(e => e.getAttribute('data-fpga-build-step') + ':' + e.getAttribute('data-state')).join(' ')`);
const stepLabels = () => ev(`[...document.querySelectorAll('[data-fpga-build-step]')].map(e => e.textContent).join(' | ')`);
const msg = () => ev(`(() => { const m = ${q('[data-fpga-build-message]')}; return m ? m.getAttribute('data-fpga-build-message') + '|' + m.textContent : null; })()`);
const idle = (ms) => waitFor(`!document.querySelector('[data-fpga-build-cancel]') && !!document.querySelector('[data-fpga-build-message]')`, ms);
const logText = () => text('[data-fpga-build-log]');

if (process.env.OPEN_URL) {
  await send('Page.navigate', { url: process.env.OPEN_URL });
  await sleep(2500);
}
await ev(`localStorage.setItem('lds.language', '${lang}')`);
await send('Page.reload');
await sleep(3000);
await waitFor(`!!document.querySelector('svg')`);

ok(await ev(`(() => { const b = [...document.querySelectorAll('button')].find(b => (b.title||'').includes('Verilog')); if (!b) return false; b.click(); return true; })()`), 'open HDL modal');
await sleep(800);
ok(await ev(`(() => { const b = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === ${JSON.stringify(T ? 'FPGA projesi' : 'FPGA project')}); if (!b) return false; b.click(); return true; })()`), 'FPGA tab');
await waitFor(`!!document.querySelector('[data-fpga-open]')`);
await click('[data-fpga-open]');
ok(await waitFor(`!!document.querySelector('[data-fpga-dialog]')`), 'map dialog');

/** Picks a board in the map dialog, suggests a mapping and opens the build tab */
async function pickBoard(name) {
  await click('[data-fpga-tab="map"]');
  await sleep(300);
  await ev(`(() => { const s = ${q('[data-fpga-board-select]')}; Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(s, ${JSON.stringify(name)}); s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
  ok(await waitFor(`!!document.querySelector('[data-fpga-board=${JSON.stringify(name)}]')`), `board ${name}`);
  await sleep(400);
  ok(await click('[data-fpga-suggest]'), `suggest on ${name}`);
  await sleep(300);
  await click('[data-fpga-tab="build"]');
  await sleep(500);
}

await pickBoard('BASYS3');
const intro = await ev(`${q('[data-fpga-build]')}?.querySelector('p')?.textContent ?? ''`);
ok(intro.includes('openXC7'), 'intro names openXC7', intro);

if (!desktop) {
  // --- web: no browser build of openXC7 ---------------------------------------------------------------------
  const blocked = await text('[data-fpga-build-blocked]');
  ok(!!blocked && blocked.includes('openXC7') && blocked.includes('BASYS3'), 'web: desktop-only notice', blocked);
  ok(!(await ev(`!!document.querySelector('[data-fpga-build-run]')`)), 'web: no build button');
  await shot(`${prefix}_${lang}_web.png`);
  // GECKO5 still builds on the web
  await pickBoard('GECKO5_EDUCATION');
  ok(await ev(`!!document.querySelector('[data-fpga-build-run="build"]')`), 'web: GECKO5 still has the build button');
} else {
  ok(!(await ev(`!!document.querySelector('[data-fpga-build-no-openxc7]')`)), 'openXC7 found (no install hint)');
  ok(await ev(`!${q('[data-fpga-build-target="flash"]')}.disabled`), 'BASYS3: flash target enabled');
  // --- build only -------------------------------------------------------------------------------------------
  ok(await click('[data-fpga-build-run="build"]'), 'build click');
  ok(await idle(300000), 'build finishes');
  let m = await msg();
  ok(m?.startsWith('ok|'), 'build ok', { m, steps: await steps(), log: (await logText())?.slice(-1500) });
  ok(/^prepare:done synth:done placeRoute:done frames:done pack:done$/.test(await steps()), 'xc7 steps done', await steps());
  const labels = await stepLabels();
  ok(labels.includes('nextpnr-xilinx') && labels.includes('fasm2frames') && labels.includes('xc7frames2bit'), 'step labels name the tools', labels);
  const log = await logText();
  ok(log.includes('nextpnr-xilinx --device xc7a35tcpg236-1'), 'log: nextpnr-xilinx command', log.slice(0, 400));
  ok(log.includes('fasm2frames --part xc7a35tcpg236-1 toplevel.fasm toplevel.frames'), 'log: fasm2frames command');
  ok(!log.includes('prjxray-db') && !log.includes('--db-root'), 'log: page never named the database');
  ok(!(await ev(`${q('[data-fpga-build-download]')}.disabled`)), 'download enabled');
  await shot(`${prefix}_${lang}_1_built.png`);
  // --- detect: openFPGALoader -b basys3, no board here -----------------------------------------------------
  await click('[data-fpga-build-detect]');
  ok(await idle(60000), 'detect finishes');
  m = await msg();
  ok(m?.startsWith('error|') && m.includes(T ? 'Programlama kablosu bulunamadı' : 'No programming cable'), 'detect: no cable', { m, log: (await logText()).slice(0, 400) });
  ok((await logText()).includes('openFPGALoader -b basys3 --detect'), 'detect uses -b basys3');
  // --- program to SRAM: same problem ------------------------------------------------------------------------
  ok(await click('[data-fpga-build-program]'), 'program enabled after build');
  ok(await idle(60000), 'program finishes');
  ok((await logText()).includes('openFPGALoader -b basys3 -m toplevel.bit'), 'program: -b basys3 -m');
  await shot(`${prefix}_${lang}_2_program.png`);

  // --- a Zynq board: SRAM only --------------------------------------------------------------------------------
  await pickBoard('TUL_PYNQ_Z2');
  ok(await ev(`${q('[data-fpga-build-target="flash"]')}.disabled`), 'PYNQ-Z2: flash target disabled');
  const title = await ev(`${q('[data-fpga-build-target="flash"]')}.title`);
  ok(title.includes('Zynq'), 'PYNQ-Z2: flash tooltip explains', title);
  ok(await click('[data-fpga-build-run="build"]'), 'PYNQ build click');
  ok(await idle(300000), 'PYNQ build finishes');
  m = await msg();
  ok(m?.startsWith('ok|') && (await logText()).includes('xc7z020clg400-1'), 'PYNQ-Z2 build ok', { m, steps: await steps() });
  await shot(`${prefix}_${lang}_3_pynq.png`);
}

console.log(`xc7_click ${lang} ${mode}: ${pass} passed, ${fail} failed (screens in ${OUT_DIR})`);
close();
process.exit(fail ? 1 : 0);
