const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const { pathToFileURL } = require('url');

const fs = require('fs');
const { createTelnetHub } = require('./telnetServer.cjs');
const { createToolRunner } = require('./toolRunner.cjs');
const distHtml = path.join(__dirname, '../dist/index.html');
const isDev = process.env.NODE_ENV === 'development' || (!app.isPackaged && !fs.existsSync(distHtml));

// Performance optimizations for instant startup
app.commandLine.appendSwitch('high-dpi-support', '1');
app.commandLine.appendSwitch('force-device-scale-factor', '1');

let mainWindow = null;

// The window shows only the app itself. Any other URL (a link, a redirect, injected script) would inherit the
// preload bridges, so navigation away and new windows are refused.
const DEV_URL = 'http://localhost:5173';
const appFileUrl = pathToFileURL(distHtml).href;
function isAppUrl(url) {
  if (typeof url !== 'string') return false;
  if (isDev) return url === DEV_URL || url.startsWith(`${DEV_URL}/`);
  return url === appFileUrl || url.startsWith(`${appFileUrl}#`) || url.startsWith(`${appFileUrl}?`);
}

// App-wide settings (not part of any circuit file): userData/lds-settings.json
const settingsFile = () => path.join(app.getPath('userData'), 'lds-settings.json');
function readSettings() {
  try {
    const s = JSON.parse(fs.readFileSync(settingsFile(), 'utf8'));
    return s && typeof s === 'object' ? s : {};
  } catch {
    return {};
  }
}
function writeSettings(patch) {
  const next = { ...readSettings(), ...patch };
  try {
    fs.mkdirSync(path.dirname(settingsFile()), { recursive: true });
    fs.writeFileSync(settingsFile(), JSON.stringify(next, null, 2));
  } catch {
    /* the setting still applies for this run */
  }
}

// Telnet parts (Aşama 5c-2b): TCP servers in this process, bytes to and from the page over IPC
const toPage = (channel, payload) => {
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send(channel, payload);
};
const telnet = createTelnetHub({
  onRx: (port, bytes) => toPage('lds-net:rx', { port, bytes: new Uint8Array(bytes) }),
  onStatus: (status) => toPage('lds-net:status', status),
});
const fromPage = (e) => mainWindow && e.sender === mainWindow.webContents;
ipcMain.on('lds-net:hello', (e) => {
  // a (re)loaded page starts without parts: servers held by the previous page are released
  if (fromPage(e)) {
    telnet.closeAll();
    tools.cancelAll();
  }
});
ipcMain.on('lds-net:open', (e, msg) => {
  if (fromPage(e) && msg) telnet.open(msg.id, msg.port, msg.telnetMode);
});
ipcMain.on('lds-net:close', (e, id) => {
  if (fromPage(e)) telnet.close(id);
});
ipcMain.on('lds-net:send', (e, msg) => {
  if (fromPage(e) && msg) telnet.send(msg.id, msg.bytes);
});
ipcMain.handle('lds-net:get-lan', () => telnet.getLan());
ipcMain.handle('lds-net:set-lan', (e, on) => {
  if (!fromPage(e)) return telnet.getLan();
  const lan = telnet.setLan(on === true);
  writeSettings({ telnetLan: lan });
  return lan;
});

// Chronogram log file (logging step c), after evolution's FilePanel + LogThread: the page picks a file through a save
// dialog (an existing non-empty file: overwrite / append / cancel) and appends text to it. Only files picked in this
// run can be written.
const logFiles = new Set();
ipcMain.handle('lds-log:choose', async (e, suggestedName) => {
  if (!fromPage(e)) return null;
  const r = await dialog.showSaveDialog(mainWindow, {
    title: 'Kayıt dosyası',
    defaultPath: typeof suggestedName === 'string' && suggestedName ? suggestedName : 'log.txt',
    filters: [
      { name: 'Metin dosyası (*.txt)', extensions: ['txt'] },
      { name: 'Tüm dosyalar', extensions: ['*'] },
    ],
  });
  if (r.canceled || !r.filePath) return null;
  const file = r.filePath;
  let stat = null;
  try {
    stat = fs.statSync(file);
  } catch {
    /* a new file */
  }
  if (stat && stat.isDirectory()) return { error: `“${path.basename(file)}” bir klasör.` };
  if (stat && stat.size > 0) {
    const { response } = await dialog.showMessageBox(mainWindow, {
      type: 'question',
      title: 'Dosya zaten var',
      message: `“${path.basename(file)}” dosyası zaten var.`,
      buttons: ['Üzerine yaz', 'Sona ekle', 'İptal'],
      defaultId: 0,
      cancelId: 2,
      noLink: true,
    });
    if (response === 2) return null;
    if (response === 0) {
      try {
        fs.writeFileSync(file, '');
      } catch {
        return { error: `“${path.basename(file)}” dosyasına yazma izniniz yok.` };
      }
    }
  }
  try {
    fs.appendFileSync(file, '');
  } catch {
    return { error: `“${path.basename(file)}” dosyasına yazma izniniz yok.` };
  }
  logFiles.add(file);
  return { path: file };
});
ipcMain.handle('lds-log:append', async (e, file, text) => {
  if (!fromPage(e) || !logFiles.has(file) || typeof text !== 'string') return false;
  try {
    await fs.promises.appendFile(file, text, 'utf8');
    return true;
  } catch {
    return false;
  }
});

// External EDA tools (Aşama 6.0c): see electron/toolRunner.cjs (allowlist, temp dir, limits) and src/tools/.
// The page names a tool id; this process alone maps it to an executable.
const tools = createToolRunner({
  readSettings,
  onProgress: (runId, progress) => toPage('lds-tool:progress', { runId, progress }),
  confirmRun: confirmToolRun,
});

// Texts of the main-process confirmation; the page's language setting only picks between them.
const CONFIRM_TEXT = {
  en: {
    title: 'Write to FPGA flash',
    message: 'Write the bitstream to the board’s flash memory?',
    detail: (file, kb) =>
      `${file} (${kb} KB) will be written to the board’s configuration flash for good and replace what is there. The board will start with this design every time it powers up.`,
    buttons: ['Write to flash', 'Cancel'],
  },
  tr: {
    title: 'FPGA flash belleğine yaz',
    message: 'Bitstream karttaki flash belleğe yazılsın mı?',
    detail: (file, kb) =>
      `${file} (${kb} KB) kartın yapılandırma flash belleğine kalıcı olarak yazılacak ve oradaki içeriğin yerini alacak. Kart her açılışta bu tasarımla başlayacak.`,
    buttons: ['Flash’a yaz', 'İptal'],
  },
};

async function pageLanguage() {
  try {
    const lang = await Promise.race([
      mainWindow.webContents.executeJavaScript("localStorage.getItem('lds.language')"),
      new Promise((resolve) => setTimeout(() => resolve(null), 500)),
    ]);
    if (lang === 'tr' || lang === 'en') return lang;
  } catch {
    /* fall back to the page's own default */
  }
  // The page does not follow the system language either (src/i18n DEFAULT_LANGUAGE)
  return 'en';
}

/**
 * Asks the user before a tool run that changes the board for good (toolRunner confirmRun). A native dialog: the
 * page cannot draw, hide or click it. "Cancel" is the default button.
 */
async function confirmToolRun({ kind, file, bytes, signal }) {
  if (kind !== 'flashWrite' || !mainWindow || mainWindow.isDestroyed() || signal?.aborted) return false;
  const text = CONFIRM_TEXT[await pageLanguage()];
  if (signal?.aborted) return false;
  const { response } = await dialog.showMessageBox(mainWindow, {
    type: 'warning',
    title: text.title,
    message: text.message,
    detail: text.detail(String(file), Math.max(1, Math.round(Number(bytes) / 1024))),
    buttons: text.buttons,
    defaultId: 1,
    cancelId: 1,
    noLink: true,
    // The run was cancelled (Cancel button, page reload) while the question is open: close it
    signal,
  });
  return response === 0;
}
// Tool requests are accepted only from the app's own top-level page, never from an iframe or a foreign URL.
const fromAppFrame = (e) => fromPage(e) && e.senderFrame === mainWindow.webContents.mainFrame && isAppUrl(e.senderFrame.url);
ipcMain.handle('lds-tool:probe', (e, tool) => (fromAppFrame(e) ? tools.probe(String(tool)) : { available: false, reason: 'not-installed' }));
ipcMain.handle('lds-tool:run', (e, req) => (fromAppFrame(e) ? tools.run(req) : { error: { kind: 'bad-request', message: 'Not from the app page' } }));
ipcMain.handle('lds-tool:cancel', (e, runId) => (fromAppFrame(e) ? tools.cancel(String(runId)) : false));

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'LogicDesign Studio — Digital Circuit CAD & Simulator',
    backgroundColor: '#ffffff',
    show: false, // Prevents white/black flicker before DOM paints
    autoHideMenuBar: true,
    webPreferences: {
      backgroundThrottling: false, // Ensures simulation and clock ticks stay smooth
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!isAppUrl(url)) event.preventDefault();
  });
  mainWindow.webContents.on('will-redirect', (event, url) => {
    if (!isAppUrl(url)) event.preventDefault();
  });
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));

  // Remove default menu bar for modern clean CAD ribbon UI
  Menu.setApplicationMenu(null);

  // Show window as soon as content is parsed
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    telnet.closeAll();
    tools.cancelAll();
    mainWindow = null;
  });

  if (isDev) {
    mainWindow.loadURL(DEV_URL);
  } else {
    mainWindow.loadFile(distHtml);
  }
}

app.whenReady().then(() => {
  telnet.setLan(readSettings().telnetLan === true);
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  telnet.closeAll();
  tools.cancelAll();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
