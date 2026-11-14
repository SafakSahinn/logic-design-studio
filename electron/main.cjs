const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');

const fs = require('fs');
const { createTelnetHub } = require('./telnetServer.cjs');
const distHtml = path.join(__dirname, '../dist/index.html');
const isDev = process.env.NODE_ENV === 'development' || (!app.isPackaged && !fs.existsSync(distHtml));

// Performance optimizations for instant startup
app.commandLine.appendSwitch('high-dpi-support', '1');
app.commandLine.appendSwitch('force-device-scale-factor', '1');

let mainWindow = null;

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
  if (fromPage(e)) telnet.closeAll();
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

  // Remove default menu bar for modern clean CAD ribbon UI
  Menu.setApplicationMenu(null);

  // Show window as soon as content is parsed
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    telnet.closeAll();
    mainWindow = null;
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
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
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
