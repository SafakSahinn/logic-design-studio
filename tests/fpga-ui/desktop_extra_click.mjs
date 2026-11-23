// Desktop-only checks added in Aşama 6j-5 (code-review fixes). Run after build_click.mjs in the same app.
//   1. The build panel stays mounted across the dialog's tabs: the built bitstream and the log survive a look at
//      the map tab.
//   2. Flash target: the Cancel button is disabled while the flash write runs (the native question is open).
//   3. Reloading the page while the native flash question is open closes the question and frees openFPGALoader,
//      so the new page can run it at once (it used to fail with "already running").
// There is no board on the test machine, so nothing can be written even if the question were answered "yes".
//
// usage: CDP_PORT=9345 [OUT_DIR=...] node desktop_extra_click.mjs <tr|en>
import { connect, sleep, waiter } from './cdp.mjs';

const [lang = 'tr'] = process.argv.slice(2);
const T = lang === 'tr';
let s = await connect('localhost');
let waitFor = waiter(s.ev);
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
const click = (sel) => s.ev(`(() => { const e = ${q(sel)}; if (!e || e.disabled) return false; e.click(); return true; })()`);
const msg = () => s.ev(`(() => { const m = ${q('[data-fpga-build-message]')}; return m ? m.getAttribute('data-fpga-build-message') + '|' + m.textContent : null; })()`);
const idle = (ms) => waitFor(`!document.querySelector('[data-fpga-build-cancel]') && !!document.querySelector('[data-fpga-build-message]')`, ms);

async function openBuildTab() {
  await s.ev(`localStorage.setItem('lds.language', '${lang}')`);
  await s.send('Page.reload');
  await sleep(3000);
  await waitFor(`!!document.querySelector('svg')`);
  await s.ev(`[...document.querySelectorAll('button')].find(b => (b.title||'').includes('Verilog'))?.click()`);
  await sleep(800);
  await s.ev(`[...document.querySelectorAll('button')].find(b => b.textContent.trim() === ${JSON.stringify(T ? 'FPGA projesi' : 'FPGA project')})?.click()`);
  await waitFor(`!!document.querySelector('[data-fpga-open]')`);
  await click('[data-fpga-open]');
  await waitFor(`!!document.querySelector('[data-fpga-dialog]')`);
  await s.ev(`(() => { const e = ${q('[data-fpga-board-select]')}; Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(e, 'GECKO5_EDUCATION'); e.dispatchEvent(new Event('change', { bubbles: true })); })()`);
  await waitFor(`!!document.querySelector('[data-fpga-board="GECKO5_EDUCATION"]')`);
  await sleep(400);
  await click('[data-fpga-suggest]');
  await sleep(300);
  await click('[data-fpga-tab="build"]');
  return waitFor(`!!document.querySelector('[data-fpga-build-run="build"]')`);
}

// --- 1. panel kept across tabs --------------------------------------------------------------------------------
ok(await openBuildTab(), 'build tab open');
await click('[data-fpga-build-run="build"]');
ok(await idle(180000), 'build finishes');
ok((await msg())?.startsWith('ok|'), 'build ok', await msg());
const logBefore = await s.ev(`${q('[data-fpga-build-log]')}.textContent.length`);
await click('[data-fpga-tab="map"]');
await sleep(400);
ok(await s.ev(`${q('[data-fpga-build]')}?.closest('.hidden') !== null`), 'panel hidden (not unmounted) on the map tab');
await click('[data-fpga-tab="build"]');
await sleep(300);
ok((await msg())?.startsWith('ok|'), 'result message kept after the tab switch', await msg());
ok((await s.ev(`${q('[data-fpga-build-log]')}.textContent.length`)) === logBefore, 'log kept after the tab switch');
ok(!(await s.ev(`${q('[data-fpga-build-program]')}.disabled`)), 'bitstream still usable after the tab switch');

// --- 2./3. flash question: Cancel disabled, reload closes the question -----------------------------------------
await click('[data-fpga-build-target="flash"]');
ok(await click('[data-fpga-build-program]'), 'program (flash) clicked');
ok(await waitFor(`!!document.querySelector('[data-fpga-build-cancel]')`, 3000), 'busy while the native question is open');
await sleep(1500); // the question is up (native, cannot be seen from the page)
ok(await s.ev(`${q('[data-fpga-build-cancel]')}.disabled`), 'Cancel disabled during a flash write');
ok((await s.ev(`${q('[data-fpga-build-cancel]')}.title`))?.length > 20, 'Cancel explains why', await s.ev(`${q('[data-fpga-build-cancel]')}.title`));
// Reload: the main process cancels every run of the old page (lds-net:hello -> cancelAll) -> question closed
await s.send('Page.reload');
s.close();
await sleep(3000);
s = await connect('localhost');
waitFor = waiter(s.ev);
ok(await openBuildTab(), 'build tab after reload');
await click('[data-fpga-build-detect]');
ok(await idle(60000), 'detect after reload finishes');
const m = await msg();
ok(m?.includes(T ? 'Programlama kablosu bulunamadı' : 'No programming cable'), 'openFPGALoader free again (no "already running")', m);
await click('[data-fpga-build-target="sram"]');

console.log(`extra ${lang}: ${pass} passed, ${fail} failed`);
s.close();
process.exit(fail ? 1 : 0);
