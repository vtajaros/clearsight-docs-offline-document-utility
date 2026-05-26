// frontend/src/components/panels/OcrPanel.tsx
import { useState, useEffect } from 'react'
import type { DragEvent } from 'react'
import {
  type OcrLanguage, type OcrFormat, type OcrAccuracy,
  type CompletionModal, formatBytes, pickFiles,
} from '../../types'
import { useOcrWebSocket } from '../../hooks/useOcrWebSocket'

interface OcrPanelProps {
  base: string
  loading: boolean
  setLoading: (v: boolean) => void
  error: string | null
  setError: (v: string | null) => void
  setModal: (m: CompletionModal) => void
  ocrFile: any
  setOcrFile: (f: any) => void
  ocrLanguage: OcrLanguage
  setOcrLanguage: (l: OcrLanguage) => void
  ocrFormat: OcrFormat
  setOcrFormat: (f: OcrFormat) => void
  ocrAccuracy: OcrAccuracy
  setOcrAccuracy: (a: OcrAccuracy) => void
  ocrTextResult: string | null
  setOcrTextResult: (t: string | null) => void
  ocrCopied: boolean
  setOcrCopied: (v: boolean) => void
  port: number | null
  setHasUnsavedChanges?: (v: boolean) => void
}

export function OcrPanel({
  base, loading, setLoading, error: _error, setError, setModal,
  ocrFile, setOcrFile, ocrLanguage, setOcrLanguage, ocrFormat, setOcrFormat,
  ocrAccuracy, setOcrAccuracy, ocrTextResult, setOcrTextResult,
  ocrCopied, setOcrCopied, port, setHasUnsavedChanges
}: OcrPanelProps) {
  const [jobId, setJobId] = useState<string | null>(null)
  const { progress, error: wsError } = useOcrWebSocket(port, jobId)

  useEffect(() => {
    if (wsError) {
      setError(wsError)
    }
  }, [wsError, setError])

  const resetOcrOutputs = () => {
    setOcrTextResult(null)
    setError(null)
  }

  const handleOcrDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }
  const handleOcrDragLeave = () => {}
  const handleOcrDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        setOcrFile(file); resetOcrOutputs(); setHasUnsavedChanges?.(true)
      } else {
        setError('Only PDF files are supported for OCR.')
      }
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setOcrCopied(true)
    setTimeout(() => setOcrCopied(false), 2000)
  }

  const downloadTextFile = (text: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = ocrFile ? `${ocrFile.name.replace(/\.pdf$/i, '')}_ocr.txt` : 'ocr_result.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleOcrSubmit = async () => {
    if (!ocrFile) return
    setLoading(true)
    setError(null)
    setOcrTextResult(null)

    const uuid = crypto.randomUUID()
    setJobId(uuid)

    const formData = new FormData()
    if (ocrFile.isElectron) {
      formData.append('file_path', ocrFile.path)
    } else {
      formData.append('file', ocrFile)
    }
    formData.append('language', ocrLanguage)
    formData.append('output_format', ocrFormat)
    formData.append('accuracy_mode', ocrAccuracy)
    formData.append('job_id', uuid)

    try {
      const res = await fetch(`${base}/api/ocr`, { method: 'POST', body: formData })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || 'OCR processing failed.')
      }

      if (ocrFormat === 'txt') {
        const text = await res.text()
        setOcrTextResult(text)
        setModal({
          open: true,
          title: 'OCR Complete',
          subtitle: 'Your extracted text is ready to export.',
          onExport: () => {
            downloadTextFile(text)
            setModal({ open: false, title: '', subtitle: '', onExport: () => {} })
            setHasUnsavedChanges?.(false)
            setJobId(null)
          }
        })
      } else {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const baseName = ocrFile.name.replace(/\.pdf$/i, '')
        setModal({
          open: true,
          title: 'OCR Complete',
          subtitle: 'Your searchable PDF is ready to export.',
          onExport: () => {
            const a = document.createElement('a')
            a.href = url; a.download = `${baseName}_ocr.pdf`; a.click()
            setModal({ open: false, title: '', subtitle: '', onExport: () => {} })
            setHasUnsavedChanges?.(false)
            setJobId(null)
          }
        })
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during OCR.')
    } finally {
      setLoading(false)
      setJobId(null)
    }
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-6 gap-6">
      {!ocrFile ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onDragOver={handleOcrDragOver}
            onDragLeave={handleOcrDragLeave}
            onDrop={handleOcrDrop}
            onClick={async () => {
              const result = await pickFiles({ filters: [{ name: 'PDF Files', extensions: ['pdf'] }], accept: 'application/pdf', multiple: false })
              if (result && result[0]) { setOcrFile(result[0]); resetOcrOutputs(); setHasUnsavedChanges?.(true) }
            }}
            className="w-full max-w-3xl mx-auto mt-12 h-64 border-2 border-dashed border-[#3a3a3a] bg-[#1a1a1a] rounded-xl flex flex-col items-center justify-center hover:bg-[#222222] transition-colors cursor-pointer"
          >
            <svg className="w-10 h-10 text-zinc-500 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-300">Drag & drop your scanned PDF here</p>
              <p className="text-xs text-zinc-500 mt-1">or click to browse files</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="shrink-0 flex items-center justify-between p-4 bg-zinc-950/50 border border-zinc-800 rounded-xl w-full max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <svg className="w-8 h-8 text-red-400 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-zinc-200 truncate max-w-md">{ocrFile.name}</p>
              <p className="text-xs text-zinc-500 mt-0.5">{formatBytes(ocrFile.size)}</p>
            </div>
          </div>
          <button onClick={() => { setOcrFile(null); resetOcrOutputs(); setHasUnsavedChanges?.(false); }} className="p-1.5 text-zinc-500 hover:text-zinc-300 rounded-lg hover:bg-zinc-850 transition-all cursor-pointer">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}

      <div className="shrink-0 flex flex-col gap-6 w-full max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">OCR Language</label>
            <select value={ocrLanguage} onChange={(e) => setOcrLanguage(e.target.value as OcrLanguage)} className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-sm rounded-lg px-3 py-2.5 outline-none focus:border-violet-500 transition-all cursor-pointer">
              <option value="eng">English (eng)</option>
              <option value="fil">Filipino (fil)</option>
              <option value="jpn">Japanese (jpn)</option>
              <option value="chi_sim">Chinese Simplified (chi_sim)</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">Output Format</label>
            <div className="flex gap-2">
              {(['txt', 'pdf'] as OcrFormat[]).map((fmt) => (
                <button key={fmt} onClick={() => setOcrFormat(fmt)} className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border text-center transition-all ${ocrFormat === fmt ? 'border-violet-500 bg-violet-500/10 text-violet-400' : 'border-zinc-800 bg-zinc-950/40 text-zinc-400 hover:text-zinc-300'}`}>
                  {fmt === 'txt' ? 'Plain Text (.txt)' : 'Searchable PDF'}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">Accuracy Mode</label>
            <div className="flex bg-zinc-950/50 p-1 border border-zinc-800 rounded-lg">
              {(['fast', 'balanced', 'accurate'] as OcrAccuracy[]).map((mode) => (
                <button key={mode} onClick={() => setOcrAccuracy(mode)} className={`flex-1 py-1.5 text-xs font-medium rounded-md capitalize transition-all ${ocrAccuracy === mode ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-400'}`}>
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          disabled={!ocrFile || loading}
          onClick={handleOcrSubmit}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-violet-500 hover:bg-violet-600 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white font-medium text-sm rounded-xl transition-all shadow-md shadow-violet-950/10 cursor-pointer"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {progress && progress.total > 0
                ? `Page ${progress.current} of ${progress.total} — ${progress.message}`
                : 'Processing...'}
            </>
          ) : 'Perform Optical Character Recognition'}
        </button>

        {loading && progress && progress.total > 0 && (
          <div className="w-full bg-zinc-800 rounded-full h-1.5">
            <div className="bg-violet-500 h-1.5 rounded-full transition-all duration-300" style={{ width: `${(progress.current / progress.total) * 100}%` }} />
          </div>
        )}
      </div>

      {ocrTextResult !== null && (
        <div className="flex-1 min-h-0 flex flex-col space-y-3 pt-4 border-t border-zinc-800 w-full max-w-4xl mx-auto">
          <div className="shrink-0 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Extracted Text Output</span>
            <button onClick={() => copyToClipboard(ocrTextResult)} className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-zinc-200 rounded-lg transition-all border border-zinc-700/50 cursor-pointer">
              {ocrCopied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <pre className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-4 bg-zinc-950 border border-zinc-800 rounded-xl font-mono text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">
            {ocrTextResult || '(No text extracted from document)'}
          </pre>
        </div>
      )}
    </div>
  )
}
