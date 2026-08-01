import { useState, useRef, useCallback } from 'react'
import type { BookmarkNode } from '../types'

interface FlatBookmarkNode {
  id: string
  title: string
  page: number
  level: number
  parentId: string | null
}

export function useBookmarkEditor(initialBookmarks: BookmarkNode[]) {
  const flattenTree = useCallback((nodes: BookmarkNode[], parentId: string | null = null): FlatBookmarkNode[] => {
    let result: FlatBookmarkNode[] = []
    for (const node of nodes) {
      const id = crypto.randomUUID()
      result.push({
        id,
        title: node.title,
        page: node.page,
        level: node.level,
        parentId
      })
      if (node.children && node.children.length > 0) {
        result = result.concat(flattenTree(node.children, id))
      }
    }
    return result
  }, [])

  const initialFlatTree = flattenTree(initialBookmarks)
  const initialFlat = useRef<FlatBookmarkNode[]>(initialFlatTree)
  const [flatNodes, setFlatNodes] = useState<FlatBookmarkNode[]>(initialFlatTree)

  const isDirty = JSON.stringify(flatNodes) !== JSON.stringify(initialFlat.current)

  const renameNode = useCallback((id: string, newTitle: string) => {
    const trimmed = newTitle.trim()
    if (!trimmed) return
    setFlatNodes(prev => prev.map(node => node.id === id ? { ...node, title: trimmed } : node))
  }, [])

  const renamePage = useCallback((id: string, newPage: number) => {
    setFlatNodes(prev => prev.map(node => node.id === id ? { ...node, page: newPage } : node))
  }, [])

  const deleteNode = useCallback((id: string) => {
    setFlatNodes(prev => {
      const descendants = new Set<string>()
      const findDescendants = (parentId: string) => {
        for (const node of prev) {
          if (node.parentId === parentId && !descendants.has(node.id)) {
            descendants.add(node.id)
            findDescendants(node.id)
          }
        }
      }
      findDescendants(id)
      descendants.add(id)

      const remaining = prev.filter(node => !descendants.has(node.id))
      if (remaining.length === 0) return prev
      return remaining
    })
  }, [])

  const addChild = useCallback((parentId: string) => {
    setFlatNodes(prev => {
      const parentIdx = prev.findIndex(n => n.id === parentId)
      if (parentIdx === -1) return prev
      const parent = prev[parentIdx]

      const descendants = new Set<string>()
      const findDescendants = (pId: string) => {
        for (const node of prev) {
          if (node.parentId === pId && !descendants.has(node.id)) {
            descendants.add(node.id)
            findDescendants(node.id)
          }
        }
      }
      findDescendants(parentId)
      
      let insertIdx = parentIdx
      for (let i = prev.length - 1; i > parentIdx; i--) {
        if (descendants.has(prev[i].id)) {
          insertIdx = i
          break
        }
      }

      const newNode: FlatBookmarkNode = {
        id: crypto.randomUUID(),
        title: "New Bookmark",
        page: parent.page,
        level: Math.min(parent.level + 1, 3),
        parentId
      }

      const newNodes = [...prev]
      newNodes.splice(insertIdx + 1, 0, newNode)
      return newNodes
    })
  }, [])

  const addRootNode = useCallback(() => {
    setFlatNodes(prev => {
      const newNode: FlatBookmarkNode = {
        id: crypto.randomUUID(),
        title: "New Bookmark",
        page: 1,
        level: 1,
        parentId: null
      }
      return [...prev, newNode]
    })
  }, [])

  const changeLevel = useCallback((id: string, delta: number) => {
    setFlatNodes(prev => {
      const targetIdx = prev.findIndex(n => n.id === id)
      if (targetIdx === -1) return prev
      const target = prev[targetIdx]

      const newLevel = Math.max(1, Math.min(3, target.level + delta))
      if (newLevel === target.level) return prev

      const descendants = new Set<string>()
      const findDescendants = (pId: string) => {
        for (const node of prev) {
          if (node.parentId === pId && !descendants.has(node.id)) {
            descendants.add(node.id)
            findDescendants(node.id)
          }
        }
      }
      findDescendants(id)

      const newNodes = [...prev]
      
      newNodes[targetIdx] = { ...target, level: newLevel }

      for (let i = 0; i < newNodes.length; i++) {
        if (descendants.has(newNodes[i].id)) {
          newNodes[i] = { ...newNodes[i], level: Math.max(1, Math.min(3, newNodes[i].level + delta)) }
        }
      }

      if (delta < 0) { // promoted (-1)
        let newParentId: string | null = null
        if (newLevel > 1) {
          let currAncestorId = target.parentId
          while (currAncestorId) {
            const ancestor = newNodes.find(n => n.id === currAncestorId)
            if (ancestor && ancestor.level === newLevel - 1) {
              newParentId = ancestor.id
              break
            }
            if (ancestor) {
               currAncestorId = ancestor.parentId
            } else {
               break
            }
          }
        }
        newNodes[targetIdx].parentId = newParentId
      } else if (delta > 0) { // demoted (+1)
        let MathTarget = newLevel - 1
        let newParentId: string | null = null
        for (let i = targetIdx - 1; i >= 0; i--) {
          if (newNodes[i].level === MathTarget) {
            newParentId = newNodes[i].id
            break
          }
        }
        newNodes[targetIdx].parentId = newParentId
      }

      return newNodes
    })
  }, [])

  const reorderNodes = useCallback((activeId: string, overId: string) => {
    setFlatNodes(prev => {
      const activeIdx = prev.findIndex(n => n.id === activeId)
      const overIdx = prev.findIndex(n => n.id === overId)
      if (activeIdx === -1 || overIdx === -1 || activeIdx === overIdx) return prev

      const descendants = new Set<string>()
      const findDescendants = (pId: string) => {
        for (const node of prev) {
          if (node.parentId === pId && !descendants.has(node.id)) {
            descendants.add(node.id)
            findDescendants(node.id)
          }
        }
      }
      findDescendants(activeId)
      descendants.add(activeId)

      const activeGroup = prev.filter(n => descendants.has(n.id))
      const remaining = prev.filter(n => !descendants.has(n.id))

      const newOverIdx = remaining.findIndex(n => n.id === overId)
      const insertIdx = activeIdx < overIdx ? newOverIdx + 1 : newOverIdx
      
      const result = [...remaining]
      result.splice(insertIdx, 0, ...activeGroup)
      return result
    })
  }, [])

  const reset = useCallback(() => {
    setFlatNodes(JSON.parse(JSON.stringify(initialFlat.current)))
  }, [])

  const toBookmarkTree = useCallback((): BookmarkNode[] => {
    const root: BookmarkNode[] = []
    const map = new Map<string, BookmarkNode>()

    for (const fn of flatNodes) {
      map.set(fn.id, {
        title: fn.title,
        page: fn.page,
        level: fn.level,
        children: []
      })
    }

    for (const fn of flatNodes) {
      const bn = map.get(fn.id)!
      if (fn.parentId === null) {
        root.push(bn)
      } else {
        const parentBn = map.get(fn.parentId)
        if (parentBn) {
          parentBn.children.push(bn)
        } else {
          root.push(bn)
        }
      }
    }

    return root
  }, [flatNodes])

  return {
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
  }
}
