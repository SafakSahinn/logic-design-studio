// Telnet part TCP servers (Aşama 5c-2b), after Logisim-evolution's TelnetServer + ServerHolder:
// - one server per port, shared by every Telnet part that uses it (holders counted; the last one closes it)
// - the newest client receives what the circuit sends; every client's bytes reach the circuit
// - telnet mode: on connect the server sends IAC WILL SGA, IAC WILL ECHO and drops IAC <command> <option> from
//   the input (evolution reads exactly two bytes after IAC, so does this; nothing is escaped on output)
// - bound to 127.0.0.1 unless the app-wide network setting asks for 0.0.0.0
// Plain Node (no Electron), so it can be tested on its own.
'use strict';

const net = require('net');

const IAC = 255;
const WILL = 251;
const SGA = 3;
const ECHO = 1;
const MAX_CLIENTS = 8; // per port; more connections are closed at once
const MAX_PENDING = 1 << 20; // received bytes waiting for the next flush; the rest is dropped
const MAX_UNSENT = 1 << 20; // bytes queued for a client that does not read; further sends are dropped
const FLUSH_MS = 10; // received bytes are passed on in batches, not one event per TCP chunk

function validPort(port) {
  return Number.isInteger(port) && port >= 1 && port <= 65535;
}

/**
 * @param {{ onRx: (port: number, bytes: Buffer) => void, onStatus: (status: object) => void }} hooks
 */
function createTelnetHub(hooks) {
  let lan = false;
  /** port -> { server, host, listening, error, clients: Set<Client>, newest, holders: Map<id, telnetMode>, pending: Buffer[], pendingLen, timer } */
  const ports = new Map();
  /** holder id -> port */
  const holderPort = new Map();

  const host = () => (lan ? '0.0.0.0' : '127.0.0.1');
  const escapeOn = (entry) => [...entry.holders.values()].some(Boolean);

  function status(port, entry) {
    hooks.onStatus({
      port,
      host: entry.host,
      listening: entry.listening,
      clients: entry.clients.size,
      error: entry.error,
    });
  }

  function flush(port, entry) {
    entry.timer = null;
    if (entry.pendingLen === 0) return;
    const bytes = Buffer.concat(entry.pending, entry.pendingLen);
    entry.pending = [];
    entry.pendingLen = 0;
    hooks.onRx(port, bytes);
  }

  function received(port, entry, bytes) {
    if (bytes.length === 0) return;
    const room = MAX_PENDING - entry.pendingLen;
    if (room <= 0) return;
    const part = bytes.length > room ? bytes.subarray(0, room) : bytes;
    entry.pending.push(part);
    entry.pendingLen += part.length;
    if (!entry.timer) entry.timer = setTimeout(() => flush(port, entry), FLUSH_MS);
  }

  function accept(port, entry, socket) {
    if (entry.clients.size >= MAX_CLIENTS) {
      socket.destroy();
      return;
    }
    const client = { socket, skip: 0 };
    entry.clients.add(client);
    entry.newest = client;
    socket.setNoDelay(true);
    socket.on('error', () => {}); // a reset connection just ends
    if (escapeOn(entry)) socket.write(Buffer.from([IAC, WILL, SGA, IAC, WILL, ECHO]));
    socket.on('data', (chunk) => {
      if (!escapeOn(entry)) {
        received(port, entry, chunk);
        return;
      }
      const out = [];
      for (const b of chunk) {
        if (client.skip > 0) client.skip--;
        else if (b === IAC) client.skip = 2;
        else out.push(b);
      }
      received(port, entry, Buffer.from(out));
    });
    socket.on('close', () => {
      entry.clients.delete(client);
      if (entry.newest === client) entry.newest = [...entry.clients].pop() ?? null;
      if (ports.get(port) === entry) status(port, entry);
    });
    status(port, entry);
  }

  function listen(port, entry) {
    entry.host = host();
    entry.listening = false;
    entry.error = undefined;
    const server = net.createServer((socket) => accept(port, entry, socket));
    entry.server = server;
    server.on('error', (err) => {
      if (entry.server !== server) return;
      entry.listening = false;
      entry.error = (err && err.code) || String(err);
      status(port, entry);
    });
    server.listen({ port, host: entry.host, exclusive: true }, () => {
      if (entry.server !== server) return;
      entry.listening = true;
      status(port, entry);
    });
  }

  function shutdown(entry) {
    if (entry.timer) clearTimeout(entry.timer);
    entry.timer = null;
    entry.pending = [];
    entry.pendingLen = 0;
    for (const c of entry.clients) c.socket.destroy();
    entry.clients.clear();
    entry.newest = null;
    const server = entry.server;
    entry.server = null;
    if (server) server.close();
  }

  function close(id) {
    const port = holderPort.get(id);
    if (port === undefined) return;
    holderPort.delete(id);
    const entry = ports.get(port);
    if (!entry) return;
    entry.holders.delete(id);
    if (entry.holders.size === 0) {
      shutdown(entry);
      ports.delete(port);
      hooks.onStatus({ port, host: entry.host, listening: false, clients: 0, closed: true });
    }
  }

  function open(id, port, telnetMode) {
    if (typeof id !== 'string' || id.length === 0 || id.length > 200 || !validPort(port)) return;
    if (holderPort.get(id) !== port) close(id);
    holderPort.set(id, port);
    let entry = ports.get(port);
    if (!entry) {
      entry = { server: null, host: host(), listening: false, error: undefined, clients: new Set(), newest: null, holders: new Map(), pending: [], pendingLen: 0, timer: null };
      ports.set(port, entry);
      entry.holders.set(id, telnetMode === true);
      listen(port, entry);
      return;
    }
    entry.holders.set(id, telnetMode === true);
    status(port, entry);
  }

  function send(id, bytes) {
    const port = holderPort.get(id);
    const entry = port === undefined ? undefined : ports.get(port);
    if (!entry || !entry.newest || !Array.isArray(bytes) || bytes.length === 0) return;
    // a client that stops reading does not make the app hold its output without limit
    if (entry.newest.socket.writableLength > MAX_UNSENT) return;
    const out = Buffer.alloc(Math.min(bytes.length, 65536));
    for (let i = 0; i < out.length; i++) out[i] = Number(bytes[i]) & 0xff;
    entry.newest.socket.write(out);
  }

  /** app-wide network setting: every open server listens again on the new address (clients are dropped) */
  function setLan(on) {
    const next = on === true;
    if (next === lan) return lan;
    lan = next;
    for (const [port, entry] of ports) {
      shutdown(entry);
      listen(port, entry);
      status(port, entry);
    }
    return lan;
  }

  function closeAll() {
    for (const id of [...holderPort.keys()]) close(id);
  }

  return { open, close, send, setLan, getLan: () => lan, closeAll, _ports: ports };
}

module.exports = { createTelnetHub, validPort };
