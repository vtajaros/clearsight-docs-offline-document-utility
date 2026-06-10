import {
  DndContext,
  closestCenter,
  type DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useBookmarkEditor } from '../hooks/useBookmarkEditor'
import type { BookmarkNode } from '../../types'

interface FlatBookmarkNode {
  id: string
  title: string
  page: number
  level: number
  parentId: string | null
}

interface SortableBookmarkRowProps {
  node: FlatBookmarkNode
  pageCount: number
  isOnlyRoot: boolean
  onRename: (id: string, newTitle: string) => void
  onRenamePage: (id: string, newPage: number) => void
  onDelete: (id: string) => void
  onAddChild: (id: string) => void
  onChangeLevel: (id: string, delta: number) => void
}

function SortableBookmarkRow({
  node,
  pageCount,
  isOnlyRoot,
  onRename,
  onRenamePage,
  onDelete,
  onAddChild,
  onChangeLevel
}: SortableBookmarkRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition
  } = useSortable({ id: node.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition
  }

  const handlePageBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    let val = parseInt(e.target.value, 10)
    if (isNaN(val)) val = node.page
    if (val < 1) val = 1
    if (val > pageCount) val = pageCount
    e.target.value = String(val)
    if (val !== node.page) {
      onRenamePage(node.id, val)
    }
  }

  return (
    <div style={style} className="flex items-center gap-2 py-1.5 px-2 bg-zinc-900/50 hover:bg-zinc-800/80 border-b border-zinc-800/50 transition-colors group">
      <div
        ref={setNodeRef}
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing p-1 text-zinc-500 hover:text-zinc-300"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8 6a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM8 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM8 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM20 6a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM20 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM20 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0z"/>
        </svg>
      </div>

      <div style={{ paddingLeft: `${(node.level - 1) * 16}px` }} className="flex-1 flex items-center gap-2">
        <input
          type="text"
          defaultValue={node.title}
          onBlur={(e) => onRename(node.id, e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          className="flex-1 bg-zinc-950/50 border border-zinc-700/50 rounded px-2 py-1 text-sm text-zinc-200 focus:outline-none focus:border-violet-500 transition-colors"
        />
      </div>

      <div className="flex items-center gap-1 shrink-0">
        <span className="text-xs text-zinc-500">Page</span>
        <input
          type="number"
          min={1}
          max={pageCount}
          defaultValue={node.page}
          onBlur={handlePageBlur}
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          className="w-16 bg-zinc-950/50 border border-zinc-700/50 rounded px-2 py-1 text-sm text-zinc-200 focus:outline-none focus:border-violet-500 transition-colors"
        />
      </div>

      <div className="flex items-center gap-1 shrink-0 ml-2">
        <button
          disabled={node.level === 1}
          onClick={() => onChangeLevel(node.id, -1)}
          className="w-6 h-6 flex items-center justify-center rounded bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          &larr;
        </button>
        <button
          disabled={node.level === 3}
          onClick={() => onChangeLevel(node.id, 1)}
          className="w-6 h-6 flex items-center justify-center rounded bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          &rarr;
        </button>
      </div>

      <div className="flex items-center gap-1 shrink-0 ml-2">
        <button
          onClick={() => onAddChild(node.id)}
          title="Add Child Bookmark"
          className="w-7 h-7 flex items-center justify-center rounded text-zinc-400 hover:text-emerald-400 hover:bg-emerald-400/10 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
        </button>
        <button
          disabled={isOnlyRoot}
          onClick={() => onDelete(node.id)}
          title={isOnlyRoot ? "Cannot delete the only bookmark" : "Delete Bookmark"}
          className="w-7 h-7 flex items-center justify-center rounded text-zinc-400 hover:text-red-400 hover:bg-red-400/10 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-zinc-400 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
        </button>
      </div>
    </div>
  )
}

interface BookmarkEditorProps {
  pageCount: number
  initialBookmarks: BookmarkNode[]
  onSave: (bookmarks: BookmarkNode[]) => void
  onCancel: () => void
  forceEnableSave?: boolean
}

export function BookmarkEditor({ pageCount, initialBookmarks, onSave, onCancel, forceEnableSave = false }: BookmarkEditorProps) {
  const {
    flatNodes,
    isDirty,
    renameNode,
    renamePage,
    deleteNode,
    addChild,
    addRootNode,
    changeLevel,
    reorderNodes,
    reset,
    toBookmarkTree
  } = useBookmarkEditor(initialBookmarks)

  const sensors = useSensors(useSensor(PointerSensor, {
    activationConstraint: { distance: 8 }
  }))

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (over && active.id !== over.id) {
      reorderNodes(String(active.id), String(over.id))
    }
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-zinc-950/50 rounded-xl border border-zinc-800/50 overflow-hidden">
      {/* Toolbar */}
      <div className="px-4 py-3 border-b border-zinc-800/50 bg-zinc-900/50 flex justify-between items-center shrink-0">
        <button
          onClick={addRootNode}
          className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm font-medium rounded-lg transition-colors shadow-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
          Add Bookmark
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-1.5 border border-zinc-700 hover:bg-zinc-800 text-zinc-300 text-sm font-medium rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            disabled={!isDirty && !forceEnableSave}
            onClick={reset}
            className="px-4 py-1.5 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium rounded-lg transition-colors"
          >
            Reset
          </button>
          <button
            disabled={!isDirty && !forceEnableSave}
            onClick={() => onSave(toBookmarkTree())}
            className="px-4 py-1.5 bg-violet-500 hover:bg-violet-600 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors shadow-md"
          >
            Save
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-2 custom-scrollbar">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={flatNodes.map(n => n.id)} strategy={verticalListSortingStrategy}>
            {flatNodes.map(node => (
              <SortableBookmarkRow
                key={node.id}
                node={node as any}
                pageCount={pageCount}
                isOnlyRoot={flatNodes.filter(n => n.level === 1).length === 1 && node.level === 1}
                onRename={renameNode}
                onRenamePage={renamePage}
                onDelete={deleteNode}
                onAddChild={addChild}
                onChangeLevel={changeLevel}
              />
            ))}
          </SortableContext>
        </DndContext>
      </div>
    </div>
  )
}
