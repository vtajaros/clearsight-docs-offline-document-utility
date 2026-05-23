// frontend/src/components/panels/DeletePagesPanel.tsx
import { useState, useRef, useEffect, useCallback } from 'react'
import * as pdfjsLib from 'pdfjs-dist'
import { pickFiles, formatBytes } from '../../types'
import type { ElectronFile, CompletionModal } from '../../types'
import { PdfHighResPreview } from './PdfHighResPreview'
import { useDebounce } from '../../hooks/useDebounce'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.mjs',
  import.meta.url
).href

type Props = {
  base: string
  loading: boolean
  setLoading: (l: boolean) => void
  setError: (e: string | null) => void
  setModal: (m: CompletionModal) => void
  setHasUnsavedChanges?: (dirty: boolean) => void
}

function PdfPageThumbnail({
  pageNumber,
  pdfDoc,
  isMarked,
  isActive,
  onSelectPage,
  onToggleMark
}: {
  pageNumber: number
  pdfDoc: pdfjsLib.PDFDocumentProxy
  isMarked: boolean
  isActive: boolean
  onSelectPage: (page: number) => void
  onToggleMark: (page: number, e: React.MouseEvent) => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isVisible, setIsVisible] = useState(false)
  const [rendered, setRendered] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { rootMargin: '200px' }
    )

    if (containerRef.current) {
      observer.observe(containerRef.current)
    }
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!isVisible || rendered || !canvasRef.current) return

    let active = true
    async function renderPage() {
      try {
        const page = await pdfDoc.getPage(pageNumber)
        if (!active) return

        const viewport = page.getViewport({ scale: 0.5 }) 
        const canvas = canvasRef.current
        if (!canvas) return
        const context = canvas.getContext('2d')
        if (!context) return

        canvas.width = viewport.width
        canvas.height = viewport.height

        await page.render({ canvasContext: context, viewport, canvas }).promise
        if (active) {
          setRendered(true)
        }
      } catch (e) {
        console.error('Failed to render page', pageNumber, e)
      }
    }
    renderPage()
    return () => { active = false }
  }, [isVisible, rendered, pdfDoc, pageNumber])

  return (
    <div
      ref={containerRef}
      onClick={() => onSelectPage(pageNumber)}
      className={`relative aspect-[3/4] rounded-lg overflow-hidden flex flex-col items-center justify-center cursor-pointer transition-all border-2 select-none group ${
        isActive
          ? 'border-violet-500 shadow-[0_0_0_2px_rgba(139,92,246,0.3)]'
          : isMarked
          ? 'border-red-500/50 opacity-75 grayscale'
          : 'border-zinc-800 bg-zinc-800/40 hover:border-zinc-600'
      }`}
    >
      {/* Page Number Badge */}
      <div className="absolute top-2 left-2 z-10 w-6 h-6 rounded bg-black/60 flex items-center justify-center text-xs font-medium text-white pointer-events-none">
        {pageNumber}
      </div>
      
      {/* Mark for Deletion Checkbox Overlay */}
      <div 
        onClick={(e) => onToggleMark(pageNumber, e)}
        className="absolute top-2 right-2 z-20"
      >
        <div className={`w-6 h-6 rounded flex items-center justify-center border transition-colors shadow-sm ${
          isMarked 
            ? 'bg-red-500 border-red-500 text-white' 
            : 'bg-zinc-900/60 border-zinc-500 text-transparent hover:border-red-400 group-hover:bg-zinc-900/80 backdrop-blur-sm'
        }`}>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      </div>

      {isMarked && (
        <div className="absolute inset-0 z-10 bg-red-500/10 pointer-events-none" />
      )}

      {!rendered && (
        <div className="absolute inset-0 bg-zinc-800 animate-pulse flex items-center justify-center pointer-events-none">
          <svg className="w-5 h-5 text-zinc-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      )}
      
      <canvas ref={canvasRef} className={`w-full h-full object-contain ${rendered ? 'opacity-100' : 'opacity-0'} ${isMarked ? 'opacity-50' : ''}`} />
    </div>
  )
}

export function DeletePagesPanel({ base, loading, setLoading, setError, setModal, setHasUnsavedChanges }: Props) {
  const [file, setFile] = useState<File | ElectronFile | null>(null)
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null)
  const [pagesToDelete, setPagesToDelete] = useState<Set<number>>(new Set())
  const [previewPageIndex, setPreviewPageIndex] = useState<number | null>(null)

  const debouncedPreviewPageIndex = useDebounce(previewPageIndex, 200)

  const handlePickFile = async () => {
    setError(null)
    try {
      const files = await pickFiles({
        accept: 'application/pdf',
        filters: [{ name: 'PDF Document', extensions: ['pdf'] }],
        multiple: false
      })
      if (files.length > 0) {
        setLoading(true)
        const selected = files[0]
        setFile(selected)
        setHasUnsavedChanges?.(true)
        setPagesToDelete(new Set())
        setPreviewPageIndex(null)
        
        const arrayBuffer = selected.isElectron
          ? await window.electronAPI!.readFile(selected.path)
          : await (selected as File).arrayBuffer()

        const doc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
        setPdfDoc(doc)
        if (doc.numPages > 0) {
          setPreviewPageIndex(1)
        }
      }
    } catch (e) {
      console.error(e)
      setError("Failed to read PDF document.")
      setFile(null)
      setPdfDoc(null)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleMark = useCallback((pageNum: number, e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation() // Prevent selecting the page for preview when just marking
    }
    setPagesToDelete(prev => {
      const next = new Set(prev)
      if (next.has(pageNum)) {
        next.delete(pageNum)
      } else {
        next.add(pageNum)
      }
      return next
    })
  }, [])

  const handleDelete = async () => {
    if (!file || pagesToDelete.size === 0) return
    if (pagesToDelete.size === pdfDoc?.numPages) {
      setError("Cannot delete all pages of the document.")
      return
    }

    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      const pagesToDeleteArray = Array.from(pagesToDelete).map(p => p - 1)
      formData.append('pages_to_delete', JSON.stringify(pagesToDeleteArray))

      if ((file as any).isElectron) {
        formData.append('file_path', (file as any).path)
      } else {
        formData.append('file', file as File)
      }

      const res = await fetch(`${base}/api/delete-pages`, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) {
        const d = await res.json()
        throw new Error(d.detail || 'Failed to delete pages')
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      
      setModal({
        open: true,
        title: 'Pages Deleted',
        subtitle: `Successfully deleted ${pagesToDelete.size} pages from the document.`,
        onExport: () => {
          const a = document.createElement('a')
          a.href = url
          let originalName = 'document'
          if ((file as any).isElectron) {
            originalName = (file as any).name.replace(/\.[^/.]+$/, "")
          } else {
            originalName = (file as File).name.replace(/\.[^/.]+$/, "")
          }
          a.download = `${originalName}_deleted.pdf`
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
          setHasUnsavedChanges?.(false)
        }
      })
    } catch (e: any) {
      console.error(e)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full h-full flex flex-col overflow-hidden">
      {!file ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onClick={handlePickFile}
            className="w-full max-w-3xl mx-auto mt-12 h-64 border-2 border-dashed border-[#3a3a3a] bg-[#1a1a1a] rounded-xl flex flex-col items-center justify-center hover:bg-[#222222] transition-colors cursor-pointer"
          >
            <svg className="w-10 h-10 text-zinc-500 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-300">Drag & drop your PDF file here</p>
              <p className="text-xs text-zinc-500 mt-1">or click to browse files</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Control Bar spans full width */}
          <div className="flex items-center justify-between p-4 bg-zinc-900 border-b border-zinc-800 shrink-0 z-10">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 pr-4 border-r border-zinc-800">
                <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <div className="overflow-hidden">
                  <p className="text-sm font-medium text-zinc-200 truncate max-w-[200px]" title={(file as any).name}>{(file as any).name}</p>
                  <p className="text-xs text-zinc-500">{formatBytes((file as any).size)} • {pdfDoc?.numPages} pages</p>
                </div>
              </div>
              
              <button
                onClick={() => {
                  setFile(null)
                  setHasUnsavedChanges?.(false)
                  setPdfDoc(null)
                  setPagesToDelete(new Set())
                  setPreviewPageIndex(null)
                }}
                disabled={loading}
                className="px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-800/50 hover:bg-zinc-700 rounded transition-colors disabled:opacity-50"
              >
                Change File
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-sm text-zinc-400">
                <span className="font-semibold text-zinc-200">{pagesToDelete.size}</span> pages marked for deletion
              </div>
              <button
                onClick={handleDelete}
                disabled={loading || pagesToDelete.size === 0}
                className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm transition-all shadow-lg ${
                  loading || pagesToDelete.size === 0
                    ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed shadow-none'
                    : 'bg-red-500 hover:bg-red-600 text-white shadow-red-950/20'
                }`}
              >
                {loading ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                  </svg>
                )}
                Delete Pages
              </button>
            </div>
          </div>

          {pdfDoc ? (
            <div className="flex-1 flex min-h-0">
              {/* Left Column: Thumbnails Grid */}
              <div className="flex-1 flex flex-col bg-zinc-950/30 overflow-hidden">
                <div className="flex items-center justify-between shrink-0 p-4 pb-2 border-b border-zinc-800/50">
                  <h4 className="text-sm font-medium text-zinc-300">Select Pages to Delete</h4>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        const all = new Set(Array.from({ length: pdfDoc.numPages }, (_, i) => i + 1))
                        setPagesToDelete(all)
                      }}
                      className="text-xs font-medium text-zinc-400 hover:text-red-400 transition-colors"
                    >
                      Mark All
                    </button>
                    <span className="text-zinc-600">|</span>
                    <button
                      onClick={() => setPagesToDelete(new Set())}
                      className="text-xs font-medium text-zinc-400 hover:text-red-400 transition-colors"
                    >
                      Clear All
                    </button>
                  </div>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 pb-12">
                    {Array.from({ length: pdfDoc.numPages }, (_, i) => i + 1).map(pageNum => (
                      <PdfPageThumbnail
                        key={pageNum}
                        pageNumber={pageNum}
                        pdfDoc={pdfDoc}
                        isMarked={pagesToDelete.has(pageNum)}
                        isActive={previewPageIndex === pageNum}
                        onSelectPage={setPreviewPageIndex}
                        onToggleMark={handleToggleMark}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column: High-Res Preview */}
              <div className="w-[400px] xl:w-[500px] shrink-0 border-l border-zinc-800 h-full overflow-y-auto bg-zinc-950 relative custom-scrollbar">
                {debouncedPreviewPageIndex ? (
                  <PdfHighResPreview
                    key={debouncedPreviewPageIndex}
                    pdfDoc={pdfDoc}
                    pageNumber={debouncedPreviewPageIndex}
                    isMarked={pagesToDelete.has(debouncedPreviewPageIndex)}
                    onToggleMark={() => handleToggleMark(debouncedPreviewPageIndex)}
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center">
                    <svg className="w-12 h-12 text-zinc-700 mb-4" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    <p className="text-zinc-500 text-sm font-medium">Select a page to preview</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
             <div className="flex-1 flex items-center justify-center">
                <svg className="w-8 h-8 text-violet-500 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
             </div>
          )}
        </div>
      )}
    </div>
  )
}
