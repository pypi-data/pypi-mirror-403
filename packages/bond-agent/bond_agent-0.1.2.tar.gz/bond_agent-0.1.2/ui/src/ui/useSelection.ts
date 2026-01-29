/**
 * Selection State Hook
 *
 * Manages block selection state with keyboard support.
 * - Tracks selected block ID
 * - Escape key to deselect
 * - Click outside to deselect
 */

import { useState, useCallback, useEffect, useRef } from "react"

export interface SelectionControls {
  /** Currently selected block ID */
  selectedBlockId: string | undefined
  /** Select a block */
  select: (blockId: string) => void
  /** Clear selection */
  deselect: () => void
  /** Toggle selection */
  toggle: (blockId: string) => void
  /** Ref to attach to container for click-outside detection */
  containerRef: React.RefObject<HTMLDivElement | null>
}

export function useSelection(): SelectionControls {
  const [selectedBlockId, setSelectedBlockId] = useState<string | undefined>(
    undefined
  )
  const containerRef = useRef<HTMLDivElement | null>(null)

  const select = useCallback((blockId: string) => {
    setSelectedBlockId(blockId)
  }, [])

  const deselect = useCallback(() => {
    setSelectedBlockId(undefined)
  }, [])

  const toggle = useCallback((blockId: string) => {
    setSelectedBlockId((prev) => (prev === blockId ? undefined : blockId))
  }, [])

  // Escape key to deselect
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && selectedBlockId) {
        deselect()
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [selectedBlockId, deselect])

  // Click outside to deselect
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (!selectedBlockId) return
      if (!containerRef.current) return

      // Check if click is inside the container
      if (!containerRef.current.contains(e.target as Node)) {
        deselect()
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [selectedBlockId, deselect])

  return {
    selectedBlockId,
    select,
    deselect,
    toggle,
    containerRef,
  }
}
