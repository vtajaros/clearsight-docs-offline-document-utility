// frontend/src/components/Thumbnails.tsx
// PdfThumbnail and ImageThumbnail components, extracted from App.tsx.

import { useState, useRef, useEffect } from 'react'
import * as pdfjsLib from 'pdfjs-dist'
import { thumbnailCache, imageThumbnailCache } from '../types'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.mjs',
  import.meta.url
).href

// ---------------------------------------------------------------------------
// ImageThumbnail
// ---------------------------------------------------------------------------

export function ImageThumbnail({ file, fileId }: { file: any; fileId: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (imageThumbnailCache.has(fileId)) return

    let active = true
    async function load() {
      let url = ''
      let isBlobUrl = false
      if (file.isElectron) {
        if (window.electronAPI?.readFile) {
          const arrayBuffer = await window.electronAPI.readFile(file.path)
          if (!active) return
          const blob = new Blob([arrayBuffer])
          url = URL.createObjectURL(blob)
          isBlobUrl = true
        }
      } else {
        url = URL.createObjectURL(file)
        isBlobUrl = true
      }

      if (!url) return

      const img = new Image()
      img.onload = () => {
        const canvas = canvasRef.current
        if (!canvas) return
        const scale = Math.min(160 / img.width, 200 / img.height)
        canvas.width = img.width * scale
        canvas.height = img.height * scale
        canvas.getContext('2d')!.drawImage(img, 0, 0, canvas.width, canvas.height)
        imageThumbnailCache.set(fileId, canvas.toDataURL())
        if (isBlobUrl) URL.revokeObjectURL(url)
      }
      img.src = url
    }
    load()
    return () => { active = false }
  }, [file, fileId])

  const cached = imageThumbnailCache.get(fileId)
  if (cached) {
    return <img src={cached} alt="" className="w-full h-full object-contain" />
  }
  return <canvas ref={canvasRef} className="w-full h-full object-contain" />
}

// ---------------------------------------------------------------------------
// PdfThumbnail
// ---------------------------------------------------------------------------

export function PdfThumbnail({ file, fileId }: { file: any; fileId: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [cachedImage, setCachedImage] = useState<string | null>(thumbnailCache.get(fileId) || null)
  const [loading, setLoading] = useState<boolean>(!cachedImage)
  const [error, setError] = useState<boolean>(false)

  useEffect(() => {
    if (cachedImage) return

    let active = true
    setLoading(true)
    setError(false)

    async function load() {
      try {
        const canvas = canvasRef.current
        if (!canvas) return

        const arrayBuffer = window.electronAPI?.readFile
          ? await window.electronAPI.readFile(file.path)
          : await file.arrayBuffer()
        if (!active) return

        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
        if (!active) return

        const page = await pdf.getPage(1)
        if (!active) return

        const viewport = page.getViewport({ scale: 0.4 })
        if (!active) return

        const context = canvas.getContext('2d')
        if (!context) return

        canvas.width = viewport.width
        canvas.height = viewport.height

        await page.render({ canvasContext: context, viewport, canvas }).promise
        if (active) {
          const dataUrl = canvas.toDataURL()
          thumbnailCache.set(fileId, dataUrl)
          setCachedImage(dataUrl)
          setLoading(false)
        }
      } catch (err) {
        console.error('Failed to render PDF thumbnail', err)
        if (active) {
          setError(true)
          setLoading(false)
        }
      }
    }

    load()
    return () => { active = false }
  }, [file, fileId, cachedImage])

  return (
    <div className="relative w-full aspect-[3/4] bg-zinc-800/40 rounded-lg overflow-hidden flex items-center justify-center border border-zinc-800/80">
      {loading && (
        <div className="absolute inset-0 bg-zinc-800 animate-pulse flex items-center justify-center">
          <svg className="w-5 h-5 text-zinc-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      )}
      {error ? (
        <div className="text-[10px] text-zinc-500 text-center px-2">Thumbnail Unavailable</div>
      ) : cachedImage ? (
        <img src={cachedImage} alt="" className="max-w-full max-h-full object-contain" />
      ) : (
        <canvas ref={canvasRef} className="hidden" />
      )}
    </div>
  )
}
