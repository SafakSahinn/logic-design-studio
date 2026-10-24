const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');

const fs = require('fs');
const distHtml = path.join(__dirname, '../dist/index.html');
const isDev = process.env.NODE_ENV === 'development' || (!app.isPackaged && !fs.existsSync(distHtml));

// Performance optimizations for instant startup
app.commandLine.appendSwitch('high-dpi-support', '1');
app.commandLine.appendSwitch('force-device-scale-factor', '1');

function createWindow() {
  const mainWindow = new BrowserWindow({
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

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
