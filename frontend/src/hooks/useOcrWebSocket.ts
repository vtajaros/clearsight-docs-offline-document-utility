import { useState, useEffect, useRef } from 'react'
import type { OcrProgress } from '../types'

export function useOcrWebSocket(port: number | null, jobId: string | null) {
  const [progress, setProgress] = useState<OcrProgress | null>(null)
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
    setProgress(null)
  }

  useEffect(() => {
    if (!jobId || port === null) {
      disconnect()
      return
    }

    const ws = new WebSocket(`ws://127.0.0.1:${port}/ws/ocr/${jobId}`)
    wsRef.current = ws
    setIsConnected(true)
    setError(null)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.message === 'done') {
          ws.close()
          setProgress(null)
          setIsConnected(false)
        } else {
          setProgress(data)
        }
      } catch (err) {
        setError('Failed to parse socket message.')
      }
    }

    ws.onerror = () => {
      setError('WebSocket connection error.')
      setIsConnected(false)
      setProgress(null)
    }

    ws.onclose = () => {
      setIsConnected(false)
      setProgress(null)
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    }
  }, [port, jobId])

  return { progress, isConnected, error, disconnect }
}
