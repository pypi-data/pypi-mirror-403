/**
 * Thinking Block Component
 *
 * Renders thinking/reasoning content with subtle, dimmer styling.
 * Shows "Thinking" label to distinguish from regular text.
 */

import { useState } from "react"
import { ChevronDown, ChevronRight, Brain } from "lucide-react"
import type { ThinkingBlock as ThinkingBlockType } from "@/bond/types"

interface ThinkingBlockProps {
  block: ThinkingBlockType
}

export function ThinkingBlock({ block }: ThinkingBlockProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="px-4 py-3">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 text-xs font-medium text-zinc-500 hover:text-zinc-400 transition-colors mb-2"
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        <Brain className="h-3 w-3" />
        <span>Thinking</span>
        {collapsed && (
          <span className="text-zinc-600 font-normal">
            ({block.content.length} chars)
          </span>
        )}
      </button>

      {!collapsed && (
        <div className="text-sm leading-relaxed text-zinc-400 whitespace-pre-wrap pl-5">
          {block.content || <span className="text-zinc-600">...</span>}
        </div>
      )}
    </div>
  )
}
