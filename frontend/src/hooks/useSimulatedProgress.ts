import { useState, useRef } from 'react'

interface Phase {
  target: number
  label: string
  delayMs: number
}

export function useSimulatedProgress() {
  const [progress, setProgress] = useState(0)
  const [label, setLabel] = useState('')
  const progressRef = useRef(0)
  const animFrameRef = useRef<number | null>(null)
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  const animateTo = (target: number) => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    const step = () => {
      progressRef.current = Math.min(
        progressRef.current + (target - progressRef.current) * 0.08,
        target
      )
      setProgress(Math.round(progressRef.current))
      if (Math.abs(progressRef.current - target) > 0.5) {
        animFrameRef.current = requestAnimationFrame(step)
      } else {
        progressRef.current = target
        setProgress(target)
      }
    }
    animFrameRef.current = requestAnimationFrame(step)
  }

  const start = (phases: Phase[]) => {
    progressRef.current = 0
    setProgress(0)
    setLabel(phases[0]?.label ?? 'Processing...')
    animateTo(5)
    timersRef.current = phases.map(({ target, label: l, delayMs }) =>
      setTimeout(() => { setLabel(l); animateTo(target) }, delayMs)
    )
  }

  const finish = () => {
    timersRef.current.forEach(clearTimeout)
    setLabel('Done!')
    animateTo(100)
  }

  const cancel = () => {
    timersRef.current.forEach(clearTimeout)
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    setProgress(0)
    setLabel('')
  }

  return { progress, label, start, finish, cancel }
}
