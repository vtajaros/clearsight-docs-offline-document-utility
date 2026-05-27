// frontend/src/components/panels/SplitPanel.tsx
import { useState, useRef } from 'react'
import type { DragEvent } from 'react'
import { type SplitMode, type CompletionModal, formatBytes, pickFiles } from '../../types'
import { useSimulatedProgress } from '../../hooks/useSimulatedProgress'
import { ProgressBar } from '../ProgressBar'

interface SplitPanelProps {
  base: string
  loading: boolean
  setLoading: (v: boolean) => void
  setError: (v: string | null) => void
  setModal: (m: CompletionModal) => void
  setHasUnsavedChanges?: (v: boolean) => void
}

export function SplitPanel({ base, loading, setLoading, setError, setModal, setHasUnsavedChanges }: SplitPanelProps) {
  const [splitMode, setSplitMode] = useState<SplitMode>('range')
  const [splitFile, setSplitFile] = useState<any | null>(null)
  const [splitStartPage, setSplitStartPage] = useState(1)
  const [splitEndPage, setSplitEndPage] = useState(2)

  const { progress, label: progressLabel, start: startProgress, finish: finishProgress, cancel: cancelProgress } = useSimulatedProgress()

  const resetSplitOutputs = () => setError(null)

  const handleSplitDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault() }
  const handleSplitDragLeave = () => {}
  const handleSplitDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) { setSplitFile(file); resetSplitOutputs(); setHasUnsavedChanges?.(true) }
      else setError('Only PDF files are supported.')
    }
  }

  const handleSplitSubmit = async () => {
    if (!splitFile) return
    setLoading(true); setError(null)

    startProgress([
      { target: 20, label: 'Reading PDF...', delayMs: 300 },
      { target: 60, label: 'Splitting pages...', delayMs: 900 },
      { target: 85, label: 'Writing output...', delayMs: 1800 },
      { target: 93, label: 'Finalizing...', delayMs: 3000 },
    ])

    const formData = new FormData()
    if (splitFile.isElectron) formData.append('file_path', splitFile.path)
    else formData.append('file', splitFile)

    const endpoint = splitMode === 'range' ? '/api/split/range' : '/api/split/pages'
    if (splitMode === 'range') {
      formData.append('start_page', splitStartPage.toString())
      formData.append('end_page', splitEndPage.toString())
    }

    try {
      const res = await fetch(`${base}${endpoint}`, { method: 'POST', body: formData })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || 'Splitting failed.')
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const baseName = splitFile.name.replace(/\.pdf$/i, '')
      const downloadName = splitMode === 'range' ? `${baseName}_p${splitStartPage}-${splitEndPage}.pdf` : `${baseName}_pages.zip`
      const subtitleText = splitMode === 'range' ? 'Your split PDF is ready to export.' : 'Your PDF pages are ready to export as ZIP.'

      finishProgress()
      await new Promise(r => setTimeout(r, 400))

      setModal({
        open: true, title: 'Split Complete', subtitle: subtitleText,
        onExport: () => {
          const a = document.createElement('a'); a.href = url; a.download = downloadName; a.click()
          setModal({ open: false, title: '', subtitle: '', onExport: () => {} })
          resetSplitOutputs(); setHasUnsavedChanges?.(false)
        }
      })
    } catch (err: any) {
      cancelProgress()
      setError(err.message || 'An unexpected error occurred during Split.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-6 gap-6">
      <div className="shrink-0 flex bg-zinc-950/50 p-1 border border-zinc-800 rounded-xl max-w-4xl mx-auto w-full">
        {(['range', 'pages'] as SplitMode[]).map((mode) => (
          <button key={mode} onClick={() => { setSplitMode(mode); resetSplitOutputs() }}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${splitMode === mode ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-400'}`}>
            {mode === 'range' ? 'Split by Range' : 'Split into Individual Pages'}
          </button>
        ))}
      </div>

      {!splitFile ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onDragOver={handleSplitDragOver} onDragLeave={handleSplitDragLeave} onDrop={handleSplitDrop}
            onClick={async () => {
              const result = await pickFiles({ filters: [{ name: 'PDF Files', extensions: ['pdf'] }], accept: 'application/pdf', multiple: false })
              if (result && result[0]) { setSplitFile(result[0]); resetSplitOutputs(); setHasUnsavedChanges?.(true) }
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
        <div className="flex-1 min-h-0 flex flex-col justify-center gap-6 max-w-4xl mx-auto w-full">
          <div className="flex items-center justify-between p-4 bg-zinc-950/50 border border-zinc-800 rounded-xl">
            <div className="flex items-center gap-3 min-w-0">
              <svg className="w-8 h-8 text-red-400 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-zinc-200 truncate max-w-md">{splitFile.name}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{formatBytes(splitFile.size)}</p>
              </div>
            </div>
            <button onClick={() => { setSplitFile(null); resetSplitOutputs(); setHasUnsavedChanges?.(false); cancelProgress(); }} className="p-1.5 text-zinc-500 hover:text-zinc-300 rounded-lg hover:bg-zinc-850 transition-all cursor-pointer">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
            </button>
          </div>

          <div className={`pt-2 grid grid-cols-2 gap-6 transition-all duration-200 ${splitMode === 'range' ? 'visible opacity-100' : 'invisible opacity-0'}`}>
            {[['Start Page', splitStartPage, setSplitStartPage], ['End Page', splitEndPage, setSplitEndPage]].map(([label, val, setter]: any) => (
              <div key={label} className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">{label}</label>
                <input type="number" min={1} value={val} onChange={(e) => setter(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-sm rounded-lg px-3 py-2.5 outline-none focus:border-violet-500 transition-all font-mono" />
              </div>
            ))}
          </div>

          <ProgressBar loading={loading} progress={progress} label={progressLabel} />

          <button disabled={!splitFile || loading} onClick={handleSplitSubmit}
            className="shrink-0 w-full flex items-center justify-center gap-2 py-3 px-4 bg-violet-500 hover:bg-violet-600 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white font-medium text-sm rounded-xl transition-all shadow-md shadow-violet-950/10 cursor-pointer">
            {loading ? (
              <><svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>Splitting PDF Document...</>
            ) : splitMode === 'range' ? `Extract Pages ${splitStartPage} to ${splitEndPage}` : 'Split PDF into Individual Pages'}
          </button>
        </div>
      )}
    </div>
  )
}
