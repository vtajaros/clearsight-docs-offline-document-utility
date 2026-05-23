import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electron', {
    platform: process.platform,
})

contextBridge.exposeInMainWorld('electronAPI', {
    openFiles: (options: {
        filters?: { name: string; extensions: string[] }[];
        multiSelections?: boolean;
    }): Promise<any[]> =>
        ipcRenderer.invoke('dialog:openFiles', options),

    readFile: (filePath: string): Promise<ArrayBuffer> =>
        ipcRenderer.invoke('file:read', filePath),

    getPort: (): Promise<number> =>
        ipcRenderer.invoke('get-port'),

    titlebar: {
        minimize: () => ipcRenderer.invoke('titlebar:minimize'),
        maximize: () => ipcRenderer.invoke('titlebar:maximize'),
        close:    () => ipcRenderer.invoke('titlebar:close'),
    },
})