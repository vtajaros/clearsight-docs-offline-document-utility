// frontend/src/App.tsx
import { useState, useEffect } from 'react'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { TitleBar } from './components/TitleBar'
import { OcrPanel } from './components/panels/OcrPanel'
import { MergePanel } from './components/panels/MergePanel'
import { SplitPanel } from './components/panels/SplitPanel'
import { CompressPanel } from './components/panels/CompressPanel'
import { PdfToImagesPanel } from './components/panels/PdfToImagesPanel'
import { ImageToPdfPanel } from './components/panels/ImageToPdfPanel'
import { DeletePagesPanel } from './components/panels/DeletePagesPanel'
import { BookmarkPanel } from './components/panels/BookmarkPanel'
import { BionicPanel } from './components/panels/BionicPanel'
import { NavigationConfirmModal } from './components/NavigationConfirmModal'
import { useNavigationGuard } from './hooks/useNavigationGuard'
import type {
  ActiveTab, OcrLanguage, OcrFormat, OcrAccuracy, CompletionModal, ElectronFile
} from './types'

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('image-to-pdf')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // OCR state (managed in App.tsx to support background websocket thread lifecycle)
  const [ocrFile, setOcrFile] = useState<ElectronFile | File | null>(null)
  const [ocrLanguage, setOcrLanguage] = useState<OcrLanguage>('eng')
  const [ocrFormat, setOcrFormat] = useState<OcrFormat>('txt')
  const [ocrAccuracy, setOcrAccuracy] = useState<OcrAccuracy>('balanced')
  const [ocrTextResult, setOcrTextResult] = useState<string | null>(null)
  const [ocrCopied, setOcrCopied] = useState<boolean>(false)

  const {
    setHasUnsavedChanges,
    isModalOpen,
    handleNavClick,
    confirmNav,
    cancelNav
  } = useNavigationGuard((newTab) => {
    if (newTab !== 'ocr') {
      setOcrFile(null) 
    }
    setActiveTab(newTab)
    setError(null)
  })

  const handleTabChange = (newTab: ActiveTab) => {
    if (activeTab === newTab) return
    const shouldGuard = activeTab === 'ocr' && ocrFile !== null
    handleNavClick(newTab, shouldGuard)
  }

  // Completion Modal State
  const [modal, setModal] = useState<CompletionModal>({
    open: false,
    title: '',
    subtitle: '',
    onExport: () => {}
  })

  // File Saved Toast State
  const [toast, setToast] = useState<{ visible: boolean; path: string } | null>(null)

  useEffect(() => {
    if (window.electronAPI?.onFileSaved) {
      const unsubscribe = window.electronAPI.onFileSaved((savePath) => {
        setToast({ visible: true, path: savePath })
      })
      return unsubscribe
    }
  }, [])

  useEffect(() => {
    if (toast?.visible) {
      const t = setTimeout(() => {
        setToast(null)
      }, 6000)
      return () => clearTimeout(t)
    }
  }, [toast])

  // Backend Port logic
  const [port, setPort] = useState<number | null>(null)

  useEffect(() => {
    if (window.electronAPI?.getPort) {
      window.electronAPI.getPort().then((p) => setPort(p))
    } else {
      setPort(8000)
    }
  }, [])

  const base = `http://127.0.0.1:${port}`

  if (port === null) {
    return (
      <div className="flex flex-col items-center justify-center w-full h-screen bg-[#0a0a0a] text-zinc-100 select-none">
        <div className="flex flex-col items-center gap-4">
          <svg className="w-12 h-12 text-violet-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <div className="text-sm font-medium text-zinc-400">Starting Clearsight...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="app-root flex w-full h-full bg-[#0a0a0a] text-zinc-100 select-none">
      <TitleBar />
      
      {/* Left Sidebar */}
      <aside className={`${sidebarCollapsed ? 'w-[60px]' : 'w-[220px]'} bg-zinc-900 border-r border-zinc-800 flex flex-col justify-between h-full transition-all duration-200`}>
        <div>
          {/* Header */}
          <div className="p-4 border-b border-zinc-800 flex items-center justify-between gap-2 min-h-[57px]">
            {!sidebarCollapsed && (
              <>
                <svg className="w-5 h-5 text-violet-500 shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                </svg>
                <span className="font-bold text-sm tracking-wide text-zinc-100 flex-1">ClearSight Docs</span>
              </>
            )}
            <button
              onClick={() => setSidebarCollapsed(p => !p)}
              className="text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-md p-1.5 transition-colors shrink-0"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? <PanelLeftOpen size={16} strokeWidth={1.75} /> : <PanelLeftClose size={16} strokeWidth={1.75} />}
            </button>
          </div>
 
          {/* Navigation */}
          <nav className="p-2 space-y-0.5">
            {/* Image to PDF */}
            <button
              onClick={() => handleTabChange('image-to-pdf')}
              title="Image to PDF"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'image-to-pdf'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
              </svg>
              {!sidebarCollapsed && 'Image to PDF'}
            </button>
 
            {/* PDF to Images */}
            <button
              onClick={() => handleTabChange('pdf-to-images')}
              title="PDF to Images"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'pdf-to-images'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
              </svg>
              {!sidebarCollapsed && 'PDF to Images'}
            </button>
 
            {/* Merge PDFs */}
            <button
              onClick={() => handleTabChange('merge')}
              title="Merge PDFs"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'merge'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              {!sidebarCollapsed && 'Merge PDFs'}
            </button>
 
            {/* Delete Pages */}
            <button
              onClick={() => handleTabChange('delete-pages')}
              title="Delete PDF Pages"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'delete-pages'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
              {!sidebarCollapsed && 'Delete Pages'}
            </button>
 
            {/* Split PDF */}
            <button
              onClick={() => handleTabChange('split')}
              title="Split PDF"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'split'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75" />
              </svg>
              {!sidebarCollapsed && 'Split PDF'}
            </button>
 
            {/* Compress PDF */}
            <button
              onClick={() => handleTabChange('compress')}
              title="Compress PDF"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'compress'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
              </svg>
              {!sidebarCollapsed && 'Compress PDF'}
            </button>
 
            {/* OCR PDF */}
            <button
              onClick={() => handleTabChange('ocr')}
              title="OCR PDF"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'ocr'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              {!sidebarCollapsed && 'OCR PDF'}
            </button>
 
            {/* Bookmarks */}
            <button
              onClick={() => handleTabChange('bookmarks')}
              title="Bookmarks"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'bookmarks'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
              </svg>
              {!sidebarCollapsed && 'Bookmarks'}
            </button>
 
            {/* Bionic Reading */}
            <button
              onClick={() => handleTabChange('bionic')}
              title="Bionic Reading"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'bionic'
                  ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent'
              }`}
            >
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" /></svg>
              {!sidebarCollapsed && 'Bionic Reading'}
            </button>
          </nav>
        </div>
 
        {/* Footer — copyright */}
        <div className="p-4 border-t border-zinc-800 flex items-center justify-center text-xs text-zinc-500 select-none">
          <span>{sidebarCollapsed ? '©' : '© vtajaros'}</span>
        </div>
      </aside>
 
      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden flex flex-col p-6">
        <div className="w-full h-full flex flex-col gap-6">
          {/* Header block inside main */}
          <div className="shrink-0">
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              {activeTab === 'ocr' && 'Optical Character Recognition (OCR)'}
              {activeTab === 'merge' && 'Merge PDF Documents'}
              {activeTab === 'split' && 'Split PDF Document'}
              {activeTab === 'delete-pages' && 'Delete PDF Pages'}
              {activeTab === 'compress' && 'Compress PDF Document'}
              {activeTab === 'pdf-to-images' && 'Convert PDF to Images'}
              {activeTab === 'image-to-pdf' && 'Convert Images to PDF'}
              {activeTab === 'bookmarks' && 'PDF Bookmarks'}
              {activeTab === 'bionic' && 'Bionic Reading Converter'}
            </h1>
            <p className="text-sm text-zinc-400 mt-1">
              {activeTab === 'ocr' && 'Convert non-searchable or scanned PDF documents into clean selectable text or searchable PDFs.'}
              {activeTab === 'merge' && 'Combine multiple PDF files into a single, cohesive document in the exact order you need.'}
              {activeTab === 'split' && 'Extract specific page ranges or break down a document into individual single-page files.'}
              {activeTab === 'delete-pages' && 'Selectively remove pages from your PDF document.'}
              {activeTab === 'compress' && 'Reduce the file size of your PDF document without significantly losing quality.'}
              {activeTab === 'pdf-to-images' && 'Extract pages from a PDF and convert them into a ZIP archive of high-quality images.'}
              {activeTab === 'image-to-pdf' && 'Combine multiple images (JPG/PNG) into a single unified PDF document.'}
              {activeTab === 'bookmarks' && 'View, generate, and edit the table of contents for any PDF.'}
              {activeTab === 'bionic' && 'Convert a PDF into a bionic-formatted HTML file to improve reading speed and focus.'}
            </p>
          </div>
 
          {/* Error Message */}
          {error && (
            <div className="shrink-0 p-4 bg-red-950/20 border border-red-800/40 rounded-xl flex items-start gap-3">
              <svg className="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              <div>
                <h4 className="text-sm font-semibold text-red-400">Execution Error</h4>
                <p className="text-xs text-red-300/80 mt-1 leading-relaxed">{error}</p>
              </div>
            </div>
          )}
 
          {/* Panels */}
          <div className="flex-1 min-h-0 flex flex-col">
          {activeTab === 'ocr' && (
            <OcrPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              error={error}
              setError={setError}
              setModal={setModal}
              ocrFile={ocrFile}
              setOcrFile={setOcrFile}
              ocrLanguage={ocrLanguage}
              setOcrLanguage={setOcrLanguage}
              ocrFormat={ocrFormat}
              setOcrFormat={setOcrFormat}
              ocrAccuracy={ocrAccuracy}
              setOcrAccuracy={setOcrAccuracy}
              ocrTextResult={ocrTextResult}
              setOcrTextResult={setOcrTextResult}
              ocrCopied={ocrCopied}
              setOcrCopied={setOcrCopied}
              port={port}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}
 
          {activeTab === 'merge' && (
            <MergePanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}
 
          {activeTab === 'split' && (
            <SplitPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}
 
          {activeTab === 'delete-pages' && (
            <DeletePagesPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}
 
          {activeTab === 'compress' && (
            <CompressPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}
 
          {activeTab === 'pdf-to-images' && (
            <PdfToImagesPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}
 
          {activeTab === 'image-to-pdf' && (
            <ImageToPdfPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}

          {activeTab === 'bookmarks' && (
            <BookmarkPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}

          {activeTab === 'bionic' && (
            <BionicPanel
              base={base}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
              setModal={setModal}
              port={port}
              setHasUnsavedChanges={setHasUnsavedChanges}
            />
          )}
          </div>
        </div>
      </main>
 
      {/* Completion Modal Overlay */}
      {modal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setModal(m => ({ ...m, open: false }))} />
          <div className="relative bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl flex flex-col items-center gap-4 min-w-[320px] max-w-sm animate-in fade-in zoom-in-95 duration-200">
            <button
              onClick={() => setModal(m => ({ ...m, open: false }))}
              className="absolute top-4 right-4 p-1.5 text-zinc-500 hover:text-zinc-300 rounded-lg hover:bg-zinc-800 transition-all cursor-pointer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mb-2">
              <svg className="w-8 h-8 text-emerald-400" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>
            <div className="text-center">
              <h3 className="text-xl font-bold text-zinc-100">{modal.title}</h3>
              <p className="text-sm text-zinc-400 mt-1">{modal.subtitle}</p>
            </div>
            <button
              onClick={modal.onExport}
              className="w-full mt-4 py-3 px-4 bg-violet-500 hover:bg-violet-600 text-white font-semibold text-sm rounded-xl transition-all shadow-md shadow-violet-950/20 cursor-pointer"
            >
              Export File
            </button>
          </div>
        </div>
      )}
 
      {/* File Saved Toast Notification */}
      {toast?.visible && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-4 bg-zinc-900/95 backdrop-blur-md border border-emerald-500/30 rounded-xl p-4 shadow-2xl max-w-md animate-in fade-in slide-in-from-bottom-5 duration-300">
          <div className="w-9 h-9 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-zinc-100">File Saved Successfully</h4>
            <p className="text-[11px] text-zinc-400 mt-1 font-mono bg-zinc-950/60 p-2 rounded-lg border border-zinc-850/80 break-all select-text selection:bg-emerald-500/20">
              {toast.path}
            </p>
          </div>
          <button
            onClick={() => setToast(null)}
            className="text-zinc-500 hover:text-zinc-300 p-1 rounded-lg hover:bg-zinc-800/60 transition-colors shrink-0 align-self-start cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Navigation Confirm Modal */}
      <NavigationConfirmModal
        isOpen={isModalOpen}
        onCancel={cancelNav}
        onConfirm={confirmNav}
      />
    </div>
  )
}
