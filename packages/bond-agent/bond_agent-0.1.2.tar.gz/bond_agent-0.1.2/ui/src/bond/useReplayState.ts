/**
 * Replay State Hook
 *
 * Manages replay position and derives visible state from event history.
 * Supports scrubbing through past events while new events continue buffering.
 */

import { useMemo, useState, useCallback, useRef, useEffect } from "react"
import type { BondEvent, BondState } from "./types"
import { initialBondState } from "./types"
import { reduceEvents } from "./reducer"

export type ReplayMode = "live" | "replay"

export interface ReplayStateControls {
  /** Current replay mode */
  mode: ReplayMode
  /** Current position in event history (0-based index) */
  position: number
  /** Total events in history */
  totalEvents: number
  /** Derived block state at current position */
  visibleState: BondState
  /** Set replay position (switches to replay mode) */
  setPosition: (position: number) => void
  /** Jump back to live position */
  jumpToLive: () => void
  /** Whether we're at the latest position */
  isAtLive: boolean
}

// Debounce delay for scrubber input (ms)
const SCRUB_DEBOUNCE_MS = 50

// Cache intermediate states every N events for faster scrubbing
const CACHE_INTERVAL = 100

export function useReplayState(events: BondEvent[]): ReplayStateControls {
  const [mode, setMode] = useState<ReplayMode>("live")
  const [position, setPositionRaw] = useState(0)
  const [debouncedPosition, setDebouncedPosition] = useState(0)

  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Cache for intermediate states (position -> state)
  const stateCache = useRef<Map<number, BondState>>(new Map())

  const totalEvents = events.length

  // Keep position in bounds
  const clampedPosition = Math.min(Math.max(0, position), totalEvents - 1)

  // Debounce position updates for scrubber
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    debounceTimeoutRef.current = setTimeout(() => {
      setDebouncedPosition(clampedPosition)
    }, SCRUB_DEBOUNCE_MS)

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [clampedPosition])

  // Update position to follow live when in live mode
  useEffect(() => {
    if (mode === "live" && totalEvents > 0) {
      setPositionRaw(totalEvents - 1)
      setDebouncedPosition(totalEvents - 1)
    }
  }, [mode, totalEvents])

  // Build state cache at intervals
  useEffect(() => {
    if (events.length === 0) {
      stateCache.current.clear()
      return
    }

    // Build cache entries at intervals
    const newCache = new Map<number, BondState>()
    let state = initialBondState

    for (let i = 0; i < events.length; i++) {
      state = reduceEvents([events[i]], state)

      // Cache at intervals
      if ((i + 1) % CACHE_INTERVAL === 0) {
        newCache.set(i, { ...state })
      }
    }

    // Always cache the final state
    newCache.set(events.length - 1, state)
    stateCache.current = newCache
  }, [events])

  // Compute visible state at debounced position
  const visibleState = useMemo(() => {
    if (events.length === 0) {
      return initialBondState
    }

    const targetPosition = Math.min(debouncedPosition, events.length - 1)

    // Find nearest cached state before target
    let startPosition = -1
    let startState = initialBondState

    for (const [cachedPos, cachedState] of stateCache.current) {
      if (cachedPos <= targetPosition && cachedPos > startPosition) {
        startPosition = cachedPos
        startState = cachedState
      }
    }

    // If exact cache hit, return it
    if (startPosition === targetPosition) {
      return startState
    }

    // Reduce from cached state to target
    const eventsToProcess = events.slice(startPosition + 1, targetPosition + 1)
    return reduceEvents(eventsToProcess, startState)
  }, [events, debouncedPosition])

  const setPosition = useCallback(
    (newPosition: number) => {
      const clamped = Math.min(Math.max(0, newPosition), totalEvents - 1)
      setPositionRaw(clamped)

      // Switch to replay mode if not at live
      if (clamped < totalEvents - 1) {
        setMode("replay")
      }
    },
    [totalEvents]
  )

  const jumpToLive = useCallback(() => {
    setMode("live")
    if (totalEvents > 0) {
      setPositionRaw(totalEvents - 1)
      setDebouncedPosition(totalEvents - 1)
    }
  }, [totalEvents])

  const isAtLive = mode === "live" || clampedPosition >= totalEvents - 1

  return {
    mode,
    position: clampedPosition,
    totalEvents,
    visibleState,
    setPosition,
    jumpToLive,
    isAtLive,
  }
}
