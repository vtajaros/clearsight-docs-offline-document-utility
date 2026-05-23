import { useState } from 'react'
import type { ActiveTab } from '../types'

export function useNavigationGuard(onNavigate: (target: ActiveTab) => void) {
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false)
  const [pendingNavTarget, setPendingNavTarget] = useState<ActiveTab | null>(null)

  const handleNavClick = (target: ActiveTab, shouldGuard: boolean) => {
    if (hasUnsavedChanges || shouldGuard) {
      setPendingNavTarget(target)
    } else {
      onNavigate(target)
      setHasUnsavedChanges(false)
    }
  }

  const confirmNav = () => {
    if (pendingNavTarget) {
      onNavigate(pendingNavTarget)
      setPendingNavTarget(null)
      setHasUnsavedChanges(false)
    }
  }

  const cancelNav = () => {
    setPendingNavTarget(null)
  }

  const isModalOpen = pendingNavTarget !== null

  return {
    hasUnsavedChanges,
    setHasUnsavedChanges,
    isModalOpen,
    handleNavClick,
    confirmNav,
    cancelNav,
    pendingNavTarget
  }
}
