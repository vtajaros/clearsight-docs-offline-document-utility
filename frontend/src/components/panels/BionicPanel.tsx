// frontend/src/components/panels/BionicPanel.tsx
import { useState, useEffect } from 'react'
import type { DragEvent } from 'react'
import { type CompletionModal, type ElectronFile, formatBytes, pickFiles } from '../../types'
import { useJobWebSocket } from '../../hooks/useJobWebSocket'

interface BionicPanelProps {
  base: string
  loading: boolean
  setLoading: (v: boolean) => void
  setError: (v: string | null) => void
  setModal: (m: CompletionModal) => void
  port: number | null
  setHasUnsavedChanges?: (v: boolean) => void
}

export function BionicPanel({
  base, loading, setLoading, setError, setModal, port, setHasUnsavedChanges
}: BionicPanelProps) {
  const [file, setFile] = useState<ElectronFile | File | null>(null)
  const [boldRatio, setBoldRatio] = useState<number>(0.5)
  const [jobId, setJobId] = useState<string | null>(null)

  const { progress, error: wsError } = useJobWebSocket(port, jobId, '/ws/bionic')

  useEffect(() => {
    if (wsError) {
      setError(wsError)
    }
  }, [wsError, setError])

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault() }
  const handleDragLeave = () => {}
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0]
      if (dropped.type === 'application/pdf' || dropped.name.endsWith('.pdf')) {
        setFile(dropped)
        setHasUnsavedChanges?.(true)
        setError(null)
      } else {
        setError('Only PDF files are supported.')
      }
    }
  }

  const handleBionicSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)

    const uuid = crypto.randomUUID()
    setJobId(uuid)

    const formData = new FormData()
    if ('isElectron' in file && file.isElectron) {
      formData.append('file_path', (file as ElectronFile).path)
    } else {
      formData.append('file', file)
    }
    formData.append('bold_ratio', String(boldRatio))
    formData.append('job_id', uuid)

    try {
      const token = window.electronAPI?.getToken ? await window.electronAPI.getToken() : ''
      const res = await fetch(`${base}/api/bionic`, {
        method: 'POST',
        body: formData,
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || 'Bionic conversion failed.')
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const stem = file.name.replace(/\.pdf$/i, '')
      setModal({
        open: true,
        title: 'Bionic Conversion Complete',
        subtitle: 'Your bionic reading HTML file is ready to export.',
        onExport: () => {
          const a = document.createElement('a')
          a.href = url
          a.download = `${stem}_bionic.html`
          a.click()
          setModal({ open: false, title: '', subtitle: '', onExport: () => {} })
          setHasUnsavedChanges?.(false)
          setJobId(null)
        }
      })
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during bionic conversion.')
    } finally {
      setLoading(false)
      setJobId(null)
    }
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-6 gap-6">
      {!file ? (
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={async () => {
              const result = await pickFiles({ filters: [{ name: 'PDF Files', extensions: ['pdf'] }], accept: 'application/pdf', multiple: false })
              if (result && result[0]) {
                setFile(result[0])
                setHasUnsavedChanges?.(true)
                setError(null)
              }
            }}
            className="w-full max-w-3xl mx-auto mt-12 h-64 border-2 border-dashed border-[#3a3a3a] bg-[#1a1a1a] rounded-xl flex flex-col items-center justify-center hover:bg-[#222222] transition-colors cursor-pointer"
          >
            <svg className="w-10 h-10 text-zinc-500 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-300">Drag &amp; drop your PDF here</p>
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
              <p className="text-sm font-semibold text-zinc-200 truncate max-w-md">{file.name}</p>
              <p className="text-xs text-zinc-500 mt-0.5">{formatBytes(file.size)}</p>
            </div>
          </div>
          <button
            onClick={() => { setFile(null); setHasUnsavedChanges?.(false); setError(null) }}
            className="p-1.5 text-zinc-500 hover:text-zinc-300 rounded-lg hover:bg-zinc-850 transition-all cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}

      <div className="shrink-0 flex flex-col gap-6 w-full max-w-4xl mx-auto">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Bold Ratio
            </label>
            <span className="text-xs font-medium text-violet-400">{Math.round(boldRatio * 100)}% bolded</span>
          </div>
          <input
            type="range"
            min={0.1}
            max={0.9}
            step={0.05}
            value={boldRatio}
            onChange={(e) => setBoldRatio(parseFloat(e.target.value))}
            className="w-full h-2 rounded-full appearance-none cursor-pointer bg-zinc-800 accent-violet-500"
          />
          <div className="flex justify-between text-xs text-zinc-600">
            <span>Light (10%)</span>
            <span>Heavy (90%)</span>
          </div>
        </div>

        <button
          disabled={!file || loading}
          onClick={handleBionicSubmit}
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
          ) : 'Convert to Bionic Reading'}
        </button>

        {loading && progress && progress.total > 0 && (
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-zinc-400">
                {progress.message || `Page ${progress.current} of ${progress.total}`}
              </span>
              <span className="text-xs font-medium text-violet-400">
                {Math.round((progress.current / progress.total) * 100)}%
              </span>
            </div>
            <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${(progress.current / progress.total) * 100}%`,
                  background: 'linear-gradient(90deg, #7c3aed, #a855f7, #c084fc)',
                  boxShadow: '0 0 8px rgba(167, 85, 247, 0.6)',
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
