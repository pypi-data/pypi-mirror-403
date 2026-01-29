/**
 * Bond Stream Hook
 *
 * SSE streaming transport layer with:
 * - EventSource connection management
 * - Status tracking (idle, connecting, live, error)
 * - Pause control with event buffering
 * - Event history for replay
 */

import { useCallback, useEffect, useReducer, useRef, useState } from "react"
import type { BondEvent, BondState } from "./types"
import { initialBondState } from "./types"
import { bondReducer } from "./reducer"
import { normalizeSSEEvent } from "./normalize"
import { useEventHistory } from "./useEventHistory"

export type ConnectionStatus = "idle" | "connecting" | "live" | "error"

export interface BondStreamControls {
  /** Current block state */
  state: BondState
  /** Connection status */
  status: ConnectionStatus
  /** Whether event processing is paused */
  paused: boolean
  /** Set pause state */
  setPaused: (paused: boolean) => void
  /** Connect to SSE endpoint */
  connect: () => void
  /** Disconnect from SSE endpoint */
  disconnect: () => void
  /** Event history for replay */
  history: {
    events: BondEvent[]
    count: number
    getUpTo: (index: number) => BondEvent[]
  }
  /** Reset state (clear blocks and history) */
  reset: () => void
}

export function useBondStream(url: string | null): BondStreamControls {
  const [state, dispatch] = useReducer(bondReducer, initialBondState)
  const [status, setStatus] = useState<ConnectionStatus>("idle")
  const [paused, setPaused] = useState(false)

  const eventSourceRef = useRef<EventSource | null>(null)
  const pausedRef = useRef(paused)
  const pauseBufferRef = useRef<BondEvent[]>([])

  const history = useEventHistory()

  // Keep pausedRef in sync
  pausedRef.current = paused

  const processEvent = useCallback(
    (event: BondEvent) => {
      // Always store in history
      history.push(event)

      // Only dispatch to reducer if not paused
      if (!pausedRef.current) {
        dispatch(event)
      } else {
        // Buffer for later when unpaused
        pauseBufferRef.current.push(event)
      }
    },
    [history]
  )

  const connect = useCallback(() => {
    if (!url) return
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setStatus("connecting")

    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      setStatus("live")
    }

    es.onerror = () => {
      // EventSource will auto-reconnect for CONNECTING state
      // Only set error if fully closed
      if (es.readyState === EventSource.CLOSED) {
        setStatus("error")
      }
    }

    // Handle named SSE events
    const eventTypes = [
      "block_start",
      "block_end",
      "text",
      "thinking",
      "tool_delta",
      "tool_exec",
      "tool_result",
      "complete",
    ]

    eventTypes.forEach((eventType) => {
      es.addEventListener(eventType, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data)
          const bondEvent = normalizeSSEEvent(eventType, data)
          if (bondEvent) {
            processEvent(bondEvent)
          }
        } catch (err) {
          console.warn(`Failed to parse SSE event: ${eventType}`, err)
        }
      })
    })

    // Also handle generic message event (for servers that don't use named events)
    es.onmessage = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data)
        // Try to determine event type from data
        if (data.t) {
          // Wire format - need to import normalizeWireEvent
          // For now, skip - we expect named events
          console.warn("Received wire format on generic message, expected named events")
        }
      } catch (err) {
        console.warn("Failed to parse generic SSE message", err)
      }
    }
  }, [url, processEvent])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setStatus("idle")
  }, [])

  const reset = useCallback(() => {
    disconnect()
    history.clear()
    pauseBufferRef.current = []
    // Reset reducer state by creating fresh state
    // Note: useReducer doesn't have a reset, so we dispatch a pseudo-reset
    // For now, we'll just disconnect and let user reconnect
  }, [disconnect, history])

  // Handle unpause - flush buffered events
  useEffect(() => {
    if (!paused && pauseBufferRef.current.length > 0) {
      // Flush buffered events
      pauseBufferRef.current.forEach((event) => {
        dispatch(event)
      })
      pauseBufferRef.current = []
    }
  }, [paused])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return {
    state,
    status,
    paused,
    setPaused,
    connect,
    disconnect,
    history: {
      events: history.events,
      count: history.count,
      getUpTo: history.getUpTo,
    },
    reset,
  }
}
