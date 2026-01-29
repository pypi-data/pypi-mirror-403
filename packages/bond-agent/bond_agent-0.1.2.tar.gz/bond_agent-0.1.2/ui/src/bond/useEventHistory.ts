/**
 * Event History Buffer
 *
 * Stores events for replay functionality.
 * Supports buffering while paused and limiting history size.
 */

import { useCallback, useRef, useState } from "react"
import type { BondEvent } from "./types"

const DEFAULT_MAX_EVENTS = 10000

export interface EventHistoryControls {
  /** All stored events */
  events: BondEvent[]
  /** Add an event to history */
  push: (event: BondEvent) => void
  /** Clear all history */
  clear: () => void
  /** Get events up to index (for replay) */
  getUpTo: (index: number) => BondEvent[]
  /** Total event count */
  count: number
}

export function useEventHistory(
  maxEvents: number = DEFAULT_MAX_EVENTS
): EventHistoryControls {
  const [events, setEvents] = useState<BondEvent[]>([])
  const eventsRef = useRef<BondEvent[]>([])

  // Keep ref in sync for use in callbacks
  eventsRef.current = events

  const push = useCallback(
    (event: BondEvent) => {
      setEvents((prev) => {
        const next = [...prev, event]
        // Limit history size
        if (next.length > maxEvents) {
          return next.slice(-maxEvents)
        }
        return next
      })
    },
    [maxEvents]
  )

  const clear = useCallback(() => {
    setEvents([])
  }, [])

  const getUpTo = useCallback((index: number) => {
    return eventsRef.current.slice(0, index + 1)
  }, [])

  return {
    events,
    push,
    clear,
    getUpTo,
    count: events.length,
  }
}
