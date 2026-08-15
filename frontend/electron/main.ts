import { app, BrowserWindow, Menu, ipcMain, dialog, session } from 'electron'
import { spawn, ChildProcess } from 'child_process'
import * as path from 'path'
import * as net from 'net'
import { fileURLToPath } from 'url'
import * as fs from 'fs'
import * as crypto from 'crypto'

const apiToken = crypto.randomUUID()

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let backendProcess: ChildProcess | null = null
let mainWindow: BrowserWindow | null = null

function findFreePort(): Promise<number> {
    return new Promise((resolve, reject) => {
        const server = net.createServer()
        server.listen(0, '127.0.0.1', () => {
            const address = server.address()
            const port = typeof address === 'object' && address ? address.port : null
            server.close(() => {
                if (port) resolve(port)
                else reject(new Error('Could not find free port'))
            })
        })
    })
}

async function startBackend(port: number): Promise<void> {
    const isDev = !!process.env.VITE_DEV_SERVER_URL
    const backendBase = path.join(app.getAppPath(), '..', 'backend')

    const isWin = process.platform === 'win32'
    const venvBinDir = isWin ? 'Scripts' : 'bin'
    const pythonExec = isWin ? 'python.exe' : 'python3'
    const backendExec = isWin ? 'backend.exe' : 'backend'

    const backendExecutable = isDev
        ? path.join(backendBase, '.venv', venvBinDir, pythonExec)
        : path.join(process.resourcesPath, 'backend', backendExec)

    const args = isDev
        ? ['-m', 'uvicorn', 'api:app', '--port', String(port), '--host', '127.0.0.1']
        : ['--port', String(port), '--host', '127.0.0.1']

    const cwd = isDev ? backendBase : undefined

    backendProcess = spawn(backendExecutable, args, {
        cwd,
        env: { ...process.env, CLEARSIGHT_API_TOKEN: apiToken },
        stdio: 'pipe',
        detached: false,
    })

    backendProcess.on('error', (err) => {
        console.error('Failed to start backend process:', err)
    })

    backendProcess.stdout?.on('data', (d) => console.log('[backend]', d.toString()))
    backendProcess.stderr?.on('data', (d) => console.error('[backend]', d.toString()))

    await waitForBackend(port)
}

function waitForBackend(port: number, retries = 40, intervalMs = 500): Promise<void> {
    return new Promise((resolve, reject) => {
        let attempts = 0
        const check = () => {
            const sock = net.createConnection({ port, host: '127.0.0.1' })
            sock.on('connect', () => { sock.destroy(); resolve() })
            sock.on('error', () => {
                if (++attempts >= retries) reject(new Error('Backend did not start in time'))
                else setTimeout(check, intervalMs)
            })
        }
        check()
    })
}

function killBackend() {
    if (backendProcess) {
        const pid = backendProcess.pid
        if (pid) {
            if (process.platform === 'win32') {
                // Kill the entire process tree (catches Tesseract/Poppler grandchildren)
                spawn('taskkill', ['/pid', String(pid), '/t', '/f'], { stdio: 'ignore' })
            } else {
                backendProcess.kill('SIGTERM')
            }
        }
        backendProcess = null
    }
}

let lastUsedDirectory: string | undefined = undefined
const allowedReadPaths = new Set<string>()

function getMimeType(filePath: string): string {
    const ext = path.extname(filePath).toLowerCase()
    if (ext === '.pdf') return 'application/pdf'
    if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg'
    if (ext === '.png') return 'image/png'
    if (ext === '.webp') return 'image/webp'
    return 'application/octet-stream'
}

ipcMain.handle(
    'dialog:openFiles',
    async (_event, options: { filters?: Electron.FileFilter[]; multiSelections?: boolean }) => {
        const { canceled, filePaths } = await dialog.showOpenDialog({
            defaultPath: lastUsedDirectory,
            properties: options.multiSelections
                ? ['openFile', 'multiSelections']
                : ['openFile'],
            filters: options.filters ?? [{ name: 'All Files', extensions: ['*'] }],
        })

        if (!canceled && filePaths.length > 0) {
            lastUsedDirectory = path.dirname(filePaths[0])
            filePaths.forEach(p => allowedReadPaths.add(p))
        }

        if (canceled) return []

        return filePaths.flatMap(filePath => {
            let stats: fs.Stats
            try {
                stats = fs.statSync(filePath)
            } catch {
                // File disappeared between dialog close and stat — skip it
                return []
            }
            return [{
                path: filePath,
                name: path.basename(filePath),
                size: stats.size,
                type: getMimeType(filePath),
                isElectron: true as const,
                lastModified: stats.mtimeMs,
                createdAt: stats.birthtimeMs,
            }]
        })
    }
)

ipcMain.handle('file:read', async (_event, filePath: string) => {
    if (!allowedReadPaths.has(filePath)) {
        throw new Error(`Access denied: ${filePath} was not selected by the user.`)
    }
    const buffer = await fs.promises.readFile(filePath)
    return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength)
})

app.whenReady().then(async () => {
    const port = await findFreePort()
    await startBackend(port)

    ipcMain.handle('get-port', () => port)
    ipcMain.handle('get-token', () => apiToken)

    Menu.setApplicationMenu(null)
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 500,
        frame: false,
        transparent: process.platform === 'linux',
        titleBarStyle: 'hidden',
        icon: path.join(app.getAppPath(), '..', 'icon.png'),
        autoHideMenuBar: true,
        webPreferences: {
            preload: path.join(__dirname, 'preload.mjs'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    })
    mainWindow.maximize()

    session.defaultSession.on('will-download', (_event, item) => {
        if (lastUsedDirectory) {
            item.setSaveDialogOptions({
                defaultPath: path.join(lastUsedDirectory, item.getFilename())
            })
        }
        item.on('done', (_event, state) => {
            if (state === 'completed' && mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('file-saved', item.getSavePath())
            }
        })
    })

    mainWindow.on('maximize', () => {
        mainWindow?.webContents.send('window-maximized', true)
    })
    mainWindow.on('unmaximize', () => {
        mainWindow?.webContents.send('window-maximized', false)
    })

    ipcMain.handle('titlebar:minimize', () => mainWindow?.minimize())
    ipcMain.handle('titlebar:isMaximized', () => mainWindow?.isMaximized() ?? false)
    ipcMain.handle('titlebar:maximize', () => {
        if (mainWindow?.isMaximized()) mainWindow.restore()
        else mainWindow?.maximize()
    })
    ipcMain.handle('titlebar:close', () => mainWindow?.close())

    ipcMain.handle('bookmarks:read', async (_event, { path }: { path: string }) => {
        const url = `http://127.0.0.1:${port}/bookmarks/read?path=${encodeURIComponent(path)}`
        const res = await fetch(url, {
            headers: { Authorization: `Bearer ${apiToken}` }
        })
        if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            throw new Error(err.detail || `bookmarks:read failed: ${res.status}`)
        }
        return res.json()
    })

    ipcMain.handle('bookmarks:write',
        async (_event, {
            sourcePath,
            overwrite,
            bookmarks
        }: { sourcePath: string; overwrite: boolean; bookmarks: unknown[] }) => {
            const tmpOutputPath = path.join(
                app.getPath('temp'),
                `clearsight_bm_${Date.now()}_${path.basename(sourcePath)}`
            )
            const res = await fetch(`http://127.0.0.1:${port}/bookmarks/write`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${apiToken}`
                },
                body: JSON.stringify({
                    source_path: sourcePath,
                    output_path: tmpOutputPath,
                    bookmarks
                })
            })
            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || `bookmarks:write failed: ${res.status}`)
            }
            const arrayBuffer = await res.arrayBuffer()
            const buffer = Buffer.from(arrayBuffer)
            await fs.promises.writeFile(tmpOutputPath, buffer)

            if (overwrite) {
                try {
                    await fs.promises.rename(tmpOutputPath, sourcePath)
                } catch (err: any) {
                    if (err.code === 'EXDEV') {
                        // Cross-device rename not allowed — fall back to copy then delete
                        await fs.promises.copyFile(tmpOutputPath, sourcePath)
                        await fs.promises.unlink(tmpOutputPath).catch(() => {})
                    } else {
                        throw err
                    }
                }
                allowedReadPaths.add(sourcePath)
                return { success: true, outputPath: sourcePath }
            } else {
                allowedReadPaths.add(tmpOutputPath)
                return { success: true, outputPath: tmpOutputPath }
            }
        }
    )

    ipcMain.handle('bookmarks:extract', async (_event, { path: pdfPath }: { path: string }) => {
        const res = await fetch(`http://127.0.0.1:${port}/bookmarks/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${apiToken}`
            },
            body: JSON.stringify({ path: pdfPath })
        })
        if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            throw new Error(err.detail || `bookmarks:extract failed: ${res.status}`)
        }
        return res.json()
    })

    if (process.env.VITE_DEV_SERVER_URL) {
        mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
    } else {
        mainWindow.loadFile('dist/index.html')
    }
})

app.on('window-all-closed', () => {
    killBackend()
    if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', killBackend)