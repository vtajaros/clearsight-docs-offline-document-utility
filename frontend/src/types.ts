// frontend/src/types.ts
// Shared types, utilities, and constants used across all panel components.

export type ActiveTab = 'ocr' | 'merge' | 'split' | 'compress' | 'pdf-to-images' | 'image-to-pdf' | 'delete-pages'
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
      titlebar: {
        minimize(): Promise<void>
        maximize(): Promise<void>
        close():    Promise<void>
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
}): Promise<any[] | File[]> {
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

// Module-level thumbnail caches shared across panels (stable across re-renders)
export const thumbnailCache = new Map<string, string>()
export const imageThumbnailCache = new Map<string, string>()
