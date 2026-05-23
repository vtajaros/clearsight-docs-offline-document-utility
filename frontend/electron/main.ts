import { app, BrowserWindow, Menu, ipcMain, dialog } from 'electron'
import { spawn, ChildProcess } from 'child_process'
import * as path from 'path'
import * as net from 'net'
import { fileURLToPath } from 'url'
import * as fs from 'fs'

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

    const backendExecutable = isDev
        ? path.join(backendBase, '.venv', 'Scripts', 'uvicorn.exe')
        : path.join(process.resourcesPath, 'backend', 'backend.exe')

    const args = isDev
        ? ['api:app', '--port', String(port), '--host', '127.0.0.1']
        : ['--port', String(port), '--host', '127.0.0.1']

    const cwd = isDev ? backendBase : undefined

    backendProcess = spawn(backendExecutable, args, {
        cwd,
        stdio: 'pipe',
        detached: false,
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
        backendProcess.kill()
        backendProcess = null
    }
}

let lastUsedDirectory: string | undefined = undefined

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
        }

        if (canceled) return []

        return filePaths.map(filePath => {
            const stats = fs.statSync(filePath)
            return {
                path: filePath,
                name: path.basename(filePath),
                size: stats.size,
                type: getMimeType(filePath),
                isElectron: true,
            }
        })
    }
)

ipcMain.handle('file:read', async (_event, filePath: string) => {
    const buffer = await fs.promises.readFile(filePath)
    return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength)
})

console.log('appPath:', app.getAppPath())
app.whenReady().then(async () => {
    const port = await findFreePort()
    await startBackend(port)

    ipcMain.handle('get-port', () => port)

    Menu.setApplicationMenu(null)
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        frame: false,
        titleBarStyle: 'hidden',
        icon: path.join(app.getAppPath(), '..', 'icon.png'),
        autoHideMenuBar: true,
        thickFrame: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.mjs'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    })
    mainWindow.maximize()  // add this line

    ipcMain.handle('titlebar:minimize', () => mainWindow?.minimize())
    ipcMain.handle('titlebar:maximize', () => {
        if (mainWindow?.isMaximized()) mainWindow.restore()
        else mainWindow?.maximize()
    })
    ipcMain.handle('titlebar:close', () => mainWindow?.close())

    // Inject backend port into renderer
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow?.webContents.executeJavaScript(
            `window.__BACKEND_PORT__ = ${port}`
        )
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