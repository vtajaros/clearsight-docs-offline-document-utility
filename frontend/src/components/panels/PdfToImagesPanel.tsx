// frontend/src/components/panels/PdfToImagesPanel.tsx
import { useState } from 'react'
import type { DragEvent } from 'react'
import { type CompletionModal, formatBytes, pickFiles, thumbnailCache } from '../../types'
import { PdfThumbnail } from '../Thumbnails'

interface PdfToImagesPanelProps {
  base: string
  loading: boolean
  setLoading: (v: boolean) => void
  setError: (v: string | null) => void
  setModal: (m: CompletionModal) => void
  setHasUnsavedChanges?: (v: boolean) => void
}

export function PdfToImagesPanel({ base, loading, setLoading, setError, setModal, setHasUnsavedChanges }: PdfToImagesPanelProps) {
  const [pdfToImagesFile, setPdfToImagesFile] = useState<any | null>(null)
  const [pdfToImagesFormat, setPdfToImagesFormat] = useState<'PNG' | 'JPG'>('PNG')
  const [pdfToImagesDpi, setPdfToImagesDpi] = useState<string>('150')

  const handlePdfToImagesDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault() }
  const handlePdfToImagesDragLeave = () => {}
  const handlePdfToImagesDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        thumbnailCache.delete('pdf-to-images-preview')
        setPdfToImagesFile(file)
        setError(null)
        setHasUnsavedChanges?.(true)
      } else setError('Only PDF files are supported.')
    }
  }

  const handlePdfToImagesSubmit = async () => {
    if (!pdfToImagesFile) return
    setLoading(true)
    setError(null)

    const formData = new FormData()
    if (pdfToImagesFile.isElectron) {
      formData.append('file_path', pdfToImagesFile.path)
    } else {
      formData.append('file', pdfToImagesFile)
    }
    formData.append('image_format', pdfToImagesFormat)
    formData.append('dpi', pdfToImagesDpi)

    try {
      const res = await fetch(`${base}/api/pdf-to-images`, { method: 'POST', body: formData })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || 'Conversion failed.')
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const downloadName = `${pdfToImagesFile.name.replace(/\.pdf$/i, '')}_images.zip`
      
      setModal({
        open: true,
        title: 'Conversion Complete',
        subtitle: 'Your images are ready to export as a ZIP file.',
        onExport: () => {
          const a = document.createElement('a')
          a.href = url
          a.download = downloadName
          a.click()
          setModal({ open: false, title: '', subtitle: '', onExport: () => {} })
          thumbnailCache.delete('pdf-to-images-preview')
          setPdfToImagesFile(null)
          setHasUnsavedChanges?.(false)
        }
      })
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during conversion.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-6">
      {!pdfToImagesFile ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onDragOver={handlePdfToImagesDragOver}
            onDragLeave={handlePdfToImagesDragLeave}
            onDrop={handlePdfToImagesDrop}
            onClick={async () => {
              const result = await pickFiles({
                filters: [{ name: 'PDF Files', extensions: ['pdf'] }],
                accept: 'application/pdf',
                multiple: false,
              });
              if (result && result[0]) {
                thumbnailCache.delete('pdf-to-images-preview')
                setPdfToImagesFile(result[0])
                setError(null)
                setHasUnsavedChanges?.(true)
              }
            }}
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
        <div className="flex-1 min-h-0 flex flex-col gap-6">
          <div className="flex-1 min-h-0 flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2">
          <div className="flex items-center justify-between p-4 bg-zinc-950/50 border border-zinc-800 rounded-xl">
            <div className="flex items-center gap-3 min-w-0">
              <svg className="w-8 h-8 text-red-400 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-zinc-200 truncate max-w-md">{pdfToImagesFile.name}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{formatBytes(pdfToImagesFile.size)}</p>
              </div>
            </div>
            <button onClick={() => { setPdfToImagesFile(null); thumbnailCache.delete('pdf-to-images-preview'); setHasUnsavedChanges?.(false); }} className="p-1.5 text-zinc-500 hover:text-zinc-300 rounded-lg hover:bg-zinc-850 transition-all cursor-pointer">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
            </button>
          </div>
          
            <div className="w-[160px] bg-zinc-950/40 border border-zinc-800 rounded-xl p-3 flex flex-col gap-2.5 mx-auto">
              <PdfThumbnail file={pdfToImagesFile} fileId="pdf-to-images-preview" />
            </div>
          </div>

          <div className="shrink-0 pt-4 border-t border-zinc-800">
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">Image Format</label>
                <div className="flex bg-zinc-950/50 p-1 border border-zinc-800 rounded-lg">
                  {(['PNG', 'JPG'] as const).map((fmt) => (
                    <button
                      key={fmt}
                      onClick={() => setPdfToImagesFormat(fmt)}
                      className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                        pdfToImagesFormat === fmt ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-400'
                      }`}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">Quality (DPI)</label>
                <div className="flex bg-zinc-950/50 p-1 border border-zinc-800 rounded-lg">
                  {(['72', '150', '300']).map((dpi) => (
                    <button
                      key={dpi}
                      onClick={() => setPdfToImagesDpi(dpi)}
                      className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                        pdfToImagesDpi === dpi ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-400'
                      }`}
                    >
                      {dpi} DPI
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              disabled={!pdfToImagesFile || loading}
              onClick={handlePdfToImagesSubmit}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-violet-500 hover:bg-violet-600 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white font-medium text-sm rounded-xl transition-all shadow-md shadow-violet-950/10 cursor-pointer"
            >
              {loading ? 'Converting...' : 'Convert to Images'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
