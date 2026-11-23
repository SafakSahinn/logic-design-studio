// Minimal Chrome DevTools Protocol client for the FPGA UI click tests (Node 22+, built-in WebSocket).
// CDP_PORT selects the debugging port: Electron started with --remote-debugging-port, or a Chrome instance.
import { mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const PORT = process.env.CDP_PORT ?? 9345;

/** Where screenshots, downloads and the localStorage backup go */
export const OUT_DIR = process.env.OUT_DIR ?? join(tmpdir(), 'lds-fpga-ui');
mkdirSync(OUT_DIR, { recursive: true });

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function wire(url) {
  const ws = new WebSocket(url);
  let id = 0;
  const pending = new Map();
  const logs = [];
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      pending.get(m.id)(m);
      pending.delete(m.id);
    } else if (m.method === 'Runtime.exceptionThrown') logs.push('EXC ' + JSON.stringify(m.params.exceptionDetails).slice(0, 600));
    else if (m.method === 'Runtime.consoleAPICalled' && (m.params.type === 'error' || m.params.type === 'warning'))
      logs.push(m.params.type + ' ' + m.params.args.map((a) => a.value ?? a.description).join(' ').slice(0, 400));
  };
  const send = (method, params = {}) =>
    new Promise((res) => {
      const i = ++id;
      pending.set(i, res);
      ws.send(JSON.stringify({ id: i, method, params }));
    });
  return { ws, send, logs, opened: new Promise((r) => (ws.onopen = r)) };
}

/** Connects to the first page whose URL contains urlPart (any page when none does) */
export async function connect(urlPart = '') {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const page = list.find((t) => t.type === 'page' && t.url.includes(urlPart)) ?? list.find((t) => t.type === 'page');
  if (!page) throw new Error(`no page on CDP port ${PORT}`);
  const { ws, send, logs, opened } = wire(page.webSocketDebuggerUrl);
  await opened;
  await send('Runtime.enable');
  await send('Page.enable');
  const ev = async (expression) => {
    const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (r.result?.exceptionDetails) return 'EXCEPTION: ' + (r.result.exceptionDetails.exception?.description ?? JSON.stringify(r.result.exceptionDetails)).slice(0, 800);
    return r.result?.result?.value;
  };
  const shot = async (name) => {
    const r = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(join(OUT_DIR, name), Buffer.from(r.result.data, 'base64'));
  };
  return { send, ev, shot, logs, close: () => ws.close() };
}

/** The browser-level target (Browser.* methods, e.g. download behaviour in headless Chrome) */
export async function connectBrowser() {
  const v = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
  const { ws, send, opened } = wire(v.webSocketDebuggerUrl);
  await opened;
  return { send, close: () => ws.close() };
}

/** Polls a page expression until it is truthy (or the time runs out) and returns its last value */
export function waiter(ev) {
  return async (expr, ms = 10000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) {
      const v = await ev(expr);
      if (v && !(typeof v === 'string' && v.startsWith('EXCEPTION'))) return v;
      await sleep(200);
    }
    return ev(expr);
  };
}
