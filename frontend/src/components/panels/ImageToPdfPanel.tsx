// frontend/src/components/panels/ImageToPdfPanel.tsx
import { useState, useRef } from 'react'
import type { DragEvent } from 'react'
import { type CompletionModal, formatBytes, pickFiles, imageThumbnailCache } from '../../types'
import { ImageThumbnail } from '../Thumbnails'
import { useSimulatedProgress } from '../../hooks/useSimulatedProgress'
import { ProgressBar } from '../ProgressBar'

interface ImageToPdfPanelProps {
  base: string
  loading: boolean
  setLoading: (v: boolean) => void
  setError: (v: string | null) => void
  setModal: (m: CompletionModal) => void
  setHasUnsavedChanges?: (v: boolean) => void
}

export function ImageToPdfPanel({ base, loading, setLoading, setError, setModal, setHasUnsavedChanges }: ImageToPdfPanelProps) {
  const [imageToPdfFiles, setImageToPdfFiles] = useState<any[]>([])
  const [imageToPdfPageSize, setImageToPdfPageSize] = useState<string>('A4')
  const [imageToPdfOrientation, setImageToPdfOrientation] = useState<string>('Landscape')
  const [imageToPdfMargin, setImageToPdfMargin] = useState<string>('None')
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  const fileIdMap = useRef<Map<any, string>>(new Map())
  const { progress, label: progressLabel, start: startProgress, finish: finishProgress, cancel: cancelProgress } = useSimulatedProgress()

  const getFileId = (file: any): string => {
    if (!fileIdMap.current.has(file)) {
      fileIdMap.current.set(file, crypto.randomUUID())
    }
    return fileIdMap.current.get(file)!
  }

  const handleImageToPdfDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault() }
  const handleImageToPdfDragLeave = () => {}
  const handleImageToPdfDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files) {
      const validFiles: File[] = []
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        const file = e.dataTransfer.files[i]
        if (file.type.startsWith('image/') || file.name.match(/\.(jpg|jpeg|png)$/i)) {
          validFiles.push(file)
        }
      }
      if (validFiles.length > 0) {
        setImageToPdfFiles((prev) => [...prev, ...validFiles])
        setError(null)
        setHasUnsavedChanges?.(true)
      } else setError('Only image files (JPG/PNG) are supported.')
    }
  }

  const removeImageToPdfFile = (index: number) => {
    const file = imageToPdfFiles[index]
    if (file) {
      const fileId = fileIdMap.current.get(file)
      if (fileId) imageThumbnailCache.delete(fileId)
      fileIdMap.current.delete(file)
    }
    setImageToPdfFiles((prev) => {
      const next = prev.filter((_, i) => i !== index)
      if (next.length === 0) setHasUnsavedChanges?.(false)
      return next
    })
  }
  
  const clearImageToPdfFiles = () => {
    imageToPdfFiles.forEach(file => {
      const fileId = fileIdMap.current.get(file)
      if (fileId) imageThumbnailCache.delete(fileId)
    })
    fileIdMap.current.clear()
    setImageToPdfFiles([])
    setError(null)
    setHasUnsavedChanges?.(false)
  }

  const handleSort = (type: string) => {
    if (!type) return
    setImageToPdfFiles((prev) => {
      const sorted = [...prev].sort((a, b) => {
        if (type === 'name-asc') return a.name.localeCompare(b.name)
        if (type === 'name-desc') return b.name.localeCompare(a.name)
        const dateA = a.lastModified || a.createdAt || (a instanceof File ? a.lastModified : 0)
        const dateB = b.lastModified || b.createdAt || (b instanceof File ? b.lastModified : 0)
        if (type === 'date-newest') return dateB - dateA
        if (type === 'date-oldest') return dateA - dateB
        return 0
      })
      setHasUnsavedChanges?.(true)
      return sorted
    })
  }

  const handleImageToPdfSubmit = async () => {
    if (imageToPdfFiles.length === 0) return
    setLoading(true)
    setError(null)

    startProgress([
      { target: 20, label: 'Reading images...', delayMs: 400 },
      { target: 55, label: 'Embedding images...', delayMs: 1200 },
      { target: 82, label: 'Writing PDF...', delayMs: 2500 },
      { target: 93, label: 'Finalizing...', delayMs: 4000 },
    ])

    const formData = new FormData()
    imageToPdfFiles.forEach((file) => {
      if (file.isElectron) {
        formData.append('files_path', file.path)
      } else {
        formData.append('files', file)
      }
    })
    formData.append('page_size', imageToPdfPageSize)
    formData.append('orientation', imageToPdfOrientation)
    formData.append('margin', imageToPdfMargin)

    try {
      const token = window.electronAPI?.getToken ? await window.electronAPI.getToken() : ''
      const res = await fetch(`${base}/api/image-to-pdf`, { 
        method: 'POST', 
        body: formData,
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || 'Conversion failed.')
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      
      finishProgress()
      await new Promise(r => setTimeout(r, 400))

      setModal({
        open: true,
        title: 'Conversion Complete',
        subtitle: 'Your PDF is ready to export.',
        onExport: () => {
          const a = document.createElement('a')
          a.href = url
          a.download = 'images_converted.pdf'
          a.click()
          setModal({ open: false, title: '', subtitle: '', onExport: () => {} })
          setHasUnsavedChanges?.(false)
        }
      })
    } catch (err: any) {
      cancelProgress()
      setError(err.message || 'An unexpected error occurred during conversion.')
    } finally {
      setLoading(false)
    }
  }

  const addMoreFiles = async () => {
    const result = await pickFiles({
      filters: [{ name: 'Image Files', extensions: ['jpg', 'jpeg', 'png', 'webp'] }],
      accept: 'image/jpeg,image/png,.jpg,.jpeg,.png',
      multiple: true,
    });
    if (result && result.length > 0) {
      setImageToPdfFiles((prev) => [...prev, ...result])
      setError(null)
      setHasUnsavedChanges?.(true)
    }
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-6">
      {imageToPdfFiles.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onDragOver={handleImageToPdfDragOver}
            onDragLeave={handleImageToPdfDragLeave}
            onDrop={handleImageToPdfDrop}
            onClick={addMoreFiles}
            className="w-full max-w-3xl mx-auto mt-12 h-64 border-2 border-dashed border-[#3a3a3a] bg-[#1a1a1a] rounded-xl flex flex-col items-center justify-center hover:bg-[#222222] transition-colors cursor-pointer"
          >
            <svg className="w-10 h-10 text-zinc-500 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-300">Drag & drop your images here</p>
              <p className="text-xs text-zinc-500 mt-1">or click to browse files</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 min-h-0 flex flex-col gap-6">
          <div className="shrink-0 flex items-center justify-between pb-4 border-b border-zinc-800">
            <div className="text-sm font-semibold text-zinc-200">
              {imageToPdfFiles.length} {imageToPdfFiles.length === 1 ? 'Image' : 'Images'}
            </div>
            <div className="flex items-center gap-3">
              <select
                onChange={(e) => { handleSort(e.target.value); e.target.value = '' }}
                className="px-3.5 py-2 text-xs font-semibold bg-zinc-800 hover:bg-zinc-750 text-zinc-200 rounded-lg transition-all cursor-pointer border border-zinc-700/50 outline-none"
              >
                <option value="">Sort by...</option>
                <option value="name-asc">Name (A-Z)</option>
                <option value="name-desc">Name (Z-A)</option>
                <option value="date-newest">Date (Newest)</option>
                <option value="date-oldest">Date (Oldest)</option>
              </select>
              <button
                onClick={addMoreFiles}
                className="px-3.5 py-2 text-xs font-semibold bg-zinc-800 hover:bg-zinc-750 text-zinc-200 rounded-lg transition-all cursor-pointer border border-zinc-700/50"
              >
                Add More
              </button>
              <button onClick={clearImageToPdfFiles} className="px-3.5 py-2 text-xs font-semibold bg-red-950/20 hover:bg-red-950/40 text-red-400 rounded-lg transition-all cursor-pointer border border-red-900/30">Clear All</button>
            </div>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-2">
            <div className="flex flex-wrap content-start gap-4 pb-4">
              {imageToPdfFiles.map((file, idx) => {
                const fileId = getFileId(file)
                return (
                  <div
                    key={fileId}
                    draggable={true}
                    onDragStart={() => setDragIndex(idx)}
                    onDragOver={(e) => { e.preventDefault(); if (dragOverIndex !== idx) setDragOverIndex(idx) }}
                    onDrop={(e) => { e.preventDefault(); if (dragIndex !== null && dragIndex !== idx) { const updated = [...imageToPdfFiles]; const [moved] = updated.splice(dragIndex, 1); updated.splice(idx, 0, moved); setImageToPdfFiles(updated); } setDragIndex(null); setDragOverIndex(null); }}
                    onDragEnd={() => { setDragIndex(null); setDragOverIndex(null); }}
                    className={`relative flex-shrink-0 w-[160px] bg-zinc-950/40 hover:bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 rounded-xl p-3 flex flex-col gap-2.5 transition-all cursor-move ${
                      dragIndex === idx ? 'opacity-40' : ''
                    } ${
                      dragOverIndex === idx && dragIndex !== idx
                        ? 'border-violet-500/40 bg-violet-500/5'
                        : ''
                    }`}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        removeImageToPdfFile(idx)
                      }}
                      className="absolute top-2.5 right-2.5 z-10 w-5 h-5 flex items-center justify-center bg-zinc-900/80 hover:bg-zinc-850 border border-zinc-800 hover:border-zinc-750 text-zinc-400 hover:text-zinc-200 rounded-full transition-all cursor-pointer"
                      title="Remove file"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                      </svg>
                    </button>

                    <div className="relative w-full aspect-[3/4] bg-zinc-800/40 rounded-lg overflow-hidden flex items-center justify-center border border-zinc-800/80">
                      <ImageThumbnail file={file} fileId={fileId} />
                    </div>

                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-zinc-300 truncate" title={file.name}>
                        {file.name}
                      </p>
                      <p className="text-[10px] text-zinc-500 mt-0.5 font-medium">
                        {formatBytes(file.size)}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="shrink-0 pt-4 border-t border-zinc-800">
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">Page Size</label>
                <select value={imageToPdfPageSize} onChange={(e) => setImageToPdfPageSize(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-violet-500 transition-all cursor-pointer">
                  <option value="A4">A4 (8.27" x 11.69")</option>
                  <option value="Letter">Letter (8.5" x 11")</option>
                  <option value="Legal">Legal (8.5" x 14")</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">Orientation</label>
                <select value={imageToPdfOrientation} onChange={(e) => setImageToPdfOrientation(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-violet-500 transition-all cursor-pointer">
                  <option value="Portrait">Portrait</option>
                  <option value="Landscape">Landscape</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">Margin</label>
                <select value={imageToPdfMargin} onChange={(e) => setImageToPdfMargin(e.target.value)} className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-violet-500 transition-all cursor-pointer">
                  <option value="None">None</option>
                  <option value="Small">Small</option>
                  <option value="Medium">Medium</option>
                  <option value="Large">Large</option>
                </select>
              </div>
            </div>

            <div className="mb-4">
              <ProgressBar loading={loading} progress={progress} label={progressLabel} />
            </div>

            <button
              disabled={imageToPdfFiles.length === 0 || loading}
              onClick={handleImageToPdfSubmit}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-violet-500 hover:bg-violet-600 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white font-medium text-sm rounded-xl transition-all shadow-md shadow-violet-950/10 cursor-pointer"
            >
              {loading ? 'Generating PDF...' : 'Convert Images to PDF'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
