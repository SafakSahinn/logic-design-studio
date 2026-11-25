// Click-through of the vendor-tool UI of the "build and program" panel (Aşama 6k-5).
// Desktop: on BASYS3 the panel offers openXC7 or Vivado (open by default), remembers the choice per board across a
// reload, builds with Vivado, programs with Vivado (no board here: "no cable"), and then, with Vivado's hw_server
// left running, openFPGALoader's "no cable" carries the hw_server hint. The "Vendor tools" section lists the
// installs and checks one. CMOD A7-15T (Vivado only), a Quartus board and an ISE board show no choice; GECKO5 shows
// neither the choice nor the section. Web: no choice, no section, and vendor boards say "desktop only".
// See README.md for how to start the app.
//
// usage: CDP_PORT=9345 [OPEN_URL=...] [OUT_DIR=...] [QUICK=1] node vendor_click.mjs <tr|en> <desktop|web> [prefix]
// QUICK=1 skips the Vivado build and programming (the slow part, 1-2 minutes).
import { execFileSync } from 'node:child_process';
import { OUT_DIR, connect, sleep, waiter } from './cdp.mjs';

const [lang = 'tr', mode = 'desktop', prefix = 'v'] = process.argv.slice(2);
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
const has = (sel) => ev(`!!${q(sel)}`);
const click = (sel) => ev(`(() => { const e = ${q(sel)}; if (!e || e.disabled) return false; e.click(); return true; })()`);
const text = (sel) => ev(`${q(sel)}?.textContent ?? null`);
const T = lang === 'tr';
const desktop = mode === 'desktop';
const QUICK = process.env.QUICK === '1';
const steps = () => ev(`[...document.querySelectorAll('[data-fpga-build-step]')].map(e => e.getAttribute('data-fpga-build-step') + ':' + e.getAttribute('data-state')).join(' ')`);
const msg = () => ev(`(() => { const m = ${q('[data-fpga-build-message]')}; return m ? m.getAttribute('data-fpga-build-message') + '|' + m.textContent : null; })()`);
const hint = () => text('[data-fpga-build-hint]');
const idle = (ms) => waitFor(`!document.querySelector('[data-fpga-build-cancel]') && !!document.querySelector('[data-fpga-build-message]')`, ms);
const logText = () => text('[data-fpga-build-log]');
const activeFlow = () => ev(`[...document.querySelectorAll('[data-fpga-build-flow]')].filter(b => b.className.includes('bg-indigo-600')).map(b => b.getAttribute('data-fpga-build-flow')).join(',')`);
const hwServer = () => /^"(?:hw_server|cs_server)\.exe",/im.test(execFileSync('tasklist', ['/FO', 'CSV', '/NH'], { encoding: 'latin1' }));

async function openApp() {
  if (process.env.OPEN_URL) {
    await send('Page.navigate', { url: process.env.OPEN_URL });
    await sleep(2500);
  }
  await ev(`localStorage.setItem('lds.language', '${lang}')`);
  await send('Page.reload');
  await sleep(3000);
  await waitFor(`!!document.querySelector('svg')`);
  // Right after a reload the app may still restore its autosave and re-render, which can swallow the first
  // click: try until the HDL window's FPGA tab is there
  const fpgaTab = `[...document.querySelectorAll('button')].find(b => b.textContent.trim() === ${JSON.stringify(T ? 'FPGA projesi' : 'FPGA project')})`;
  let opened = false;
  for (let i = 0; i < 6 && !opened; i++) {
    await ev(`(() => { const b = [...document.querySelectorAll('button')].find(b => (b.title||'').includes('Verilog')); if (b) b.click(); })()`);
    opened = await waitFor(`!!${fpgaTab}`, 2500);
  }
  ok(opened, 'open HDL modal');
  ok(await ev(`(() => { const b = ${fpgaTab}; if (!b) return false; b.click(); return true; })()`), 'FPGA tab');
  await waitFor(`!!document.querySelector('[data-fpga-open]')`);
  await click('[data-fpga-open]');
  ok(await waitFor(`!!document.querySelector('[data-fpga-dialog]')`), 'map dialog');
}

/** Picks a board in the map dialog, suggests a mapping and opens the build tab */
async function pickBoard(name) {
  await click('[data-fpga-tab="map"]');
  await sleep(300);
  await ev(`(() => { const s = ${q('[data-fpga-board-select]')}; Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(s, ${JSON.stringify(name)}); s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
  ok(await waitFor(`!!document.querySelector('[data-fpga-board=${JSON.stringify(name)}]')`), `board ${name}`);
  await sleep(400);
  // A fresh web profile opens an empty circuit, where there is nothing to suggest; the web checks need no mapping
  const suggested = await click('[data-fpga-suggest]');
  if (desktop) ok(suggested, `suggest on ${name}`);
  await sleep(300);
  await click('[data-fpga-tab="build"]');
  await sleep(700);
}

// Start from no remembered choice
await ev(`localStorage.removeItem('lds.fpga.flowChoice')`);
await openApp();
await pickBoard('BASYS3');

if (!desktop) {
  ok(!(await has('[data-fpga-build-flow]')), 'web: no flow choice');
  ok(!(await has('[data-fpga-vendor-tools]')), 'web: no vendor tools section');
  await pickBoard('DE10-LITE');
  const blocked = await text('[data-fpga-build-blocked]');
  ok(!!blocked && blocked.includes(T ? 'yalnız masaüstü' : 'only in the desktop app'), 'web: Quartus board says desktop only', blocked);
  ok(!(await has('[data-fpga-vendor-tools]')), 'web: no section on a Quartus board');
  await pickBoard('BASYS2');
  const blocked2 = await text('[data-fpga-build-blocked]');
  ok(!!blocked2 && blocked2.includes(T ? 'yalnız masaüstü' : 'only in the desktop app'), 'web: ISE board says desktop only', blocked2);
  await shot(`${prefix}_${lang}_web.png`);
} else {
  // --- the flow choice on BASYS3 ------------------------------------------------------------------------------
  // the choice appears once the panel knows which tools are installed
  ok(await waitFor(`!!document.querySelector('[data-fpga-build-flow="open"]') && !!document.querySelector('[data-fpga-build-flow="vendor"]')`, 30000), 'BASYS3: flow choice shown');
  ok((await activeFlow()) === 'open', 'BASYS3: open flow by default', await activeFlow());
  ok((await text('[data-fpga-build-flow="open"]'))?.includes('openXC7') && (await text('[data-fpga-build-flow="vendor"]')) === 'Vivado', 'choice labels');
  ok(await has('[data-fpga-build-detect]') && !(await has('[data-fpga-build-vendor-note]')), 'open flow: detect button, no vendor note');
  // --- the vendor tools section --------------------------------------------------------------------------------
  ok(await has('[data-fpga-vendor-tools][data-open="false"]'), 'section collapsed at first');
  ok(await click('[data-fpga-vendor-toggle]'), 'open the section');
  ok(await waitFor(`!!document.querySelector('[data-fpga-vendor-kind="vivado"][data-found="true"]')`, 10000), 'Vivado listed as found');
  const order = await ev(`[...document.querySelectorAll('[data-fpga-vendor-kind]')].map(e => e.getAttribute('data-fpga-vendor-kind')).join(',')`);
  ok(order === 'vivado,quartus,quartusLegacy,ise', 'kinds listed, the board\'s first', order);
  const found = await ev(`[...document.querySelectorAll('[data-fpga-vendor-kind]')].map(e => e.getAttribute('data-fpga-vendor-kind') + '=' + e.getAttribute('data-found')).join(',')`);
  ok(found === 'vivado=true,quartus=true,quartusLegacy=true,ise=true', 'all four installs found on this machine', found);
  const inst = await text('[data-fpga-vendor-kind="vivado"] [data-fpga-vendor-install]');
  ok(!!inst && inst.includes('2026.1') && /vivado\.bat/i.test(inst), 'Vivado install line: version and exe', inst);
  ok(await has('[data-fpga-vendor-choose]'), 'choose folder button');
  ok(await click('[data-fpga-vendor-check="vivado"]'), 'check Vivado');
  ok(await waitFor(`!!document.querySelector('[data-fpga-vendor-kind="vivado"] [data-fpga-vendor-check-note]')`, 120000), 'Vivado check finished');
  const note = await ev(`${q('[data-fpga-vendor-kind="vivado"] [data-fpga-vendor-check-note]')}.getAttribute('data-fpga-vendor-check-note') + '|' + ${q('[data-fpga-vendor-kind="vivado"] [data-fpga-vendor-check-note]')}.textContent`);
  ok(note.startsWith('ok|') && /vivado v2026\.1/i.test(note), 'Vivado check ok', note);
  ok(await click('[data-fpga-vendor-check="ise"]'), 'check ISE');
  ok(await waitFor(`!!document.querySelector('[data-fpga-vendor-kind="ise"] [data-fpga-vendor-check-note]')`, 120000), 'ISE check finished');
  const iseNote = await text('[data-fpga-vendor-kind="ise"] [data-fpga-vendor-check-note]');
  ok(!!iseNote, 'ISE check note', iseNote);
  await shot(`${prefix}_${lang}_1_section.png`);

  // --- choose Vivado; remembered across a reload ---------------------------------------------------------------
  ok(await click('[data-fpga-build-flow="vendor"]'), 'choose Vivado');
  await sleep(500);
  ok((await activeFlow()) === 'vendor', 'Vivado active', await activeFlow());
  const vnote = await text('[data-fpga-build-vendor-note]');
  ok(!!vnote && vnote.includes(T ? 'Açık kaynak akış da' : 'The open-source flow can build it too'), 'chosen-Vivado note', vnote);
  ok(!(await has('[data-fpga-build-detect]')), 'Vivado flow: no detect button');
  ok(!(await has('[data-fpga-build-no-vendor]')), 'Vivado found: no "not found" note');
  ok((await ev(`localStorage.getItem('lds.fpga.flowChoice')`)) === '{"BASYS3":"vendor"}', 'stored per board', await ev(`localStorage.getItem('lds.fpga.flowChoice')`));
  await openApp();
  await pickBoard('BASYS3');
  ok((await activeFlow()) === 'vendor', 'Vivado still chosen after a reload', await activeFlow());

  const hwBefore = hwServer();
  if (!QUICK) {
    // --- build and program with Vivado -------------------------------------------------------------------------
    ok(await click('[data-fpga-build-run="build"]'), 'Vivado build click');
    ok(await idle(600000), 'Vivado build finishes');
    let m = await msg();
    ok(m?.startsWith('ok|'), 'Vivado build ok', { m, steps: await steps(), log: (await logText())?.slice(-1500) });
    ok(/^prepare:done vendorBuild:done$/.test(await steps()), 'Vivado steps', await steps());
    ok(await click('[data-fpga-build-program]'), 'program with Vivado');
    ok(await idle(300000), 'Vivado program finishes');
    m = await msg();
    ok(m?.startsWith('error|') && m.includes('hw_server'), 'Vivado program: no cable', m);
    ok((await logText()).includes('vivado --step program'), 'log: vivado program');
    await shot(`${prefix}_${lang}_2_vivado.png`);

    // --- back to openFPGALoader with hw_server left running: the hint --------------------------------------------
    ok(await click('[data-fpga-build-flow="open"]'), 'back to the open flow');
    await sleep(500);
    const hwNow = hwServer();
    ok(hwNow, 'Vivado left hw_server running', hwNow);
    ok(await click('[data-fpga-build-detect]'), 'detect with openFPGALoader');
    ok(await idle(60000), 'detect finishes');
    m = await msg();
    const h = await hint();
    ok(m?.startsWith('error|') && !!h && h.includes('hw_server.exe') && h.includes(T ? 'hâlâ çalışıyor' : 'still running'), 'hw_server hint shown', { m, h });
    await shot(`${prefix}_${lang}_3_hwserver.png`);
    // The app only looks; this test stops the hw_server its own Vivado run left (not one that ran before)
    if (!hwBefore) {
      for (const im of ['hw_server.exe', 'cs_server.exe']) {
        try {
          execFileSync('taskkill', ['/IM', im, '/F'], { stdio: 'ignore' });
        } catch {
          // not running
        }
      }
      await sleep(1500);
      ok(!hwServer(), 'hw_server stopped by the test');
      ok(await click('[data-fpga-build-detect]'), 'detect again');
      ok(await idle(60000), 'detect again finishes');
      ok(!(await has('[data-fpga-build-hint]')), 'no hw_server hint once it is gone', await hint());
    }
  } else {
    ok(await click('[data-fpga-build-flow="open"]'), 'back to the open flow');
    await sleep(500);
  }
  ok((await activeFlow()) === 'open' && (await ev(`localStorage.getItem('lds.fpga.flowChoice')`)) === '{"BASYS3":"open"}', 'open stored');

  // --- boards with one flow -----------------------------------------------------------------------------------------
  await pickBoard('DIGILENT_CMOD_A7_15T');
  ok(!(await has('[data-fpga-build-flow]')), 'CMOD A7-15T: no choice (Vivado only)');
  const cnote = await text('[data-fpga-build-vendor-note]');
  ok(!!cnote && cnote.includes(T ? 'derleyemiyor' : 'cannot build'), 'CMOD: Vivado-only note', cnote);
  await pickBoard('DE10-LITE');
  ok(!(await has('[data-fpga-build-flow]')), 'Quartus board: no choice');
  ok(await click('[data-fpga-vendor-toggle]'), 'Quartus board: open the section');
  await waitFor(`!!document.querySelector('[data-fpga-vendor-kind]')`, 10000);
  const qorder = await ev(`[...document.querySelectorAll('[data-fpga-vendor-kind]')].map(e => e.getAttribute('data-fpga-vendor-kind')).join(',')`);
  ok(qorder === 'quartus,quartusLegacy,vivado,ise', 'Quartus board: Quartus kinds first', qorder);
  await pickBoard('BASYS2');
  ok(!(await has('[data-fpga-build-flow]')), 'ISE board: no choice');
  ok(await click('[data-fpga-vendor-toggle]'), 'ISE board: open the section');
  await waitFor(`!!document.querySelector('[data-fpga-vendor-kind]')`, 10000);
  ok((await ev(`[...document.querySelectorAll('[data-fpga-vendor-kind]')].map(e => e.getAttribute('data-fpga-vendor-kind'))[0]`)) === 'ise', 'ISE board: ISE first');
  await shot(`${prefix}_${lang}_4_ise.png`);
  await pickBoard('GECKO5_EDUCATION');
  ok(!(await has('[data-fpga-build-flow]')) && !(await has('[data-fpga-vendor-tools]')), 'GECKO5: no choice, no section');
}

await ev(`localStorage.removeItem('lds.fpga.flowChoice')`);
console.log(`vendor_click ${lang} ${mode}: ${pass} passed, ${fail} failed (screens in ${OUT_DIR})`);
close();
process.exit(fail ? 1 : 0);
