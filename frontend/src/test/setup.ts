import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock URL.createObjectURL and revokeObjectURL
if (typeof window !== 'undefined') {
  window.URL.createObjectURL = vi.fn().mockReturnValue('mock-url')
  window.URL.revokeObjectURL = vi.fn()
}

// Mock electronAPI
globalThis.window.electronAPI = {
  openFiles: vi.fn(),
  readFile: vi.fn(),
  getPort: vi.fn().mockResolvedValue(8000),
  titlebar: {
    minimize: vi.fn(),
    maximize: vi.fn(),
    close: vi.fn(),
    isMaximized: vi.fn().mockResolvedValue(true),
    onMaximizedChange: vi.fn().mockReturnValue(() => {}),
  },
}
