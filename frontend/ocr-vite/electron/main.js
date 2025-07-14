import { app, BrowserWindow } from 'electron';
import path from 'path';

function createWindow() {
	const win = new BrowserWindow({
		width: 800,
		height: 600,
	});

	// During development, load Vite server
	const isDev = !app.isPackaged;

	if (isDev) {
		win.loadURL('http://localhost:5173');
	} else {
		win.loadFile(path.join(__dirname, '../dist/index.html'));
	}

	// Uncomment this if you want to open DevTools by default
	// win.webContents.openDevTools();
}

app.whenReady().then(() => {
	createWindow();

	app.on('activate', () => {
		if (BrowserWindow.getAllWindows().length === 0) createWindow();
	});
});

app.on('window-all-closed', () => {
	if (process.platform !== 'darwin') app.quit();
});
