/**
 * Text Block Component
 *
 * Renders text content from the agent with clean prose styling.
 */

import type { TextBlock as TextBlockType } from "@/bond/types"

interface TextBlockProps {
  block: TextBlockType
}

export function TextBlock({ block }: TextBlockProps) {
  return (
    <div className="px-4 py-3">
      <div className="text-[15px] leading-relaxed text-zinc-50 whitespace-pre-wrap">
        {block.content || <span className="text-zinc-500">...</span>}
      </div>
    </div>
  )
}
