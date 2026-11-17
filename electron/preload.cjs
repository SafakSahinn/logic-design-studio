const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  isDesktop: true,
  platform: process.platform,
});

// Telnet parts (Aşama 5c-2b): see src/utils/telnetNet.ts (LdsNet) and electron/telnetServer.cjs
ipcRenderer.send('lds-net:hello');
const listen = (channel, wrap) => (cb) => {
  if (typeof cb !== 'function') return () => {};
  const handler = (_e, payload) => wrap(cb, payload);
  ipcRenderer.on(channel, handler);
  return () => ipcRenderer.removeListener(channel, handler);
};
contextBridge.exposeInMainWorld('ldsNet', {
  open: (id, port, telnetMode) => ipcRenderer.send('lds-net:open', { id: String(id), port: Number(port), telnetMode: telnetMode === true }),
  close: (id) => ipcRenderer.send('lds-net:close', String(id)),
  send: (id, bytes) => ipcRenderer.send('lds-net:send', { id: String(id), bytes: Array.from(bytes, (b) => Number(b) & 0xff) }),
  onRx: listen('lds-net:rx', (cb, p) => cb(p.port, Array.from(p.bytes))),
  onStatus: listen('lds-net:status', (cb, p) => cb(p)),
  getLan: () => ipcRenderer.invoke('lds-net:get-lan'),
  setLan: (on) => ipcRenderer.invoke('lds-net:set-lan', on === true),
});

// Chronogram log file (logging step c): see src/components/useChronoLogFile.ts and electron/main.cjs
contextBridge.exposeInMainWorld('ldsLog', {
  choose: (suggestedName) => ipcRenderer.invoke('lds-log:choose', String(suggestedName ?? '')),
  append: (file, text) => ipcRenderer.invoke('lds-log:append', String(file), String(text)),
});

// External EDA tools (Aşama 6.0c): see src/tools/nativeBackend.ts and electron/toolRunner.cjs.
// Only plain data crosses: strings, string arrays, and file maps of string or Uint8Array.
const plainFiles = (files) => {
  const out = {};
  if (files && typeof files === 'object') {
    for (const [name, data] of Object.entries(files)) {
      out[String(name)] = data instanceof Uint8Array ? new Uint8Array(data) : String(data);
    }
  }
  return out;
};
contextBridge.exposeInMainWorld('ldsTool', {
  probe: (tool) => ipcRenderer.invoke('lds-tool:probe', String(tool)),
  run: (req) =>
    ipcRenderer.invoke('lds-tool:run', {
      runId: String(req && req.runId),
      tool: String(req && req.tool),
      args: Array.isArray(req && req.args) ? req.args.map(String) : [],
      files: plainFiles(req && req.files),
      outputs: Array.isArray(req && req.outputs) ? req.outputs.map(String) : [],
      timeoutMs: Number(req && req.timeoutMs) || 0,
    }),
  cancel: (runId) => ipcRenderer.invoke('lds-tool:cancel', String(runId)),
  onProgress: listen('lds-tool:progress', (cb, p) => cb(p.runId, p.progress)),
});
