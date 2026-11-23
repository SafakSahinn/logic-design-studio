// Click-through of the FPGA "build and program" panel (Aşama 6j-4/6j-5), in the desktop app (Electron with the
// native tools) or in the web build (WASM tools, bitstream download). See README.md for how to start the app.
//
// usage: CDP_PORT=9345 [OPEN_URL=...] [OUT_DIR=...] node build_click.mjs <tr|en> <desktop|web> [prefix]
//   OPEN_URL  page to open first, e.g. http://localhost:5173/?preset=t_flip_flop_counter#circuit-simulator
//             (the circuit on the open sheet is what gets built)
//   QUICK=1   only the build (and on the web the download), no detect/program/VHDL/cancel/HDL-tab parts
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { OUT_DIR, connect, connectBrowser, sleep, waiter } from './cdp.mjs';

const [lang = 'tr', mode = 'desktop', prefix = 'b'] = process.argv.slice(2);
const QUICK = process.env.QUICK === '1';
const { ev, send, shot, logs, close } = await connect('localhost');
const waitFor = waiter(ev);
let pass = 0;
let fail = 0;
const ok = (c, what, d) => {
  if (c) pass++;
  else {
    fail++;
    console.log('FAIL', what, d === undefined ? '' : JSON.stringify(d).slice(0, 700));
  }
};
const q = (sel) => `document.querySelector(${JSON.stringify(sel)})`;
const click = (sel) => ev(`(() => { const e = ${q(sel)}; if (!e || e.disabled) return false; e.click(); return true; })()`);
const text = (sel) => ev(`${q(sel)}?.textContent ?? null`);
const T = lang === 'tr';
const desktop = mode === 'desktop';
const steps = () => ev(`[...document.querySelectorAll('[data-fpga-build-step]')].map(e => e.getAttribute('data-fpga-build-step') + ':' + e.getAttribute('data-state')).join(' ')`);
const msg = () => ev(`(() => { const m = ${q('[data-fpga-build-message]')}; return m ? m.getAttribute('data-fpga-build-message') + '|' + m.textContent : null; })()`);
const idle = (ms) => waitFor(`!document.querySelector('[data-fpga-build-cancel]') && !!document.querySelector('[data-fpga-build-message]')`, ms);
const logText = () => text('[data-fpga-build-log]');

// lds.language must be set on the app's origin (about:blank is another one), so navigate first
if (process.env.OPEN_URL) {
  await send('Page.navigate', { url: process.env.OPEN_URL });
  await sleep(2500);
}
await ev(`localStorage.setItem('lds.language', '${lang}')`);
await send('Page.reload');
await sleep(3000);
await waitFor(`!!document.querySelector('svg')`);

// --- the map dialog: GECKO5 + suggested mapping (the mapping is re-made each run) ----------------------------
ok(await ev(`(() => { const b = [...document.querySelectorAll('button')].find(b => (b.title||'').includes('Verilog')); if (!b) return false; b.click(); return true; })()`), 'open HDL modal');
await sleep(800);
ok(await ev(`(() => { const b = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === ${JSON.stringify(T ? 'FPGA projesi' : 'FPGA project')}); if (!b) return false; b.click(); return true; })()`), 'FPGA tab');
await waitFor(`!!document.querySelector('[data-fpga-open]')`);
await click('[data-fpga-open]');
ok(await waitFor(`!!document.querySelector('[data-fpga-dialog]')`), 'map dialog');
await ev(`(() => { const s = ${q('[data-fpga-board-select]')}; Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(s, 'GECKO5_EDUCATION'); s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
await waitFor(`!!document.querySelector('[data-fpga-board="GECKO5_EDUCATION"]')`);
await sleep(400);
ok(await click('[data-fpga-suggest]'), 'suggest');
await sleep(300);
const buildTab = await text('[data-fpga-tab="build"]');
ok(buildTab === (T ? 'Sentez ve yükleme' : 'Build & program'), 'build tab label', buildTab);
await click('[data-fpga-tab="build"]');
if (!(await waitFor(`!!document.querySelector('[data-fpga-build-run="build"]')`))) {
  // Wrong page (the web build opens on its home page: pass OPEN_URL=...#circuit-simulator) or no mapping
  console.log(`FAIL build button not found on ${await ev('location.href')} - is OPEN_URL the simulator page?`);
  process.exit(1);
}
pass++;
ok(desktop === !!(await ev(`!!document.querySelector('[data-fpga-build-run="program"]')`)), 'build-and-program only on the desktop');
ok(desktop === !!(await ev(`!!document.querySelector('[data-fpga-build-detect]')`)), 'detect only on the desktop');
ok(await ev(`${q('[data-fpga-build-download]')}.disabled`), 'download disabled before a build');
await shot(`${prefix}_${lang}_0.png`);

// --- build only ---------------------------------------------------------------------------------------------
await click('[data-fpga-build-run="build"]');
if (!desktop) {
  // The WASM download question (only when consent is not stored yet): agree to every tool
  for (let i = 0; i < 3; i++) {
    const asked = await waitFor(`!!document.querySelector('[aria-labelledby="lds-tool-download-title"]')`, i === 0 ? 4000 : 2500);
    if (!asked) break;
    if (i === 0) await shot(`${prefix}_${lang}_consent.png`);
    await ev(`[...document.querySelectorAll('[aria-labelledby="lds-tool-download-title"] button')].pop().click()`);
    await sleep(500);
  }
}
ok(await idle(desktop ? 180000 : 900000), 'build finishes');
let m = await msg();
ok(m?.startsWith('ok|'), 'build ok', { m, steps: await steps(), log: (await logText())?.slice(-1500) });
ok(/^prepare:done synth:done placeRoute:done pack:done$/.test(await steps()), 'steps done', await steps());
const logLines = (await logText()).split('\n');
ok(logLines.length > 30, 'log has the tools output', logLines.length);
ok(logLines[0].trim() !== '', 'log does not start with a blank line', logLines.slice(0, 2));
ok(!(await ev(`${q('[data-fpga-build-download]')}.disabled`)), 'download enabled after build');
await shot(`${prefix}_${lang}_1_built.png`);

// --- web: the download really saves the bitstream -----------------------------------------------------------
if (!desktop) {
  const dl = join(OUT_DIR, `dl_${prefix}_${lang}`);
  rmSync(dl, { recursive: true, force: true });
  mkdirSync(dl, { recursive: true });
  // Headless Chrome only saves files when the browser target allows it (Page.setDownloadBehavior is not enough)
  const browser = await connectBrowser();
  await browser.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dl });
  ok(await click('[data-fpga-build-download]'), 'download click');
  let file = null;
  for (let i = 0; i < 50 && !file; i++) {
    await sleep(200);
    file = readdirSync(dl).find((f) => f.endsWith('.bit')) ?? null;
  }
  ok(!!file, 'bitstream file saved', readdirSync(dl));
  if (file) {
    const bytes = readFileSync(join(dl, file));
    ok(statSync(join(dl, file)).size > 10_000 && bytes[0] === 0xff && bytes[1] === 0x00, 'saved file looks like an ECP5 bitstream', { size: bytes.length, head: [...bytes.subarray(0, 4)] });
  }
  m = await msg();
  ok(m?.startsWith('info|') && m.includes(file ?? '.bit'), 'download message', m);
  await browser.send('Browser.setDownloadBehavior', { behavior: 'default' });
  browser.close();
}

if (!QUICK) {
  if (desktop) {
    // --- detect: no board on this machine -> a friendly "no cable" message -----------------------------------
    await click('[data-fpga-build-detect]');
    ok(await idle(60000), 'detect finishes');
    m = await msg();
    ok(m?.startsWith('error|') && m.includes(T ? 'Programlama kablosu bulunamadı' : 'No programming cable'), 'detect: no cable', { m, log: await logText() });
    // --- program to SRAM -> same problem; the log starts with the stage header, not a blank line ------------
    ok(await click('[data-fpga-build-program]'), 'program button enabled after build');
    ok(await idle(60000), 'program finishes');
    m = await msg();
    ok(m?.startsWith('error|') && m.includes(T ? 'Programlama kablosu bulunamadı' : 'No programming cable'), 'program: no cable', { m, steps: await steps() });
    ok((await steps()) === 'program:failed', 'program step failed', await steps());
    ok((await logText()).startsWith('== '), 'program-only log starts with the header', (await logText()).slice(0, 80));
    await shot(`${prefix}_${lang}_2_program.png`);
    // --- build and program: the flow runs, programming fails the same way -----------------------------------
    await click('[data-fpga-build-run="program"]');
    ok(await idle(180000), 'build+program finishes');
    ok(/^prepare:done synth:done placeRoute:done pack:done program:failed$/.test(await steps()), 'build+program steps', await steps());
  }

  // --- changing the circuit's language makes the bitstream stale -------------------------------------------
  await click('[data-fpga-build-lang="vhdl"]');
  if (desktop) {
    ok(await waitFor(`!!document.querySelector('[data-fpga-build-stale]')`, 3000), 'stale note after a language change');
    ok(await ev(`${q('[data-fpga-build-download]')}.disabled`), 'stale bitstream cannot be downloaded');
    ok(await ev(`${q('[data-fpga-build-program]')}.disabled`), 'stale bitstream cannot be programmed');
  } else {
    // Without ghdl, VHDL is synthesized from the same Verilog: the very same bitstream, so it stays current
    await sleep(800);
    ok(!(await ev(`!!document.querySelector('[data-fpga-build-stale]')`)), 'web: VHDL-as-Verilog keeps the bitstream current');
    ok(!(await ev(`${q('[data-fpga-build-download]')}.disabled`)), 'web: download still enabled');
  }
  ok(desktop === !(await ev(`!!document.querySelector('[data-fpga-build-vhdl-note]')`)), 'VHDL-as-Verilog note only without ghdl');
  // ... and switching back makes it current again
  await click('[data-fpga-build-lang="verilog"]');
  ok(await waitFor(`!document.querySelector('[data-fpga-build-stale]')`, 3000), 'not stale after switching back');
  await click('[data-fpga-build-lang="vhdl"]');
  if (desktop) {
    await click('[data-fpga-build-run="build"]');
    ok(await idle(180000), 'VHDL build finishes');
    ok(/^prepare:done vhdlToVerilog:done synth:done placeRoute:done pack:done$/.test(await steps()), 'VHDL steps (ghdl)', { s: await steps(), m: await msg() });
  }

  // --- cancel during a run ---------------------------------------------------------------------------------
  await click('[data-fpga-build-run="build"]');
  await waitFor(`!!document.querySelector('[data-fpga-build-step="synth"][data-state="running"]')`, 20000);
  await sleep(300);
  ok(await click('[data-fpga-build-cancel]'), 'cancel click');
  ok(await idle(30000), 'cancelled run ends');
  m = await msg();
  ok(m === (T ? 'info|İptal edildi.' : 'info|Cancelled.'), 'cancelled message', { m, steps: await steps() });
  ok(/:failed( \w+:skipped)*$/.test(await steps()) && !/pack:done/.test(await steps()), 'cancel steps', await steps());
  await shot(`${prefix}_${lang}_3_cancel.png`);
  await click('[data-fpga-build-lang="verilog"]');

  // --- the same panel inside the HDL window ----------------------------------------------------------------
  await click('[data-fpga-close]');
  await sleep(400);
  ok(await waitFor(`!!document.querySelector('[data-fpga-hdl-view="build"]')`), 'HDL tab: build view button');
  await click('[data-fpga-hdl-view="build"]');
  ok(await waitFor(`!!document.querySelector('[data-fpga-hdl] [data-fpga-build-run="build"]')`), 'HDL tab: panel shown');
  ok(!(await ev(`!!document.querySelector('[data-fpga-hdl] [data-fpga-build-lang]')`)), 'HDL tab: no own language choice');
  await shot(`${prefix}_${lang}_4_hdltab.png`);
  await click('[data-fpga-hdl-view="topLevel"]');
  ok(await waitFor(`!!document.querySelector('[data-fpga-hdl-file]')`), 'HDL tab: back to the files');
}

const noise = /Download the React DevTools|DevTools/;
const shown = logs.filter((l) => !noise.test(l)).slice(0, 10);
if (shown.length) console.log(shown.join('\n'));
console.log(`${prefix} ${lang} ${mode}: ${pass} passed, ${fail} failed (screenshots in ${OUT_DIR}${existsSync(OUT_DIR) ? '' : ' - missing'})`);
close();
process.exit(fail ? 1 : 0);
