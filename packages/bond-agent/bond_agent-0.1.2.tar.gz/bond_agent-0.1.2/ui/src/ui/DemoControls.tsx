/**
 * Demo Controls Component
 *
 * Playback controls for demo mode:
 * - Play/Pause toggle
 * - Speed selector (0.5x, 1x, 2x)
 * - Progress indicator
 * - Demo mode badge
 */

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Pause, Play, Square, Film, Gauge } from "lucide-react"
import { cn } from "@/lib/utils"
import type { DemoStatus, PlaybackSpeed } from "@/bond/useBondReplayFromFile"

interface DemoControlsProps {
  /** Current demo status */
  status: DemoStatus
  /** Current playback speed */
  speed: PlaybackSpeed
  /** Current position */
  position: number
  /** Total events */
  totalEvents: number
  /** Pause playback */
  onPause: () => void
  /** Resume playback */
  onResume: () => void
  /** Set speed */
  onSetSpeed: (speed: PlaybackSpeed) => void
  /** Stop demo */
  onStop: () => void
}

const SPEEDS: PlaybackSpeed[] = [0.5, 1, 2]

export function DemoControls({
  status,
  speed,
  position,
  totalEvents,
  onPause,
  onResume,
  onSetSpeed,
  onStop,
}: DemoControlsProps) {
  const isPlaying = status === "playing"
  const isComplete = status === "complete"
  const hasEvents = totalEvents > 0

  // Cycle through speeds
  const cycleSpeed = () => {
    const currentIndex = SPEEDS.indexOf(speed)
    const nextIndex = (currentIndex + 1) % SPEEDS.length
    onSetSpeed(SPEEDS[nextIndex])
  }

  return (
    <div className="flex items-center gap-3 px-4 py-2 border-t border-zinc-800 bg-amber-950/20">
      {/* Demo mode indicator */}
      <Badge variant="warning" className="text-xs gap-1">
        <Film className="h-3 w-3" />
        Demo Mode
      </Badge>

      {/* Play/Pause */}
      <Button
        variant="ghost"
        size="sm"
        onClick={isPlaying ? onPause : onResume}
        disabled={!hasEvents || isComplete}
        className="h-8 w-8 p-0"
        title={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? (
          <Pause className="h-4 w-4" />
        ) : (
          <Play className="h-4 w-4" />
        )}
      </Button>

      {/* Stop */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onStop}
        disabled={status === "idle"}
        className="h-8 w-8 p-0"
        title="Stop"
      >
        <Square className="h-4 w-4" />
      </Button>

      {/* Speed control */}
      <Button
        variant="ghost"
        size="sm"
        onClick={cycleSpeed}
        disabled={!hasEvents}
        className="h-8 gap-1 text-xs"
        title="Change speed"
      >
        <Gauge className="h-3 w-3" />
        {speed}x
      </Button>

      {/* Progress */}
      <div className="flex-1">
        <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full bg-amber-500/50 transition-all duration-200",
              isComplete && "bg-amber-500"
            )}
            style={{
              width: totalEvents > 0 ? `${((position + 1) / totalEvents) * 100}%` : "0%",
            }}
          />
        </div>
      </div>

      {/* Position display */}
      <div className="text-xs text-zinc-500 tabular-nums min-w-[4rem] text-right">
        {hasEvents ? (
          <>
            <span className="text-zinc-300">{position + 1}</span>
            <span className="mx-0.5">/</span>
            <span>{totalEvents}</span>
          </>
        ) : (
          "—"
        )}
      </div>

      {/* Status indicator */}
      <Badge
        variant={isComplete ? "success" : isPlaying ? "default" : "secondary"}
        className="text-xs"
      >
        {status === "loading" && "Loading..."}
        {status === "playing" && "Playing"}
        {status === "paused" && "Paused"}
        {status === "complete" && "Complete"}
        {status === "idle" && "Ready"}
      </Badge>
    </div>
  )
}
