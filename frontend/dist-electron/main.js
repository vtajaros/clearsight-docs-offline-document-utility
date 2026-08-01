import { BrowserWindow as e, Menu as t, app as n, dialog as r, ipcMain as i, session as a } from "electron";
import { spawn as o } from "child_process";
import * as s from "path";
import * as c from "net";
import { fileURLToPath as l } from "url";
import * as u from "fs";
import * as d from "crypto";
//#region electron/main.ts
var f = d.randomUUID(), p = l(import.meta.url), m = s.dirname(p), h = null, g = null;
function _() {
	return new Promise((e, t) => {
		let n = c.createServer();
		n.listen(0, "127.0.0.1", () => {
			let r = n.address(), i = typeof r == "object" && r ? r.port : null;
			n.close(() => {
				i ? e(i) : t(/* @__PURE__ */ Error("Could not find free port"));
			});
		});
	});
}
async function v(e) {
	let t = !!process.env.VITE_DEV_SERVER_URL, r = s.join(n.getAppPath(), "..", "backend"), i = process.platform === "win32", a = i ? "Scripts" : "bin", c = i ? "python.exe" : "python3", l = i ? "backend.exe" : "backend";
	h = o(t ? s.join(r, ".venv", a, c) : s.join(process.resourcesPath, "backend", l), t ? [
		"-m",
		"uvicorn",
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
		env: {
			...process.env,
			CLEARSIGHT_API_TOKEN: f
		},
		stdio: "pipe",
		detached: !1
	}), h.on("error", (e) => {
		console.error("Failed to start backend process:", e);
	}), h.stdout?.on("data", (e) => console.log("[backend]", e.toString())), h.stderr?.on("data", (e) => console.error("[backend]", e.toString())), await y(e);
}
function y(e, t = 40, n = 500) {
	return new Promise((r, i) => {
		let a = 0, o = () => {
			let s = c.createConnection({
				port: e,
				host: "127.0.0.1"
			});
			s.on("connect", () => {
				s.destroy(), r();
			}), s.on("error", () => {
				++a >= t ? i(/* @__PURE__ */ Error("Backend did not start in time")) : setTimeout(o, n);
			});
		};
		o();
	});
}
function b() {
	if (h) {
		let e = h.pid;
		e && (process.platform === "win32" ? o("taskkill", [
			"/pid",
			String(e),
			"/t",
			"/f"
		], { stdio: "ignore" }) : h.kill("SIGTERM")), h = null;
	}
}
var x = void 0, S = /* @__PURE__ */ new Set();
function C(e) {
	let t = s.extname(e).toLowerCase();
	return t === ".pdf" ? "application/pdf" : t === ".jpg" || t === ".jpeg" ? "image/jpeg" : t === ".png" ? "image/png" : t === ".webp" ? "image/webp" : "application/octet-stream";
}
i.handle("dialog:openFiles", async (e, t) => {
	let { canceled: n, filePaths: i } = await r.showOpenDialog({
		defaultPath: x,
		properties: t.multiSelections ? ["openFile", "multiSelections"] : ["openFile"],
		filters: t.filters ?? [{
			name: "All Files",
			extensions: ["*"]
		}]
	});
	return !n && i.length > 0 && (x = s.dirname(i[0]), i.forEach((e) => S.add(e))), n ? [] : i.flatMap((e) => {
		let t;
		try {
			t = u.statSync(e);
		} catch {
			return [];
		}
		return [{
			path: e,
			name: s.basename(e),
			size: t.size,
			type: C(e),
			isElectron: !0,
			lastModified: t.mtimeMs,
			createdAt: t.birthtimeMs
		}];
	});
}), i.handle("file:read", async (e, t) => {
	if (!S.has(t)) throw Error(`Access denied: ${t} was not selected by the user.`);
	let n = await u.promises.readFile(t);
	return n.buffer.slice(n.byteOffset, n.byteOffset + n.byteLength);
}), n.whenReady().then(async () => {
	let r = await _();
	await v(r), i.handle("get-port", () => r), i.handle("get-token", () => f), t.setApplicationMenu(null), g = new e({
		width: 1200,
		height: 800,
		minWidth: 800,
		minHeight: 500,
		frame: !1,
		transparent: process.platform === "linux",
		titleBarStyle: "hidden",
		icon: s.join(n.getAppPath(), "..", "icon.png"),
		autoHideMenuBar: !0,
		webPreferences: {
			preload: s.join(m, "preload.mjs"),
			contextIsolation: !0,
			nodeIntegration: !1
		}
	}), g.maximize(), a.defaultSession.on("will-download", (e, t) => {
		t.on("done", (e, n) => {
			n === "completed" && g && !g.isDestroyed() && g.webContents.send("file-saved", t.getSavePath());
		});
	}), g.on("maximize", () => {
		g?.webContents.send("window-maximized", !0);
	}), g.on("unmaximize", () => {
		g?.webContents.send("window-maximized", !1);
	}), i.handle("titlebar:minimize", () => g?.minimize()), i.handle("titlebar:isMaximized", () => g?.isMaximized() ?? !1), i.handle("titlebar:maximize", () => {
		g?.isMaximized() ? g.restore() : g?.maximize();
	}), i.handle("titlebar:close", () => g?.close()), i.handle("bookmarks:read", async (e, { path: t }) => {
		let n = `http://127.0.0.1:${r}/bookmarks/read?path=${encodeURIComponent(t)}`, i = await fetch(n, { headers: { Authorization: `Bearer ${f}` } });
		if (!i.ok) {
			let e = await i.json().catch(() => ({}));
			throw Error(e.detail || `bookmarks:read failed: ${i.status}`);
		}
		return i.json();
	}), i.handle("bookmarks:write", async (e, { sourcePath: t, overwrite: i, bookmarks: a }) => {
		let o = s.join(n.getPath("temp"), `clearsight_bm_${Date.now()}_${s.basename(t)}`), c = await fetch(`http://127.0.0.1:${r}/bookmarks/write`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${f}`
			},
			body: JSON.stringify({
				source_path: t,
				output_path: o,
				bookmarks: a
			})
		});
		if (!c.ok) {
			let e = await c.json().catch(() => ({}));
			throw Error(e.detail || `bookmarks:write failed: ${c.status}`);
		}
		let l = await c.arrayBuffer(), d = Buffer.from(l);
		if (await u.promises.writeFile(o, d), i) {
			try {
				await u.promises.rename(o, t);
			} catch (e) {
				if (e.code === "EXDEV") await u.promises.copyFile(o, t), await u.promises.unlink(o).catch(() => {});
				else throw e;
			}
			return S.add(t), {
				success: !0,
				outputPath: t
			};
		} else return S.add(o), {
			success: !0,
			outputPath: o
		};
	}), i.handle("bookmarks:extract", async (e, { path: t }) => {
		let n = await fetch(`http://127.0.0.1:${r}/bookmarks/extract`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${f}`
			},
			body: JSON.stringify({ path: t })
		});
		if (!n.ok) {
			let e = await n.json().catch(() => ({}));
			throw Error(e.detail || `bookmarks:extract failed: ${n.status}`);
		}
		return n.json();
	}), process.env.VITE_DEV_SERVER_URL ? g.loadURL(process.env.VITE_DEV_SERVER_URL) : g.loadFile("dist/index.html");
}), n.on("window-all-closed", () => {
	b(), process.platform !== "darwin" && n.quit();
}), n.on("before-quit", b);
//#endregion
