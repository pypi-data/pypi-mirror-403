/**
 * Keyboard Shortcuts Hook
 *
 * Global keyboard shortcuts for timeline navigation:
 * - Space: Toggle pause/play
 * - L: Jump to live
 * - J: Step backward
 * - K: Step forward
 * - Escape: Close inspector (handled in useSelection)
 */

import { useEffect } from "react"

interface KeyboardShortcutsConfig {
  /** Toggle pause/play */
  onTogglePause?: () => void
  /** Jump to live */
  onJumpToLive?: () => void
  /** Step backward one event */
  onStepBackward?: () => void
  /** Step forward one event */
  onStepForward?: () => void
  /** Whether shortcuts are enabled */
  enabled?: boolean
}

export function useKeyboardShortcuts({
  onTogglePause,
  onJumpToLive,
  onStepBackward,
  onStepForward,
  enabled = true,
}: KeyboardShortcutsConfig) {
  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }

      // Ignore if modifier keys are pressed (except shift)
      if (e.metaKey || e.ctrlKey || e.altKey) {
        return
      }

      switch (e.key.toLowerCase()) {
        case " ": // Space
          e.preventDefault()
          onTogglePause?.()
          break

        case "l":
          e.preventDefault()
          onJumpToLive?.()
          break

        case "j":
          e.preventDefault()
          onStepBackward?.()
          break

        case "k":
          e.preventDefault()
          onStepForward?.()
          break
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [enabled, onTogglePause, onJumpToLive, onStepBackward, onStepForward])
}
