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
		close: () => electron.ipcRenderer.invoke("titlebar:close"),
		isMaximized: () => electron.ipcRenderer.invoke("titlebar:isMaximized"),
		onMaximizedChange: (callback) => {
			const listener = (_event, state) => callback(state);
			electron.ipcRenderer.on("window-maximized", listener);
			return () => {
				electron.ipcRenderer.removeListener("window-maximized", listener);
			};
		}
	},
	onFileSaved: (callback) => {
		const listener = (_event, filePath) => callback(filePath);
		electron.ipcRenderer.on("file-saved", listener);
		return () => {
			electron.ipcRenderer.removeListener("file-saved", listener);
		};
	},
	bookmarks: {
		read: (args) => electron.ipcRenderer.invoke("bookmarks:read", args),
		write: (args) => electron.ipcRenderer.invoke("bookmarks:write", args),
		extract: (args) => electron.ipcRenderer.invoke("bookmarks:extract", args)
	}
});
//#endregion
