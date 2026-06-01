let electron = require("electron");
//#region electron/preload.ts
electron.contextBridge.exposeInMainWorld("electron", { platform: process.platform });
electron.contextBridge.exposeInMainWorld("electronAPI", {
	openFiles: (options) => electron.ipcRenderer.invoke("dialog:openFiles", options),
	readFile: (filePath) => electron.ipcRenderer.invoke("file:read", filePath),
	getPort: () => electron.ipcRenderer.invoke("get-port"),
	getToken: () => electron.ipcRenderer.invoke("get-token"),
	titlebar: {
		minimize: () => electron.ipcRenderer.invoke("titlebar:minimize"),
		maximize: () => electron.ipcRenderer.invoke("titlebar:maximize"),
		close: () => electron.ipcRenderer.invoke("titlebar:close")
	}
});
//#endregion
