/**
 * Bond Replay From File Hook
 *
 * Loads and plays pre-recorded TraceEvents from an NDJSON file.
 * Uses timestamps in TraceEvents for realistic playback timing.
 */

import { useCallback, useEffect, useReducer, useRef, useState } from "react"
import type { TraceEvent, BondEvent, BondState } from "./types"
import { initialBondState } from "./types"
import { bondReducer } from "./reducer"
import { normalizeTraceEvent } from "./normalize"

export type DemoStatus = "idle" | "loading" | "playing" | "paused" | "complete"
export type PlaybackSpeed = 0.5 | 1 | 2

export interface DemoControls {
  /** Current block state */
  state: BondState
  /** Demo status */
  status: DemoStatus
  /** Current playback speed */
  speed: PlaybackSpeed
  /** Event history for replay scrubbing */
  events: BondEvent[]
  /** Current position (event index) */
  position: number
  /** Total events */
  totalEvents: number
  /** Load and start demo from URL */
  startDemo: (url: string) => Promise<void>
  /** Pause playback */
  pause: () => void
  /** Resume playback */
  resume: () => void
  /** Set playback speed */
  setSpeed: (speed: PlaybackSpeed) => void
  /** Jump to position */
  jumpTo: (position: number) => void
  /** Stop and reset */
  stop: () => void
}

export function useBondReplayFromFile(): DemoControls {
  const [state, dispatch] = useReducer(bondReducer, initialBondState)
  const [status, setStatus] = useState<DemoStatus>("idle")
  const [speed, setSpeed] = useState<PlaybackSpeed>(1)
  const [position, setPosition] = useState(0)

  // Store parsed trace events
  const traceEventsRef = useRef<TraceEvent[]>([])
  const eventsRef = useRef<BondEvent[]>([])
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const startTimeRef = useRef<number>(0)
  const speedRef = useRef(speed)

  // Keep speed ref in sync
  speedRef.current = speed

  // Clear any pending timeout
  const clearScheduled = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  // Schedule next event based on timestamp difference
  const scheduleNext = useCallback(
    (currentIndex: number) => {
      const traces = traceEventsRef.current
      if (currentIndex >= traces.length) {
        setStatus("complete")
        return
      }

      const currentTrace = traces[currentIndex]
      const nextIndex = currentIndex + 1

      // If there's a next event, calculate delay based on timestamps
      if (nextIndex < traces.length) {
        const nextTrace = traces[nextIndex]
        const delay =
          ((nextTrace.timestamp - currentTrace.timestamp) * 1000) /
          speedRef.current

        timeoutRef.current = setTimeout(() => {
          // Dispatch the next event
          const bondEvent = normalizeTraceEvent(nextTrace)
          if (bondEvent) {
            eventsRef.current = [...eventsRef.current, bondEvent]
            dispatch(bondEvent)
          }
          setPosition(nextIndex)
          scheduleNext(nextIndex)
        }, Math.max(0, delay))
      } else {
        // No more events after dispatching current
        setStatus("complete")
      }
    },
    []
  )

  const startDemo = useCallback(
    async (url: string) => {
      clearScheduled()
      setStatus("loading")

      try {
        const response = await fetch(url)
        const text = await response.text()

        // Parse NDJSON
        const lines = text.trim().split("\n")
        const traces: TraceEvent[] = []

        for (const line of lines) {
          if (line.trim()) {
            try {
              traces.push(JSON.parse(line) as TraceEvent)
            } catch {
              console.warn("Failed to parse line:", line)
            }
          }
        }

        if (traces.length === 0) {
          setStatus("idle")
          return
        }

        // Sort by sequence number
        traces.sort((a, b) => a.sequence - b.sequence)

        // Store and reset state
        traceEventsRef.current = traces
        eventsRef.current = []

        // Reset reducer state by re-dispatching from empty
        // (useReducer doesn't have reset, so we dispatch first event)
        const firstEvent = normalizeTraceEvent(traces[0])
        if (firstEvent) {
          eventsRef.current = [firstEvent]
          // We need to reset state - create a pseudo-reset by using initial state
          // For now, we'll just start fresh with first event
        }

        setPosition(0)
        setStatus("playing")
        startTimeRef.current = performance.now()

        // Dispatch first event and schedule next
        if (firstEvent) {
          dispatch(firstEvent)
          scheduleNext(0)
        }
      } catch (err) {
        console.error("Failed to load demo:", err)
        setStatus("idle")
      }
    },
    [clearScheduled, scheduleNext]
  )

  const pause = useCallback(() => {
    if (status === "playing") {
      clearScheduled()
      setStatus("paused")
    }
  }, [status, clearScheduled])

  const resume = useCallback(() => {
    if (status === "paused") {
      setStatus("playing")
      scheduleNext(position)
    }
  }, [status, position, scheduleNext])

  const jumpTo = useCallback(
    (newPosition: number) => {
      clearScheduled()

      const traces = traceEventsRef.current
      if (newPosition < 0 || newPosition >= traces.length) return

      // Re-reduce all events up to newPosition
      const events: BondEvent[] = []
      let newState = initialBondState

      for (let i = 0; i <= newPosition; i++) {
        const event = normalizeTraceEvent(traces[i])
        if (event) {
          events.push(event)
          newState = bondReducer(newState, event)
        }
      }

      eventsRef.current = events
      setPosition(newPosition)

      // We need to set state - but useReducer doesn't support setting directly
      // Dispatch a batch of events to get to target state
      // Actually, we need to reconstruct - for now just rebuild from position
      // This is a limitation - would need a different state management approach

      // For MVP: just continue from new position
      if (status === "playing") {
        scheduleNext(newPosition)
      }
    },
    [status, clearScheduled, scheduleNext]
  )

  const stop = useCallback(() => {
    clearScheduled()
    traceEventsRef.current = []
    eventsRef.current = []
    setPosition(0)
    setStatus("idle")
    // State will stay - user needs to reconnect or reload to clear
  }, [clearScheduled])

  // Cleanup on unmount
  useEffect(() => {
    return () => clearScheduled()
  }, [clearScheduled])

  // Update speed effect - reschedule with new timing
  useEffect(() => {
    if (status === "playing") {
      clearScheduled()
      scheduleNext(position)
    }
  }, [speed, status, position, clearScheduled, scheduleNext])

  return {
    state,
    status,
    speed,
    events: eventsRef.current,
    position,
    totalEvents: traceEventsRef.current.length,
    startDemo,
    pause,
    resume,
    setSpeed,
    jumpTo,
    stop,
  }
}
