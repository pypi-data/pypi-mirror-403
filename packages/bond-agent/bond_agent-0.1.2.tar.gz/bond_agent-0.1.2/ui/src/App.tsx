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

import { useState, useCallback, useMemo, useEffect } from "react"
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
  const [initialPrompt, setInitialPrompt] = useState<string | null>(null)
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
    (url: string, prompt: string) => {
      setServerUrl(url)
      setInitialPrompt(prompt)
      setMode("server")
      setConnectDialogOpen(false)
    },
    []
  )

  // Trigger initial message when server is ready
  // This avoids race conditions where serverUrl hasn't propagated to useBondServer yet
  useEffect(() => {
    if (
      mode === "server" &&
      serverUrl &&
      initialPrompt &&
      !server.sessionId &&
      !server.error &&
      connectionStatus === "idle"
    ) {
      server.sendMessage(initialPrompt)
      setInitialPrompt(null)
    }
  }, [mode, serverUrl, initialPrompt, server, connectionStatus])


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