# Bond Server UI Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add full bond.server integration to the UI with a connect dialog, message input, and multi-turn conversation support.

**Architecture:** Replace the simple `prompt()` connect flow with a modal dialog. Create a new `useBondServer` hook that handles the 2-step flow (POST /ask → SSE stream). Add a chat input component for multi-turn conversations. Reuse existing `useBondStream` internals for SSE handling.

**Tech Stack:** React, TypeScript, Tailwind CSS, shadcn/ui components

---

## Task 1: Create Input Component

**Files:**
- Create: `ui/src/components/ui/input.tsx`

**Step 1: Create the input component**

```tsx
import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-50 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-600 focus:ring-offset-2 focus:ring-offset-zinc-950 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
```

**Step 2: Verify it builds**

Run: `cd ui && pnpm build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add ui/src/components/ui/input.tsx
git commit -m "feat(ui): add input component"
```

---

## Task 2: Create Dialog Component

**Files:**
- Create: `ui/src/components/ui/dialog.tsx`

**Step 1: Create the dialog component**

```tsx
import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/80"
        onClick={() => onOpenChange(false)}
      />
      {/* Content */}
      <div className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2">
        {children}
      </div>
    </div>
  )
}

interface DialogContentProps {
  children: React.ReactNode
  className?: string
  onClose?: () => void
}

export function DialogContent({ children, className, onClose }: DialogContentProps) {
  return (
    <div
      className={cn(
        "w-full max-w-lg rounded-lg border border-zinc-800 bg-zinc-950 p-6 shadow-lg",
        className
      )}
    >
      {onClose && (
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
        >
          <X className="h-4 w-4" />
        </button>
      )}
      {children}
    </div>
  )
}

export function DialogHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)}>
      {children}
    </div>
  )
}

export function DialogTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h2 className={cn("text-lg font-semibold leading-none tracking-tight", className)}>
      {children}
    </h2>
  )
}

export function DialogDescription({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={cn("text-sm text-zinc-400", className)}>
      {children}
    </p>
  )
}

export function DialogFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)}>
      {children}
    </div>
  )
}
```

**Step 2: Verify it builds**

Run: `cd ui && pnpm build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add ui/src/components/ui/dialog.tsx
git commit -m "feat(ui): add dialog component"
```

---

## Task 3: Create useBondServer Hook

**Files:**
- Create: `ui/src/bond/useBondServer.ts`

**Step 1: Create the hook**

```tsx
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

  const eventSourceRef = useRef<EventSource | null>(null)
  const pausedRef = useRef(paused)
  const pauseBufferRef = useRef<BondEvent[]>([])

  const history = useEventHistory()

  // Keep pausedRef in sync
  pausedRef.current = paused

  const processEvent = useCallback(
    (event: BondEvent) => {
      history.push(event)
      if (!pausedRef.current) {
        dispatch(event)
      } else {
        pauseBufferRef.current.push(event)
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
            const data = JSON.parse(e.data)
            const bondEvent = normalizeSSEEvent(eventType, data)
            if (bondEvent) {
              processEvent(bondEvent)
            }
            // On complete, close the stream
            if (eventType === "complete") {
              es.close()
              setStatus("live")
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
        setSessionId(data.session_id)
        connectToStream(data.stream_url)
      } catch (err) {
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
```

**Step 2: Verify it builds**

Run: `cd ui && pnpm build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add ui/src/bond/useBondServer.ts
git commit -m "feat(ui): add useBondServer hook for bond.server integration"
```

---

## Task 4: Create ConnectDialog Component

**Files:**
- Create: `ui/src/ui/ConnectDialog.tsx`

**Step 1: Create the connect dialog**

```tsx
/**
 * Connect Dialog
 *
 * Modal for connecting to a bond.server instance.
 * Collects server URL and initial prompt.
 */

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"

interface ConnectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConnect: (serverUrl: string, prompt: string) => void
  isConnecting?: boolean
}

export function ConnectDialog({
  open,
  onOpenChange,
  onConnect,
  isConnecting = false,
}: ConnectDialogProps) {
  const [serverUrl, setServerUrl] = useState("http://localhost:8000")
  const [prompt, setPrompt] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (serverUrl && prompt) {
      onConnect(serverUrl, prompt)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Connect to Bond Server</DialogTitle>
            <DialogDescription>
              Enter your server URL and initial message to start a session.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 space-y-4">
            <div className="space-y-2">
              <label htmlFor="server-url" className="text-sm font-medium">
                Server URL
              </label>
              <Input
                id="server-url"
                placeholder="http://localhost:8000"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                disabled={isConnecting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="prompt" className="text-sm font-medium">
                Message
              </label>
              <Input
                id="prompt"
                placeholder="Hello! What can you help me with?"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isConnecting}
                autoFocus
              />
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={isConnecting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!serverUrl || !prompt || isConnecting}
            >
              {isConnecting ? "Connecting..." : "Connect"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

**Step 2: Verify it builds**

Run: `cd ui && pnpm build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add ui/src/ui/ConnectDialog.tsx
git commit -m "feat(ui): add ConnectDialog component"
```

---

## Task 5: Create ChatInput Component

**Files:**
- Create: `ui/src/ui/ChatInput.tsx`

**Step 1: Create the chat input**

```tsx
/**
 * Chat Input
 *
 * Input field for sending follow-up messages in a conversation.
 */

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send } from "lucide-react"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Type a message...",
}: ChatInputProps) {
  const [message, setMessage] = useState("")

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (message.trim() && !disabled) {
        onSend(message.trim())
        setMessage("")
      }
    },
    [message, disabled, onSend]
  )

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t border-zinc-800">
      <Input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1"
      />
      <Button type="submit" size="sm" disabled={!message.trim() || disabled}>
        <Send className="h-4 w-4" />
      </Button>
    </form>
  )
}
```

**Step 2: Verify it builds**

Run: `cd ui && pnpm build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add ui/src/ui/ChatInput.tsx
git commit -m "feat(ui): add ChatInput component"
```

---

## Task 6: Update App.tsx with Server Integration

**Files:**
- Modify: `ui/src/App.tsx`

**Step 1: Update App.tsx with new imports and state**

Replace the entire App.tsx with the updated version that integrates bond.server:

```tsx
/**
 * Bond Forensic Timeline
 *
 * Main application shell with:
 * - Header with connection controls
 * - Run status line
 * - Timeline view with blocks
 * - Inspector panel
 * - Replay/Demo controls
 * - Chat input for multi-turn conversations
 */

import { useState, useCallback, useMemo } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Wifi, WifiOff, Loader2 } from "lucide-react"

import { useBondStream } from "@/bond/useBondStream"
import { useBondServer } from "@/bond/useBondServer"
import { useBondReplayFromFile } from "@/bond/useBondReplayFromFile"
import { useReplayState } from "@/bond/useReplayState"
import { useSelection } from "@/ui/useSelection"
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts"

import { Timeline } from "@/ui/Timeline"
import { Inspector } from "@/ui/Inspector"
import { ReplayControls } from "@/ui/ReplayControls"
import { DemoControls } from "@/ui/DemoControls"
import { ConnectDialog } from "@/ui/ConnectDialog"
import { ChatInput } from "@/ui/ChatInput"

type AppMode = "idle" | "live" | "server" | "demo"

export default function App() {
  const [mode, setMode] = useState<AppMode>("idle")
  const [sseUrl, setSseUrl] = useState<string | null>(null)
  const [serverUrl, setServerUrl] = useState<string | null>(null)
  const [connectDialogOpen, setConnectDialogOpen] = useState(false)

  // Stream hook for legacy live mode (direct SSE)
  const stream = useBondStream(sseUrl)

  // Server hook for bond.server integration
  const server = useBondServer(serverUrl)

  // Demo hook for demo mode
  const demo = useBondReplayFromFile()

  // Determine which events/state to use based on mode
  const events =
    mode === "demo"
      ? demo.events
      : mode === "server"
        ? server.history.events
        : stream.history.events
  const liveState =
    mode === "demo"
      ? demo.state
      : mode === "server"
        ? server.state
        : stream.state

  // Replay state for scrubbing through history
  const replay = useReplayState(events)

  // Selection state for inspector
  const selection = useSelection()

  // Determine visible state (live or replayed)
  const visibleState = replay.isAtLive ? liveState : replay.visibleState

  // Find selected block
  const selectedBlock = useMemo(
    () => visibleState.blocks.find((b) => b.id === selection.selectedBlockId),
    [visibleState.blocks, selection.selectedBlockId]
  )

  // Connection status for display
  const connectionStatus =
    mode === "server"
      ? server.status
      : mode === "live"
        ? stream.status
        : "idle"
  const isConnected = connectionStatus === "live" || connectionStatus === "streaming"
  const isConnecting = connectionStatus === "connecting"
  const isStreaming = connectionStatus === "streaming"

  // Event count
  const eventCount = events.length

  // Trace ID
  const traceId =
    mode === "demo"
      ? "demo-001"
      : mode === "server" && server.sessionId
        ? server.sessionId.slice(0, 8)
        : mode === "live"
          ? "live"
          : "—"

  // Status for display
  const displayStatus =
    mode === "demo"
      ? demo.status
      : mode === "server"
        ? server.status
        : mode === "live"
          ? stream.status
          : "idle"

  // Handle connect button - opens dialog for server mode
  const handleConnect = useCallback(() => {
    setConnectDialogOpen(true)
  }, [])

  // Handle server connection from dialog
  const handleServerConnect = useCallback(
    async (url: string, prompt: string) => {
      setServerUrl(url)
      setMode("server")
      setConnectDialogOpen(false)
      // Small delay to ensure state is set
      setTimeout(() => {
        server.sendMessage(prompt)
      }, 0)
    },
    [server]
  )

  // Handle legacy direct SSE connect
  const handleLegacyConnect = useCallback(() => {
    const url = prompt("Enter SSE endpoint URL:", "http://localhost:8000/stream")
    if (url) {
      setSseUrl(url)
      setMode("live")
      stream.connect()
    }
  }, [stream])

  // Handle disconnect
  const handleDisconnect = useCallback(() => {
    if (mode === "server") {
      server.disconnect()
      setServerUrl(null)
    } else {
      stream.disconnect()
      setSseUrl(null)
    }
    setMode("idle")
  }, [mode, server, stream])

  // Handle sending follow-up messages
  const handleSendMessage = useCallback(
    (message: string) => {
      if (mode === "server") {
        server.sendMessage(message)
      }
    },
    [mode, server]
  )

  // Handle demo start
  const handleStartDemo = useCallback(async () => {
    setMode("demo")
    await demo.startDemo("/demo-events.ndjson")
  }, [demo])

  // Handle demo stop
  const handleStopDemo = useCallback(() => {
    demo.stop()
    setMode("idle")
  }, [demo])

  // Toggle pause
  const handleTogglePause = useCallback(() => {
    if (mode === "server") {
      server.setPaused(!server.paused)
    } else if (mode === "live") {
      stream.setPaused(!stream.paused)
    } else if (mode === "demo") {
      if (demo.status === "playing") {
        demo.pause()
      } else if (demo.status === "paused") {
        demo.resume()
      }
    }
  }, [mode, server, stream, demo])

  // Jump to live
  const handleJumpToLive = useCallback(() => {
    replay.jumpToLive()
  }, [replay])

  // Step backward
  const handleStepBackward = useCallback(() => {
    if (replay.position > 0) {
      replay.setPosition(replay.position - 1)
    }
  }, [replay])

  // Step forward
  const handleStepForward = useCallback(() => {
    if (replay.position < replay.totalEvents - 1) {
      replay.setPosition(replay.position + 1)
    }
  }, [replay])

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onTogglePause: handleTogglePause,
    onJumpToLive: handleJumpToLive,
    onStepBackward: handleStepBackward,
    onStepForward: handleStepForward,
    enabled: mode !== "idle",
  })

  const isPaused = mode === "server" ? server.paused : stream.paused

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50" ref={selection.containerRef}>
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-950/60 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-3">
            <div className="text-xl font-semibold tracking-tight">Bond</div>
            <div className="text-sm text-zinc-400">Forensic Timeline</div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={mode === "demo" ? handleStopDemo : handleStartDemo}
              disabled={mode === "live" || mode === "server"}
            >
              {mode === "demo" ? "Stop Demo" : "Run Demo"}
            </Button>
            <Button
              size="sm"
              onClick={
                mode === "live" || mode === "server"
                  ? handleDisconnect
                  : handleConnect
              }
              disabled={mode === "demo"}
            >
              {mode === "live" || mode === "server" ? "Disconnect" : "Connect"}
            </Button>
          </div>
        </div>
      </header>

      {/* Run Header / Status Line */}
      <div className="border-b border-zinc-800/50 bg-zinc-900/30">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">Session:</span>
            <span className="font-mono text-zinc-300">{traceId}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">Status:</span>
            <Badge
              variant={
                displayStatus === "idle"
                  ? "secondary"
                  : displayStatus === "live" ||
                      displayStatus === "playing" ||
                      displayStatus === "streaming"
                    ? "success"
                    : displayStatus === "error"
                      ? "destructive"
                      : "secondary"
              }
              className="text-xs"
            >
              {displayStatus}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">Events:</span>
            <span className="font-mono text-zinc-300">{eventCount}</span>
          </div>
          <div className="ml-auto flex items-center gap-2">
            {isConnecting ? (
              <>
                <Loader2 className="h-4 w-4 text-amber-400 animate-spin" />
                <span className="text-amber-400">Connecting...</span>
              </>
            ) : isStreaming ? (
              <>
                <Loader2 className="h-4 w-4 text-emerald-400 animate-spin" />
                <span className="text-emerald-400">Streaming...</span>
              </>
            ) : isConnected ? (
              <>
                <Wifi className="h-4 w-4 text-emerald-400" />
                <span className="text-emerald-400">Connected</span>
              </>
            ) : mode === "demo" ? (
              <Badge variant="warning" className="text-xs">
                Demo
              </Badge>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-zinc-500" />
                <span className="text-zinc-500">Disconnected</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {mode === "server" && server.error && (
        <div className="bg-red-950/50 border-b border-red-900 px-6 py-2">
          <div className="mx-auto max-w-6xl text-sm text-red-400">
            Error: {server.error}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="mx-auto grid max-w-6xl grid-cols-12 gap-6 px-6 py-6">
        {/* Sidebar */}
        <aside className="col-span-4">
          <Card className="p-4">
            <div className="text-sm font-medium">Session</div>
            <div className="mt-2 text-sm text-zinc-400">
              {mode === "idle" ? (
                <>
                  No stream connected. Click <strong>Connect</strong> to start a
                  live session or <strong>Run Demo</strong> to see a recorded
                  example.
                </>
              ) : mode === "demo" ? (
                <>
                  Playing demo session. Use the controls below to pause, scrub,
                  or change playback speed.
                </>
              ) : mode === "server" ? (
                <>
                  Connected to bond.server. Send messages using the input below.
                  {server.sessionId && (
                    <span className="block mt-1 font-mono text-xs text-zinc-500">
                      Session: {server.sessionId}
                    </span>
                  )}
                </>
              ) : (
                <>
                  Connected to live stream. Events will appear in the timeline
                  as they arrive.
                </>
              )}
            </div>

            {/* Keyboard shortcuts help */}
            {mode !== "idle" && (
              <div className="mt-4 pt-4 border-t border-zinc-800">
                <div className="text-xs text-zinc-500 mb-2">Keyboard Shortcuts</div>
                <div className="grid grid-cols-2 gap-1 text-xs">
                  <div className="text-zinc-400">Space</div>
                  <div className="text-zinc-500">Pause/Play</div>
                  <div className="text-zinc-400">L</div>
                  <div className="text-zinc-500">Jump to Live</div>
                  <div className="text-zinc-400">J / K</div>
                  <div className="text-zinc-500">Step Back/Forward</div>
                  <div className="text-zinc-400">Escape</div>
                  <div className="text-zinc-500">Close Inspector</div>
                </div>
              </div>
            )}
          </Card>
        </aside>

        {/* Timeline */}
        <section className="col-span-8">
          <Card className="overflow-hidden">
            <div className="border-b border-zinc-800 px-4 py-3 flex items-center justify-between">
              <div className="text-sm font-medium">Timeline</div>
              {!replay.isAtLive && (
                <Badge variant="secondary" className="text-xs">
                  Viewing event {replay.position + 1} of {replay.totalEvents}
                </Badge>
              )}
            </div>

            <div className="h-[50vh]">
              <Timeline
                blocks={visibleState.blocks}
                selectedBlockId={selection.selectedBlockId}
                onSelectBlock={selection.toggle}
              />
            </div>

            {/* Chat input for server mode */}
            {mode === "server" && (
              <ChatInput
                onSend={handleSendMessage}
                disabled={isStreaming}
                placeholder={
                  isStreaming ? "Waiting for response..." : "Send a message..."
                }
              />
            )}

            {/* Controls based on mode */}
            {mode === "demo" && (
              <DemoControls
                status={demo.status}
                speed={demo.speed}
                position={replay.position}
                totalEvents={replay.totalEvents}
                onPause={demo.pause}
                onResume={demo.resume}
                onSetSpeed={demo.setSpeed}
                onStop={handleStopDemo}
              />
            )}

            {(mode === "live" || mode === "server") && eventCount > 0 && (
              <ReplayControls
                mode={replay.mode}
                paused={isPaused}
                onPauseToggle={handleTogglePause}
                position={replay.position}
                totalEvents={replay.totalEvents}
                onPositionChange={replay.setPosition}
                onJumpToLive={replay.jumpToLive}
                isAtLive={replay.isAtLive}
              />
            )}
          </Card>
        </section>
      </main>

      {/* Inspector Panel */}
      <Inspector block={selectedBlock} onClose={selection.deselect} />

      {/* Connect Dialog */}
      <ConnectDialog
        open={connectDialogOpen}
        onOpenChange={setConnectDialogOpen}
        onConnect={handleServerConnect}
        isConnecting={isConnecting}
      />
    </div>
  )
}
```

**Step 2: Verify it builds**

Run: `cd ui && pnpm build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add ui/src/App.tsx
git commit -m "feat(ui): integrate bond.server with connect dialog and chat input"
```

---

## Task 7: Test the Integration

**Step 1: Start a test server**

Create a simple test server (`test_server.py`) in the project root:

```python
import os
from bond import BondAgent
from bond.server import create_bond_server

agent = BondAgent(
    name="test-assistant",
    instructions="You are a helpful test assistant. Keep responses brief.",
    model="openai:gpt-4o-mini",
)

app = create_bond_server(agent)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Step 2: Run the server**

```bash
pip install bond-agent[server]
python test_server.py
```

**Step 3: Run the UI**

```bash
cd ui && pnpm dev
```

**Step 4: Test the flow**

1. Open http://localhost:5173
2. Click "Connect"
3. Enter server URL: `http://localhost:8000`
4. Enter message: "Hello! What's 2+2?"
5. Click "Connect"
6. Verify timeline shows streaming events
7. Send follow-up message using chat input
8. Verify conversation continues

**Step 5: Commit test server**

```bash
git add test_server.py
git commit -m "test: add simple test server for UI integration"
```

---

## Task 8: Final Commit and Push

**Step 1: Create final commit with all changes**

```bash
git add -A
git status  # Verify all files
git push
```

**Step 2: Update PR description**

Add to the PR:
- UI now supports full bond.server integration
- Connect dialog for server URL + initial message
- Chat input for multi-turn conversations
- Session persistence across messages
