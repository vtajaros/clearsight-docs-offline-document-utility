
interface ProgressBarProps {
  loading: boolean
  progress: number        // 0-100
  label: string
}

export function ProgressBar({ loading, progress, label }: ProgressBarProps) {
  if (!loading) return null
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-xs text-zinc-400">{label}</span>
        <span className="text-xs font-medium text-violet-400">{progress}%</span>
      </div>
      <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: `${progress}%`,
            background: 'linear-gradient(90deg, #7c3aed, #a855f7, #c084fc)',
            boxShadow: '0 0 8px rgba(167, 85, 247, 0.6)',
            transition: 'width 0.1s linear',
          }}
        />
      </div>
    </div>
  )
}
