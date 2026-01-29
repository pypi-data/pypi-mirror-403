/**
 * Replay Controls Component
 *
 * Provides UI for scrubbing through event history:
 * - Play/Pause toggle
 * - Position slider (0..N events)
 * - Live/Replay indicator
 * - Jump to Live button
 */

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Pause, Play, Radio, History, FastForward } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ReplayMode } from "@/bond/useReplayState"

interface ReplayControlsProps {
  /** Current mode (live or replay) */
  mode: ReplayMode
  /** Whether stream is paused */
  paused: boolean
  /** Toggle pause state */
  onPauseToggle: () => void
  /** Current position in event history */
  position: number
  /** Total events in history */
  totalEvents: number
  /** Set position (scrub) */
  onPositionChange: (position: number) => void
  /** Jump to live */
  onJumpToLive: () => void
  /** Whether we're at live position */
  isAtLive: boolean
}

export function ReplayControls({
  mode,
  paused,
  onPauseToggle,
  position,
  totalEvents,
  onPositionChange,
  onJumpToLive,
  isAtLive,
}: ReplayControlsProps) {
  const hasEvents = totalEvents > 0

  return (
    <div className="flex items-center gap-3 px-4 py-2 border-t border-zinc-800 bg-zinc-900/50">
      {/* Play/Pause */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onPauseToggle}
        disabled={!hasEvents}
        className="h-8 w-8 p-0"
        title={paused ? "Resume" : "Pause"}
      >
        {paused ? (
          <Play className="h-4 w-4" />
        ) : (
          <Pause className="h-4 w-4" />
        )}
      </Button>

      {/* Mode indicator */}
      <Badge
        variant={mode === "live" ? "success" : "secondary"}
        className={cn(
          "text-xs gap-1 transition-colors",
          mode === "live" && "animate-pulse"
        )}
      >
        {mode === "live" ? (
          <>
            <Radio className="h-3 w-3" />
            Live
          </>
        ) : (
          <>
            <History className="h-3 w-3" />
            Replay
          </>
        )}
      </Badge>

      {/* Scrubber slider */}
      <div className="flex-1 flex items-center gap-3">
        <input
          type="range"
          min={0}
          max={Math.max(0, totalEvents - 1)}
          value={position}
          onChange={(e) => onPositionChange(parseInt(e.target.value, 10))}
          disabled={!hasEvents}
          className={cn(
            "flex-1 h-1 bg-zinc-700 rounded-full appearance-none cursor-pointer",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "[&::-webkit-slider-thumb]:appearance-none",
            "[&::-webkit-slider-thumb]:w-3",
            "[&::-webkit-slider-thumb]:h-3",
            "[&::-webkit-slider-thumb]:rounded-full",
            "[&::-webkit-slider-thumb]:bg-zinc-300",
            "[&::-webkit-slider-thumb]:hover:bg-zinc-100",
            "[&::-webkit-slider-thumb]:transition-colors",
            "[&::-moz-range-thumb]:w-3",
            "[&::-moz-range-thumb]:h-3",
            "[&::-moz-range-thumb]:rounded-full",
            "[&::-moz-range-thumb]:bg-zinc-300",
            "[&::-moz-range-thumb]:border-0",
            "[&::-moz-range-thumb]:hover:bg-zinc-100"
          )}
        />

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
      </div>

      {/* Jump to Live button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onJumpToLive}
        disabled={isAtLive || !hasEvents}
        className={cn(
          "h-8 gap-1 text-xs",
          !isAtLive && hasEvents && "text-emerald-400 hover:text-emerald-300"
        )}
      >
        <FastForward className="h-3 w-3" />
        Live
      </Button>
    </div>
  )
}
