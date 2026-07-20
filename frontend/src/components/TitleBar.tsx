import { useState, useEffect } from 'react'
import { Minus, Square, Copy, X } from 'lucide-react'

export function TitleBar() {
  const [isMaximized, setIsMaximized] = useState(true)

  useEffect(() => {
    window.electronAPI?.titlebar.isMaximized().then(setIsMaximized)
    const cleanup = window.electronAPI?.titlebar.onMaximizedChange(setIsMaximized)
    return () => {
      cleanup?.()
    }
  }, [])

  const handleDoubleClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.titlebar-controls')) return
    window.electronAPI?.titlebar.maximize()
  }

  return (
    <div
      className="titlebar"
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
      onDoubleClick={handleDoubleClick}
    >
      <div className="titlebar-spacer" />

      <div className="titlebar-center">
        <img
          src="./icon-64.png"
          alt=""
          width={18}
          height={18}
          style={{ width: 18, height: 18, objectFit: 'contain', imageRendering: 'auto' }}
        />
        <span className="titlebar-title">ClearSight Docs</span>
      </div>

      <div className="titlebar-controls" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
        <button onClick={() => window.electronAPI?.titlebar.minimize()} title="Minimize">
          <Minus size={14} strokeWidth={1.5} />
        </button>
        <button
          onClick={() => window.electronAPI?.titlebar.maximize()}
          title={isMaximized ? 'Restore' : 'Maximize'}
        >
          {isMaximized ? <Copy size={13} strokeWidth={1.5} /> : <Square size={13} strokeWidth={1.5} />}
        </button>
        <button className="close-btn" onClick={() => window.electronAPI?.titlebar.close()} title="Close">
          <X size={14} strokeWidth={1.5} />
        </button>
      </div>
    </div>
  )
}
