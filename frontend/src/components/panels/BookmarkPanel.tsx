import { useState, useEffect } from 'react'
import type { DragEvent } from 'react'
import { type CompletionModal, type ElectronFile, type BookmarkNode, formatBytes, pickFiles } from '../../types'
import { BookmarkTreeNode } from '../BookmarkTreeNode'
import { BookmarkEditor } from '../BookmarkEditor'

interface BookmarkPanelProps {
  base: string
  loading: boolean
  setLoading: (v: boolean) => void
  setError: (v: string | null) => void
  setModal: (m: CompletionModal) => void
  setHasUnsavedChanges: (v: boolean) => void
}

export function BookmarkPanel({ base, loading, setLoading, setError, setModal, setHasUnsavedChanges }: BookmarkPanelProps) {
  const [file, setFile] = useState<ElectronFile | File | null>(null)
  const [bookmarks, setBookmarks] = useState<BookmarkNode[]>([])
  const [pageCount, setPageCount] = useState<number>(0)
  const [fetchStatus, setFetchStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const [mode, setMode] = useState<'view' | 'editing' | 'generating'>('view')
  const [editingBookmarks, setEditingBookmarks] = useState<BookmarkNode[]>([])
  const [needsOcr, setNeedsOcr] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  useEffect(() => {
    if (saveStatus === 'saved') {
      const t = setTimeout(() => setSaveStatus('idle'), 2500)
      return () => clearTimeout(t)
    }
  }, [saveStatus])

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault() }
  const handleDragLeave = () => {}
  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type === 'application/pdf' || droppedFile.name.endsWith('.pdf')) {
        setFile(droppedFile)
        setHasUnsavedChanges(true)
        await loadBookmarks(droppedFile)
      } else {
        setError('Only PDF files are supported.')
      }
    }
  }

  const handleFilePick = async () => {
    const result = await pickFiles({ filters: [{ name: 'PDF Files', extensions: ['pdf'] }], accept: 'application/pdf', multiple: false })
    if (result && result[0]) {
      const selectedFile = result[0]
      setFile(selectedFile)
      setHasUnsavedChanges(true)
      await loadBookmarks(selectedFile)
    }
  }

  const loadBookmarks = async (targetFile: ElectronFile | File) => {
    if (!('isElectron' in targetFile && targetFile.isElectron)) {
      setError("Bookmark reading requires a locally selected file. Please use the file picker.")
      setFetchStatus('error')
      return
    }

    setFetchStatus('loading')
    setError(null)
    try {
      const result = await window.electronAPI!.bookmarks.read({ path: targetFile.path })
      setBookmarks(result.bookmarks)
      setPageCount(result.page_count)
      setFetchStatus('idle')
    } catch (err: any) {
      setFetchStatus('error')
      setError(err.message || "Failed to load bookmarks.")
    }
  }

  async function handleGenerate() {
    if (!file || !('isElectron' in file) || !file.path) return
    setMode('generating')
    setNeedsOcr(false)
    try {
      const result = await window.electronAPI!.bookmarks.extract({
        path: file.path
      })
      if (result.needs_ocr) {
        setNeedsOcr(true)
        setMode('view')
        return
      }
      setEditingBookmarks(result.bookmarks)
      setMode('editing')
    } catch (err: any) {
      setError(err.message || 'Failed to generate bookmarks.')
      setMode('view')
    }
  }

  async function handleSave(edited: BookmarkNode[]) {
    if (!file || !('isElectron' in file) || !file.path) return
    setSaveStatus('saving')
    try {
      const fullPath = file.path
      const result = await window.electronAPI!.bookmarks.write({
        sourcePath: fullPath,
        overwrite: true,
        bookmarks: edited
      })
      if (result.success) {
        setSaveStatus('saved')
        setMode('view')
        setEditingBookmarks([])
        const updated = await window.electronAPI!.bookmarks.read({
          path: result.outputPath
        })
        setBookmarks(updated.bookmarks)
        setPageCount(updated.page_count)
      }
    } catch (err: any) {
      setSaveStatus('error')
      setError(err.message || 'Failed to save bookmarks.')
    } finally {
      setSaveStatus(prev => prev !== 'error' ? 'idle' : prev)
    }
  }

  const handleClearFile = () => {
    setFile(null)
    setBookmarks([])
    setPageCount(0)
    setFetchStatus('idle')
    setHasUnsavedChanges(false)
    setError(null)
    setMode('view')
    setEditingBookmarks([])
    setNeedsOcr(false)
    setSaveStatus('idle')
  }

  const renderContent = () => {
    if (fetchStatus === 'loading') {
      return (
        <div className="flex-1 flex flex-col items-center justify-center">
          <svg className="w-8 h-8 text-violet-500 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="text-sm text-zinc-400">Loading bookmarks...</span>
        </div>
      )
    }

    if (fetchStatus === 'error') {
      return (
        <div className="flex-1 flex flex-col items-center justify-center">
          <svg className="w-10 h-10 text-red-500 mb-4" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-zinc-300 text-sm mb-4">Failed to read bookmarks</p>
          <button 
            onClick={() => file && loadBookmarks(file)}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      )
    }

    if (mode === 'generating') {
      return (
        <div className="flex-1 flex flex-col items-center justify-center">
          <svg className="w-8 h-8 text-violet-500 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="text-sm text-zinc-400">Analyzing PDF structure...</span>
        </div>
      )
    }

    if (mode === 'editing') {
      return (
        <BookmarkEditor
          pageCount={pageCount}
          initialBookmarks={editingBookmarks}
          onSave={handleSave}
          onCancel={() => {
            setMode('view')
            setEditingBookmarks([])
          }}
          forceEnableSave={editingBookmarks !== bookmarks}
        />
      )
    }

    if (bookmarks.length === 0) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center max-w-sm mx-auto text-center">
          <svg className="w-12 h-12 text-zinc-500 mb-4" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
          </svg>
          <h3 className="text-lg font-semibold text-zinc-200 mb-2">No bookmarks found</h3>
          <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
            This PDF has no table of contents. Click Generate Bookmarks to create one automatically based on heading detection.
          </p>
          <button disabled className="px-5 py-2.5 bg-violet-500 text-white rounded-xl text-sm font-medium transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed">
            Generate Bookmarks
          </button>
        </div>
      )
    }

    const flatCount = (nodes: BookmarkNode[]): number => {
      return nodes.reduce((acc, node) => acc + 1 + flatCount(node.children), 0)
    }

    return (
      <div className="flex flex-col flex-1 min-h-0 bg-zinc-950/50 rounded-xl border border-zinc-800/50 overflow-hidden">
        <div className="px-4 py-2 border-b border-zinc-800/50 bg-zinc-900/50 flex justify-between items-center shrink-0">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Table of Contents</span>
          <span className="text-xs text-zinc-500">{flatCount(bookmarks)} bookmarks</span>
        </div>
        <div className="flex-1 overflow-y-auto p-2 custom-scrollbar">
          {bookmarks.map((node, i) => (
            <BookmarkTreeNode 
              key={`${node.page}-${node.title}-${i}`} 
              node={node} 
              depth={0} 
              onJumpToPage={(p) => console.log('Jump to', p)} 
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-6 gap-6">
      {!file ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
            onClick={handleFilePick}
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
        <div className="flex-1 min-h-0 flex flex-col gap-6 w-full">
          {/* Top Bar */}
          <div className="shrink-0 flex items-center justify-between p-4 bg-zinc-950/50 border border-zinc-800 rounded-xl relative">
            {saveStatus === 'saved' && (
              <div className="absolute -top-3 right-4 bg-emerald-500 text-white text-xs font-bold px-2 py-1 rounded-md shadow-md flex items-center gap-1 animate-in slide-in-from-top-2 fade-in">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
                Saved
              </div>
            )}
            <div className="flex items-center gap-3 min-w-0">
              <svg className="w-8 h-8 text-red-400 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-zinc-200 truncate max-w-md">{file.name}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{formatBytes(file.size)} &bull; {pageCount} pages</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {mode === 'view' && bookmarks.length > 0 && (
                <button
                  onClick={() => { setEditingBookmarks(bookmarks); setMode('editing') }}
                  className="px-4 py-2 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 rounded-lg text-sm font-medium transition-colors"
                >
                  Edit Bookmarks
                </button>
              )}
              <button
                disabled={!(file && 'isElectron' in file && file.path && mode === 'view' && fetchStatus === 'idle')}
                onClick={handleGenerate}
                className="px-4 py-2 bg-violet-500 text-white rounded-lg text-sm font-medium transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {mode === 'generating' ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                    Analyzing...
                  </>
                ) : 'Generate Bookmarks'}
              </button>
              <div className="w-px h-6 bg-zinc-800"></div>
              <button
                onClick={handleFilePick}
                className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer"
              >
                Change File
              </button>
            </div>
          </div>

          {mode === 'view' && needsOcr && (
            <div className="shrink-0 p-3 bg-amber-950/20 border border-amber-800/40 rounded-xl flex items-start gap-3 relative">
              <button onClick={() => setNeedsOcr(false)} className="absolute top-3 right-3 text-amber-500/70 hover:text-amber-400"><svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>
              <svg className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              <div>
                <h4 className="text-sm font-semibold text-amber-500">OCR Required</h4>
                <p className="text-xs text-amber-400/80 mt-1 leading-relaxed">No text layer detected. Run OCR on this PDF first, then try generating bookmarks again.</p>
              </div>
            </div>
          )}

          {/* Main Content Area */}
          <div className="flex-1 min-h-0 flex flex-col w-full max-w-4xl mx-auto">
            {renderContent()}
          </div>
        </div>
      )}
    </div>
  )
}
