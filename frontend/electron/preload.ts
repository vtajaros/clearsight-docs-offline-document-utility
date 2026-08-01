import { contextBridge, ipcRenderer } from 'electron'
import type { ElectronFile } from '../src/types'

contextBridge.exposeInMainWorld('electron', {
    platform: process.platform,
})

contextBridge.exposeInMainWorld('electronAPI', {
    openFiles: (options: {
        filters?: { name: string; extensions: string[] }[];
        multiSelections?: boolean;
    }): Promise<ElectronFile[]> =>
        ipcRenderer.invoke('dialog:openFiles', options),

    readFile: (filePath: string): Promise<ArrayBuffer> =>
        ipcRenderer.invoke('file:read', filePath),

    getPort: (): Promise<number> =>
        ipcRenderer.invoke('get-port'),

    getToken: (): Promise<string> =>
        ipcRenderer.invoke('get-token'),

    titlebar: {
        minimize: () => ipcRenderer.invoke('titlebar:minimize'),
        maximize: () => ipcRenderer.invoke('titlebar:maximize'),
        close:    () => ipcRenderer.invoke('titlebar:close'),
        isMaximized: (): Promise<boolean> => ipcRenderer.invoke('titlebar:isMaximized'),
        onMaximizedChange: (callback: (isMaximized: boolean) => void) => {
            const listener = (_event: unknown, state: boolean) => callback(state)
            ipcRenderer.on('window-maximized', listener)
            return () => {
                ipcRenderer.removeListener('window-maximized', listener)
            }
        },
    },

    onFileSaved: (callback: (filePath: string) => void) => {
        const listener = (_event: unknown, filePath: string) => callback(filePath)
        ipcRenderer.on('file-saved', listener)
        return () => {
            ipcRenderer.removeListener('file-saved', listener)
        }
    },

    bookmarks: {
        read: (args: { path: string }) =>
            ipcRenderer.invoke('bookmarks:read', args),
        write: (args: { sourcePath: string; overwrite: boolean; bookmarks: unknown[] }) =>
            ipcRenderer.invoke('bookmarks:write', args),
        extract: (args: { path: string }) =>
            ipcRenderer.invoke('bookmarks:extract', args),
    },
})