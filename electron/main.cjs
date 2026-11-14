const { app, BrowserWindow, Menu, ipcMain } = require('electron');
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
