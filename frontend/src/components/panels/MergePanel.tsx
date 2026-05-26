// frontend/src/components/panels/MergePanel.tsx
import { useState, useRef, useEffect } from 'react'
import type { DragEvent } from 'react'
import { type CompletionModal, formatBytes, pickFiles, thumbnailCache } from '../../types'
import { PdfThumbnail } from '../Thumbnails'
import * as pdfjsLib from 'pdfjs-dist'

interface MergePanelProps {
  base: string
  loading: boolean
  setLoading: (v: boolean) => void
  setError: (v: string | null) => void
  setModal: (m: CompletionModal) => void
  setHasUnsavedChanges?: (v: boolean) => void
}

export function MergePanel({ base, loading, setLoading, setError, setModal, setHasUnsavedChanges }: MergePanelProps) {
  const [mergeFiles, setMergeFiles] = useState<any[]>([])
  const [totalPageCount, setTotalPageCount] = useState<number | null>(null)
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  const fileIdMap = useRef<Map<any, string>>(new Map())

  const getFileId = (file: any): string => {
    if (!fileIdMap.current.has(file)) {
      fileIdMap.current.set(file, crypto.randomUUID())
    }
    return fileIdMap.current.get(file)!
  }

  useEffect(() => {
    if (mergeFiles.length === 0) { setTotalPageCount(null); return }
    let active = true
    async function calculateTotalPages() {
      try {
        let total = 0
        for (const file of mergeFiles) {
          const arrayBuffer = window.electronAPI?.readFile
            ? await window.electronAPI.readFile(file.path)
            : await file.arrayBuffer()
          if (!active) return
          const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
          total += pdf.numPages
        }
        if (active) setTotalPageCount(total)
      } catch (err) {
        console.error('Failed to calculate total pages', err)
      }
    }
    calculateTotalPages()
    return () => { active = false }
  }, [mergeFiles])

  const removeMergeFile = (index: number) => {
    const file = mergeFiles[index]
    if (file) {
      const fileId = fileIdMap.current.get(file)
      if (fileId) thumbnailCache.delete(fileId)
      fileIdMap.current.delete(file)
    }
    setMergeFiles((prev) => {
      const next = prev.filter((_, i) => i !== index)
      if (next.length === 0) setHasUnsavedChanges?.(false)
      return next
    })
  }

  const clearMergeFiles = () => {
    mergeFiles.forEach(file => {
      const fileId = fileIdMap.current.get(file)
      if (fileId) thumbnailCache.delete(fileId)
    })
    fileIdMap.current.clear()
    setMergeFiles([])
    setError(null)
    setHasUnsavedChanges?.(false)
  }

  const handleSort = (type: string) => {
    if (!type) return
    setMergeFiles((prev) => {
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

  const handleMergeDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault() }
  const handleMergeDragLeave = () => {}
  const handleMergeDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files) {
      const valid: File[] = []
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        const f = e.dataTransfer.files[i]
        if (f.type === 'application/pdf' || f.name.endsWith('.pdf')) valid.push(f)
      }
      if (valid.length > 0) { setMergeFiles(prev => [...prev, ...valid]); setError(null); setHasUnsavedChanges?.(true) }
      else setError('Only PDF files are supported.')
    }
  }

  const handleMergeSubmit = async () => {
    if (mergeFiles.length < 2) return
    setLoading(true); setError(null)

    const formData = new FormData()
    mergeFiles.forEach((file) => {
      if (file.isElectron) formData.append('files_path', file.path)
      else formData.append('files', file)
    })

    try {
      const res = await fetch(`${base}/api/merge`, { method: 'POST', body: formData })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || 'Merging failed.')
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setModal({
        open: true, title: 'Merge Complete', subtitle: 'Your merged file is ready to export.',
        onExport: () => {
          const a = document.createElement('a'); a.href = url; a.download = 'merged.pdf'; a.click()
          setModal({ open: false, title: '', subtitle: '', onExport: () => {} })
          setHasUnsavedChanges?.(false)
        }
      })
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during Merge.')
    } finally {
      setLoading(false)
    }
  }

  const addMoreFiles = async () => {
    const result = await pickFiles({ filters: [{ name: 'PDF Files', extensions: ['pdf'] }], accept: 'application/pdf', multiple: true })
    if (result && result.length > 0) { setMergeFiles(prev => [...prev, ...result]); setError(null); setHasUnsavedChanges?.(true) }
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-6">
      {mergeFiles.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onDragOver={handleMergeDragOver} onDragLeave={handleMergeDragLeave} onDrop={handleMergeDrop}
            onClick={addMoreFiles}
            className="w-full max-w-3xl mx-auto mt-12 h-64 border-2 border-dashed border-[#3a3a3a] bg-[#1a1a1a] rounded-xl flex flex-col items-center justify-center hover:bg-[#222222] transition-colors cursor-pointer"
          >
            <svg className="w-10 h-10 text-zinc-500 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-300">Drag & drop your PDF files here</p>
              <p className="text-xs text-zinc-500 mt-1">or click to browse files</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 min-h-0 flex flex-col gap-6">
          <div className="shrink-0 flex items-center justify-between pb-4 border-b border-zinc-800">
            <div className="text-sm font-semibold text-zinc-200">
              {mergeFiles.length} {mergeFiles.length === 1 ? 'Document' : 'Documents'}
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
              <button onClick={addMoreFiles} className="px-3.5 py-2 text-xs font-semibold bg-zinc-800 hover:bg-zinc-750 text-zinc-200 rounded-lg transition-all cursor-pointer border border-zinc-700/50">Add More</button>
              <button onClick={clearMergeFiles} className="px-3.5 py-2 text-xs font-semibold bg-red-950/20 hover:bg-red-950/40 text-red-400 rounded-lg transition-all cursor-pointer border border-red-900/30">Clear All</button>
              <button
                disabled={mergeFiles.length < 2 || loading}
                onClick={handleMergeSubmit}
                className="px-4 py-2 text-xs font-semibold bg-violet-500 hover:bg-violet-600 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white rounded-lg transition-all shadow-md cursor-pointer flex items-center gap-2"
              >
                {loading ? (
                  <><svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>Merging...</>
                ) : `Merge ${mergeFiles.length} PDF Documents`}
              </button>
            </div>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-2">
            <div className="flex flex-wrap content-start gap-4 pb-4">
              {mergeFiles.map((file, idx) => {
                const fileId = getFileId(file)
                return (
                  <div
                    key={fileId} draggable
                    onDragStart={() => setDragIndex(idx)}
                    onDragOver={(e) => { e.preventDefault(); if (dragOverIndex !== idx) setDragOverIndex(idx) }}
                    onDrop={(e) => {
                      e.preventDefault()
                      if (dragIndex !== null && dragIndex !== idx) {
                        const updated = [...mergeFiles]
                        const [moved] = updated.splice(dragIndex, 1)
                        updated.splice(idx, 0, moved)
                        setMergeFiles(updated)
                      }
                      setDragIndex(null); setDragOverIndex(null)
                    }}
                    onDragEnd={() => { setDragIndex(null); setDragOverIndex(null) }}
                    className={`relative flex-shrink-0 w-[160px] bg-zinc-950/40 hover:bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 rounded-xl p-3 flex flex-col gap-2.5 transition-all cursor-move ${dragIndex === idx ? 'opacity-40' : ''} ${dragOverIndex === idx && dragIndex !== idx ? 'border-violet-500/40 bg-violet-500/5' : ''}`}
                  >
                    <button
                      onClick={(e) => { e.stopPropagation(); removeMergeFile(idx) }}
                      className="absolute top-2.5 right-2.5 z-10 w-5 h-5 flex items-center justify-center bg-zinc-900/80 hover:bg-zinc-850 border border-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-full transition-all cursor-pointer"
                      title="Remove file"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                    </button>
                    <PdfThumbnail file={file} fileId={fileId} />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-zinc-300 truncate" title={file.name}>{file.name}</p>
                      <p className="text-[10px] text-zinc-500 mt-0.5 font-medium">{formatBytes(file.size)}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="shrink-0 flex items-center justify-between pt-4 border-t border-zinc-800 text-xs text-zinc-500">
            <span>Files will be merged in the order shown. Drag to reorder.</span>
            {totalPageCount !== null && (
              <span className="font-semibold text-zinc-400 bg-zinc-950 px-2 py-1 rounded border border-zinc-800/60 font-mono">
                Total Pages: {totalPageCount}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
