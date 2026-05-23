import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { formatBytes } from '../types'
import { CompressPanel } from '../components/panels/CompressPanel'
import { SplitPanel } from '../components/panels/SplitPanel'

describe('ClearSight Frontend Utilities', () => {
  it('should format bytes correctly', () => {
    expect(formatBytes(0)).toBe('0 Bytes')
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1024 * 1024 * 2.5)).toBe('2.5 MB')
  })
})

describe('CompressPanel Component', () => {
  it('renders standard dropzone when no file is selected', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <CompressPanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        setError={mockSetError}
        setModal={mockSetModal}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    expect(screen.getByText(/Drag & drop your PDF file here/i)).toBeInTheDocument()
  })

  it('renders compression level options', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <CompressPanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        setError={mockSetError}
        setModal={mockSetModal}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    expect(screen.getByText(/Compression Level/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /low/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /medium/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /high/i })).toBeInTheDocument()
  })
})

describe('SplitPanel Component', () => {
  it('allows toggling split modes', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <SplitPanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        setError={mockSetError}
        setModal={mockSetModal}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    const rangeButton = screen.getByRole('button', { name: /Split by Range/i })
    const pagesButton = screen.getByRole('button', { name: /Split into Individual Pages/i })

    expect(rangeButton).toBeInTheDocument()
    expect(pagesButton).toBeInTheDocument()
  })
})

import { DeletePagesPanel } from '../components/panels/DeletePagesPanel'

vi.mock('pdfjs-dist', () => {
  return {
    GlobalWorkerOptions: { workerSrc: '' },
    getDocument: vi.fn(),
  }
})

class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.IntersectionObserver = MockIntersectionObserver as any

describe('DeletePagesPanel Component', () => {
  it('renders pick file UI initially', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <DeletePagesPanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        setError={mockSetError}
        setModal={mockSetModal}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    expect(screen.getByText(/Drag & drop your PDF file here/i)).toBeInTheDocument()
  })
})

import { PdfToImagesPanel } from '../components/panels/PdfToImagesPanel'
import { ImageToPdfPanel } from '../components/panels/ImageToPdfPanel'
import { MergePanel } from '../components/panels/MergePanel'
import { OcrPanel } from '../components/panels/OcrPanel'

describe('PdfToImagesPanel Component', () => {
  it('renders pick file UI initially', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <PdfToImagesPanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        setError={mockSetError}
        setModal={mockSetModal}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    expect(screen.getByText(/Drag & drop your PDF file here/i)).toBeInTheDocument()
  })
})

describe('ImageToPdfPanel Component', () => {
  it('renders pick file UI initially', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <ImageToPdfPanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        setError={mockSetError}
        setModal={mockSetModal}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    expect(screen.getByText(/Drag & drop your images here/i)).toBeInTheDocument()
  })
})

describe('MergePanel Component', () => {
  it('renders pick file UI initially', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <MergePanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        setError={mockSetError}
        setModal={mockSetModal}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    expect(screen.getByText(/Drag & drop your PDF files here/i)).toBeInTheDocument()
  })
})

describe('OcrPanel Component', () => {
  it('renders pick file UI initially', () => {
    const mockSetLoading = vi.fn()
    const mockSetError = vi.fn()
    const mockSetModal = vi.fn()

    render(
      <OcrPanel
        base="http://127.0.0.1:8000"
        loading={false}
        setLoading={mockSetLoading}
        error={null}
        setError={mockSetError}
        setModal={mockSetModal}
        ocrFile={null}
        setOcrFile={vi.fn()}
        ocrLanguage="eng"
        setOcrLanguage={vi.fn()}
        ocrFormat="pdf"
        setOcrFormat={vi.fn()}
        ocrAccuracy="balanced"
        setOcrAccuracy={vi.fn()}
        ocrTextResult={null}
        setOcrTextResult={vi.fn()}
        ocrCopied={false}
        setOcrCopied={vi.fn()}
        port={8000}
        setHasUnsavedChanges={vi.fn()}
      />
    )

    expect(screen.getByText(/Drag & drop your scanned PDF here/i)).toBeInTheDocument()
  })
})
