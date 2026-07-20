// frontend/src/types.ts
// Shared types, utilities, and constants used across all panel components.

export type ActiveTab = 'ocr' | 'merge' | 'split' | 'compress' | 'pdf-to-images' | 'image-to-pdf' | 'delete-pages' | 'bookmarks' | 'bionic'
export type OcrLanguage = 'eng' | 'fil' | 'jpn' | 'chi_sim'
export type OcrFormat = 'txt' | 'pdf'
export type OcrAccuracy = 'fast' | 'balanced' | 'accurate'
export type SplitMode = 'range' | 'pages'

export type CompletionModal = {
  open: boolean
  title: string
  subtitle: string
  onExport: () => void
}

export interface BookmarkNode {
  title: string
  page: number
  level: number
  children: BookmarkNode[]
}

export type OcrProgress = {
  current: number
  total: number
  message: string
}

// Virtual file object returned by the Electron IPC dialog handler.
export type ElectronFile = {
  path: string
  name: string
  size: number
  type: string
  isElectron: true
  lastModified?: number
  createdAt?: number
}

declare global {
  interface Window {
    electronAPI?: {
      openFiles(options: {
        filters?: { name: string; extensions: string[] }[];
        multiSelections?: boolean;
      }): Promise<ElectronFile[]>;
      readFile(filePath: string): Promise<ArrayBuffer>;
      getPort(): Promise<number>;
      getToken(): Promise<string>;
      titlebar: {
        minimize(): Promise<void>
        maximize(): Promise<void>
        close(): Promise<void>
        isMaximized(): Promise<boolean>
        onMaximizedChange(callback: (isMaximized: boolean) => void): () => void
      }
      bookmarks: {
        read: (args: { path: string }) => Promise<{
          bookmarks: BookmarkNode[]
          page_count: number
        }>
        write: (args: {
          sourcePath: string
          overwrite: boolean
          bookmarks: BookmarkNode[]
        }) => Promise<{ success: boolean; outputPath: string }>
        extract: (args: { path: string }) => Promise<{
          bookmarks: BookmarkNode[]
          is_generated: boolean
          needs_ocr: boolean
          page_count: number
        }>
      }
    };
  }
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export async function pickFiles(options: {
  accept?: string;
  filters?: { name: string; extensions: string[] }[];
  multiple?: boolean;
}): Promise<(ElectronFile | File)[]> {
  if (window.electronAPI?.openFiles) {
    return window.electronAPI.openFiles({
      filters: options.filters,
      multiSelections: options.multiple ?? false,
    });
  }

  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = options.multiple ?? false;
    if (options.accept) input.accept = options.accept;
    input.onchange = () => resolve(Array.from(input.files ?? []));
    input.click();
  });
}

export class LruCache<K, V> {
  private readonly max: number
  private readonly map: Map<K, V>

  constructor(max: number) {
    this.max = max
    this.map = new Map()
  }

  has(key: K): boolean {
    return this.map.has(key)
  }

  get(key: K): V | undefined {
    if (!this.map.has(key)) return undefined
    // Re-insert to mark as recently used
    const value = this.map.get(key)!
    this.map.delete(key)
    this.map.set(key, value)
    return value
  }

  set(key: K, value: V): void {
    if (this.map.has(key)) this.map.delete(key)
    this.map.set(key, value)
    if (this.map.size > this.max) {
      // Map iteration order is insertion order — first key is oldest
      this.map.delete(this.map.keys().next().value!)
    }
  }
}

export const thumbnailCache = new LruCache<string, string>(50)
export const imageThumbnailCache = new LruCache<string, string>(50)
