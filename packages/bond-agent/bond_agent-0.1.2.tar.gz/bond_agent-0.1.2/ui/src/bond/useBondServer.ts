/**
 * Bond Server Hook
 *
 * Handles the 2-step bond.server flow:
 * 1. POST /ask with prompt -> get session_id and stream_url
 * 2. Connect EventSource to stream_url
 * 3. For follow-ups, POST /ask with same session_id
 */

import { useCallback, useEffect, useReducer, useRef, useState } from "react"
import type { BondEvent, BondState } from "./types"
import { initialBondState } from "./types"
import { bondReducer } from "./reducer"
import { normalizeSSEEvent } from "./normalize"
import { useEventHistory } from "./useEventHistory"

export type ServerStatus = "idle" | "connecting" | "live" | "streaming" | "error"

export interface BondServerControls {
  /** Current block state */
  state: BondState
  /** Server connection status */
  status: ServerStatus
  /** Current session ID */
  sessionId: string | null
  /** Error message if status is error */
  error: string | null
  /** Whether event processing is paused */
  paused: boolean
  /** Set pause state */
  setPaused: (paused: boolean) => void
  /** Send a message to the server */
  sendMessage: (prompt: string) => Promise<void>
  /** Disconnect from server */
  disconnect: () => void
  /** Event history for replay */
  history: {
    events: BondEvent[]
    count: number
    getUpTo: (index: number) => BondEvent[]
  }
  /** Reset state */
  reset: () => void
}

interface AskResponse {
  session_id: string
  stream_url: string
}

export function useBondServer(serverUrl: string | null): BondServerControls {
  const [state, dispatch] = useReducer(bondReducer, initialBondState)
  const [status, setStatus] = useState<ServerStatus>("idle")
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [paused, setPaused] = useState(false)
  // Track if current stream has yielded events
  const streamHasEventsRef = useRef(false)
  
  // Track global block index to prevent collisions between streams
  const nextBlockIndexRef = useRef(0)
  const streamIndexMapRef = useRef<Record<number, number>>({})

  const eventSourceRef = useRef<EventSource | null>(null)
  const pausedRef = useRef(paused)
  const pauseBufferRef = useRef<BondEvent[]>([])

  const history = useEventHistory()

  // Keep pausedRef in sync
  pausedRef.current = paused

  const processEvent = useCallback(
    (event: BondEvent) => {
      streamHasEventsRef.current = true
      
      // Re-index blocks to ensure unique IDs across session
      const processedEvent = { ...event }
      
      if (processedEvent.type === "block_start") {
        const newIndex = nextBlockIndexRef.current++
        streamIndexMapRef.current[processedEvent.index] = newIndex
        processedEvent.index = newIndex
      } else if (processedEvent.type === "block_end") {
        const mapped = streamIndexMapRef.current[processedEvent.index]
        if (mapped !== undefined) {
          processedEvent.index = mapped
        }
      }

      history.push(processedEvent)
      if (!pausedRef.current) {
        dispatch(processedEvent)
      } else {
        pauseBufferRef.current.push(processedEvent)
      }
    },
    [history]
  )

  const connectToStream = useCallback(
    (streamUrl: string) => {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }

      streamHasEventsRef.current = false
      streamIndexMapRef.current = {}
      const fullUrl = serverUrl ? `${serverUrl}${streamUrl}` : streamUrl
      const es = new EventSource(fullUrl)
      eventSourceRef.current = es

      es.onopen = () => {
        setStatus("streaming")
      }

      es.onerror = () => {
        if (es.readyState === EventSource.CLOSED) {
          setStatus("live") // Stream ended, but still connected to server
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
            console.log(`BondServer: Received ${eventType}`, e.data)
            const data = JSON.parse(e.data)

            // On complete, handle non-streaming fallback BEFORE processing
            if (eventType === "complete") {
              const d = data as { data: string }
              // If we only got a complete event (no streaming), treat it as a text response
              if (!streamHasEventsRef.current && d.data) {
                const text = typeof d.data === "string" ? d.data : JSON.stringify(d.data)
                processEvent({ type: "block_start", kind: "text", index: 0 })
                processEvent({ type: "text_delta", delta: text })
                processEvent({ type: "block_end", kind: "text", index: 0 })
              }
              es.close()
              setStatus("live")
              return
            }

            const bondEvent = normalizeSSEEvent(eventType, data)
            if (bondEvent) {
              processEvent(bondEvent)
            }
          } catch (err) {
            console.warn(`Failed to parse SSE event: ${eventType}`, err)
          }
        })
      })

      // Handle error events
      es.addEventListener("error", (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data)
          setError(data.error || "Unknown error")
          setStatus("error")
          es.close()
        } catch {
          // Ignore parse errors on error events
        }
      })
    },
    [serverUrl, processEvent]
  )

  const sendMessage = useCallback(
    async (prompt: string) => {
      if (!serverUrl) {
        setError("No server URL configured")
        setStatus("error")
        return
      }

      setStatus("connecting")
      setError(null)

      try {
        const response = await fetch(`${serverUrl}/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt,
            session_id: sessionId,
          }),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.error || `Server error: ${response.status}`)
        }

        const data: AskResponse = await response.json()
        console.log("BondServer: Session created", data)
        setSessionId(data.session_id)
        connectToStream(data.stream_url)
      } catch (err) {
        console.error("BondServer: Connection failed", err)
        setError(err instanceof Error ? err.message : "Failed to connect")
        setStatus("error")
      }
    },
    [serverUrl, sessionId, connectToStream]
  )

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setStatus("idle")
    setSessionId(null)
    setError(null)
  }, [])

  const reset = useCallback(() => {
    disconnect()
    history.clear()
    pauseBufferRef.current = []
  }, [disconnect, history])

  // Handle unpause - flush buffered events
  useEffect(() => {
    if (!paused && pauseBufferRef.current.length > 0) {
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
    sessionId,
    error,
    paused,
    setPaused,
    sendMessage,
    disconnect,
    history: {
      events: history.events,
      count: history.count,
      getUpTo: history.getUpTo,
    },
    reset,
  }
}
