import { BrowserWindow as e, Menu as t, app as n, dialog as r, ipcMain as i } from "electron";
import { spawn as a } from "child_process";
import * as o from "path";
import * as s from "net";
import { fileURLToPath as c } from "url";
import * as l from "fs";
//#region electron/main.ts
var u = c(import.meta.url), d = o.dirname(u), f = null, p = null;
function m() {
	return new Promise((e, t) => {
		let n = s.createServer();
		n.listen(0, "127.0.0.1", () => {
			let r = n.address(), i = typeof r == "object" && r ? r.port : null;
			n.close(() => {
				i ? e(i) : t(/* @__PURE__ */ Error("Could not find free port"));
			});
		});
	});
}
async function h(e) {
	let t = !!process.env.VITE_DEV_SERVER_URL, r = o.join(n.getAppPath(), "..", "backend");
	f = a(t ? o.join(r, ".venv", "Scripts", "uvicorn.exe") : o.join(process.resourcesPath, "backend", "backend.exe"), t ? [
		"api:app",
		"--port",
		String(e),
		"--host",
		"127.0.0.1"
	] : [
		"--port",
		String(e),
		"--host",
		"127.0.0.1"
	], {
		cwd: t ? r : void 0,
		stdio: "pipe",
		detached: !1
	}), f.stdout?.on("data", (e) => console.log("[backend]", e.toString())), f.stderr?.on("data", (e) => console.error("[backend]", e.toString())), await g(e);
}
function g(e, t = 40, n = 500) {
	return new Promise((r, i) => {
		let a = 0, o = () => {
			let c = s.createConnection({
				port: e,
				host: "127.0.0.1"
			});
			c.on("connect", () => {
				c.destroy(), r();
			}), c.on("error", () => {
				++a >= t ? i(/* @__PURE__ */ Error("Backend did not start in time")) : setTimeout(o, n);
			});
		};
		o();
	});
}
function _() {
	f &&= (f.kill(), null);
}
var v = void 0;
function y(e) {
	let t = o.extname(e).toLowerCase();
	return t === ".pdf" ? "application/pdf" : t === ".jpg" || t === ".jpeg" ? "image/jpeg" : t === ".png" ? "image/png" : t === ".webp" ? "image/webp" : "application/octet-stream";
}
i.handle("dialog:openFiles", async (e, t) => {
	let { canceled: n, filePaths: i } = await r.showOpenDialog({
		defaultPath: v,
		properties: t.multiSelections ? ["openFile", "multiSelections"] : ["openFile"],
		filters: t.filters ?? [{
			name: "All Files",
			extensions: ["*"]
		}]
	});
	return !n && i.length > 0 && (v = o.dirname(i[0])), n ? [] : i.map((e) => {
		let t = l.statSync(e);
		return {
			path: e,
			name: o.basename(e),
			size: t.size,
			type: y(e),
			isElectron: !0
		};
	});
}), i.handle("file:read", async (e, t) => {
	let n = await l.promises.readFile(t);
	return n.buffer.slice(n.byteOffset, n.byteOffset + n.byteLength);
}), console.log("appPath:", n.getAppPath()), n.whenReady().then(async () => {
	let r = await m();
	await h(r), i.handle("get-port", () => r), t.setApplicationMenu(null), p = new e({
		width: 1200,
		height: 800,
		frame: !1,
		titleBarStyle: "hidden",
		icon: o.join(n.getAppPath(), "..", "icon.png"),
		autoHideMenuBar: !0,
		menuBarVisible: !1,
		thickFrame: !1,
		webPreferences: {
			preload: o.join(d, "preload.mjs"),
			contextIsolation: !0,
			nodeIntegration: !1
		}
	}), p.maximize(), i.handle("titlebar:minimize", () => p?.minimize()), i.handle("titlebar:maximize", () => {
		p?.isMaximized() ? p.restore() : p?.maximize();
	}), i.handle("titlebar:close", () => p?.close()), p.webContents.on("did-finish-load", () => {
		p?.webContents.executeJavaScript(`window.__BACKEND_PORT__ = ${r}`);
	}), process.env.VITE_DEV_SERVER_URL ? p.loadURL(process.env.VITE_DEV_SERVER_URL) : p.loadFile("dist/index.html");
}), n.on("window-all-closed", () => {
	_(), process.platform !== "darwin" && n.quit();
}), n.on("before-quit", _);
//#endregion
