import { useState } from 'react'
import type { BookmarkNode } from '../types'

interface BookmarkTreeNodeProps {
  node: BookmarkNode
  onJumpToPage: (page: number) => void
  depth: number
}

export function BookmarkTreeNode({ node, onJumpToPage, depth }: BookmarkTreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(depth > 0 ? false : true)
  const hasChildren = node.children && node.children.length > 0

  const getTextStyle = (d: number) => {
    if (d === 0) return 'text-sm font-semibold text-zinc-200'
    if (d === 1) return 'text-sm font-medium text-zinc-300'
    return 'text-xs font-normal text-zinc-400'
  }

  return (
    <div className="flex flex-col w-full">
      <div
        className="flex items-center group hover:bg-zinc-800/50 rounded pr-2 py-1.5 cursor-pointer transition-colors"
        onClick={() => onJumpToPage(node.page)}
        style={{ paddingLeft: `${(depth * 16) + 8}px` }}
      >
        <div className="w-5 h-5 flex items-center justify-center shrink-0 mr-1.5">
          {hasChildren && (
            <div
              className="p-0.5 rounded hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer"
              onClick={(e) => {
                e.stopPropagation()
                setIsExpanded(!isExpanded)
              }}
            >
              <svg 
                className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} 
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          )}
        </div>

        <div className={`flex-1 truncate ${getTextStyle(depth)}`}>
          {node.title}
        </div>

        <div className="shrink-0 ml-3 bg-zinc-800 text-zinc-500 text-xs rounded px-1.5 py-0.5">
          {node.page}
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div className="flex flex-col w-full">
          {node.children.map((child, i) => (
            <BookmarkTreeNode
              key={`${child.page}-${child.title}-${i}`}
              node={child}
              onJumpToPage={onJumpToPage}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
