/**
 * Tool Block Component
 *
 * Renders tool calls with:
 * - Tool name and status badge
 * - Streaming args in monospace
 * - Result panel when done
 */

import { Badge } from "@/components/ui/badge"
import { Wrench, Loader2, Check } from "lucide-react"
import type { ToolBlock as ToolBlockType } from "@/bond/types"

interface ToolBlockProps {
  block: ToolBlockType
}

function StatusBadge({ status }: { status: ToolBlockType["status"] }) {
  switch (status) {
    case "forming":
      return (
        <Badge variant="secondary" className="text-xs gap-1">
          <span className="animate-pulse">●</span>
          forming
        </Badge>
      )
    case "executing":
      return (
        <Badge variant="warning" className="text-xs gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          executing
        </Badge>
      )
    case "done":
      return (
        <Badge variant="success" className="text-xs gap-1">
          <Check className="h-3 w-3" />
          done
        </Badge>
      )
  }
}

export function ToolBlock({ block }: ToolBlockProps) {
  const toolName = block.toolName ?? block.toolNameDraft
  const toolArgs = block.toolArgs
    ? JSON.stringify(block.toolArgs, null, 2)
    : block.toolArgsDraft

  return (
    <div className="px-4 py-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Wrench className="h-4 w-4 text-zinc-500" />
        <div className="text-xs font-medium text-zinc-500">Tool</div>
        <div className="font-mono text-sm text-zinc-100">
          {toolName || "..."}
        </div>
        <div className="ml-auto">
          <StatusBadge status={block.status} />
        </div>
      </div>

      {/* Args */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-3 mb-3">
        <div className="mb-2 text-xs text-zinc-500">Arguments</div>
        <pre className="overflow-x-auto text-xs text-zinc-300 font-mono">
          {toolArgs || "..."}
        </pre>
      </div>

      {/* Result (when done) */}
      {block.result && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-3">
          <div className="mb-2 text-xs text-zinc-500">Result</div>
          <pre className="overflow-x-auto text-xs text-zinc-300 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
            {block.result}
          </pre>
        </div>
      )}
    </div>
  )
}
