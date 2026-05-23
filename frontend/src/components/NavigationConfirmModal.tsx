// frontend/src/components/NavigationConfirmModal.tsx

type Props = {
  isOpen: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function NavigationConfirmModal({ isOpen, onConfirm, onCancel }: Props) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />
      
      {/* Modal Content */}
      <div className="relative bg-[#1e1e1e] border border-zinc-800 rounded-2xl p-6 shadow-2xl flex flex-col gap-4 w-full max-w-[400px] animate-in fade-in zoom-in-95 duration-200">
        
        {/* Close button */}
        <button
          onClick={onCancel}
          className="absolute top-4 right-4 p-1.5 text-zinc-500 hover:text-zinc-300 rounded-lg hover:bg-zinc-800 transition-all cursor-pointer"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-white">Unsaved Progress</h3>
        </div>
        
        <p className="text-sm text-zinc-400 leading-relaxed">
          You have a file loaded in the current workspace. Navigating away will discard your current progress. Are you sure you want to leave?
        </p>
        
        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 px-4 rounded-xl font-semibold text-sm text-zinc-300 bg-zinc-800/50 hover:bg-zinc-700/80 border border-zinc-700 transition-all cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 px-4 rounded-xl font-semibold text-sm text-white bg-violet-600 hover:bg-violet-700 shadow-md shadow-violet-900/20 transition-all cursor-pointer"
          >
            Leave Page
          </button>
        </div>
      </div>
    </div>
  )
}
