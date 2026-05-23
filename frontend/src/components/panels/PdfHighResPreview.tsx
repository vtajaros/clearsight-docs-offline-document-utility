import { useRef, useEffect, useState } from 'react'
import * as pdfjsLib from 'pdfjs-dist'

export function PdfHighResPreview({
  pdfDoc,
  pageNumber,
  isMarked,
  onToggleMark
}: {
  pdfDoc: pdfjsLib.PDFDocumentProxy
  pageNumber: number
  isMarked: boolean
  onToggleMark: () => void
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const renderTaskRef = useRef<pdfjsLib.RenderTask | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)

    async function renderPage() {
      if (!canvasRef.current) return

      try {
        const page = await pdfDoc.getPage(pageNumber)
        if (!active) return

        // Cancel previous render task if it's still running
        if (renderTaskRef.current) {
          try {
            renderTaskRef.current.cancel()
          } catch (e) {
            // Ignore cancel errors
          }
        }

        const viewport = page.getViewport({ scale: 1.5 }) // High-res scale
        const canvas = canvasRef.current
        const context = canvas.getContext('2d')
        if (!context) return

        canvas.width = viewport.width
        canvas.height = viewport.height

        const renderContext = {
          canvasContext: context,
          viewport: viewport,
          canvas: canvas
        }

        const renderTask = page.render(renderContext)
        renderTaskRef.current = renderTask

        await renderTask.promise
        if (active) {
          setLoading(false)
        }
      } catch (err: any) {
        if (err.name === 'RenderingCancelledException') {
          // Expected when rapidly clicking through pages
          console.log(`Render cancelled for page ${pageNumber}`)
        } else {
          console.error(`Failed to render high-res page ${pageNumber}`, err)
        }
      } finally {
        if (renderTaskRef.current && active) {
          renderTaskRef.current = null
        }
      }
    }

    renderPage()

    return () => {
      active = false
      if (renderTaskRef.current) {
        try {
          renderTaskRef.current.cancel()
        } catch (e) {}
      }
    }
  }, [pdfDoc, pageNumber])

  return (
    <div className="flex flex-col h-full bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-inner relative">
      {/* Top Header */}
      <div className="flex items-center justify-between p-3 bg-zinc-900 border-b border-zinc-800 shrink-0 z-10">
        <h4 className="text-sm font-semibold text-zinc-200">Page {pageNumber} Preview</h4>
        
        <button
          onClick={onToggleMark}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            isMarked 
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30' 
              : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-zinc-100 border border-transparent'
          }`}
        >
          {isMarked ? (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
              Marked for Deletion
            </>
          ) : (
            <>
              <svg className="w-4 h-4 opacity-70" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
              Mark for Deletion
            </>
          )}
        </button>
      </div>

      {/* Preview Container */}
      <div className="flex-1 relative overflow-auto custom-scrollbar bg-black/40 flex items-center justify-center p-4">
        {loading && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-zinc-950/50 backdrop-blur-sm">
            <svg className="w-8 h-8 text-violet-500 animate-spin mb-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-sm text-zinc-400 font-medium tracking-wide">Rendering preview...</span>
          </div>
        )}
        <canvas
          ref={canvasRef}
          className={`max-w-full h-auto object-contain bg-white shadow-2xl transition-opacity duration-300 ${loading ? 'opacity-30' : 'opacity-100'} ${isMarked ? 'opacity-50 grayscale sepia-[.3] hue-rotate-[-50deg] saturate-[3]' : ''}`}
        />
      </div>
    </div>
  )
}
