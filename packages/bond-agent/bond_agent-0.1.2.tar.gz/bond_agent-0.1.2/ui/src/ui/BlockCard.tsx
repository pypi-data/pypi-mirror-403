/**
 * Block Card Component
 *
 * Wrapper that provides:
 * - Consistent card styling
 * - Active cursor affordance (glow + shimmer)
 * - Framer Motion animations
 */

import { motion } from "motion/react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { Block } from "@/bond/types"
import { isTextBlock, isThinkingBlock, isToolBlock } from "@/bond/types"
import { TextBlock } from "./TextBlock"
import { ThinkingBlock } from "./ThinkingBlock"
import { ToolBlock } from "./ToolBlock"

interface BlockCardProps {
  block: Block
  onClick?: () => void
  selected?: boolean
}

export function BlockCard({ block, onClick, selected }: BlockCardProps) {
  const renderContent = () => {
    if (isTextBlock(block)) {
      return <TextBlock block={block} />
    }
    if (isThinkingBlock(block)) {
      return <ThinkingBlock block={block} />
    }
    if (isToolBlock(block)) {
      return <ToolBlock block={block} />
    }
    // Unknown kind - render as generic text
    // At this point, block is UnknownBlock
    const unknownBlock = block
    return (
      <div className="px-4 py-3">
        <div className="mb-2 text-xs font-medium text-zinc-500">
          {unknownBlock.originalKind}
        </div>
        <div className="text-sm text-zinc-400 whitespace-pre-wrap">
          {unknownBlock.content || "..."}
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      layout
    >
      <Card
        className={cn(
          "border-zinc-800 bg-zinc-900/40 cursor-pointer transition-all duration-200",
          // Active cursor affordance - soft glow
          block.isActive && [
            "border-zinc-600",
            "shadow-[0_0_15px_rgba(161,161,170,0.1)]",
            "ring-1 ring-zinc-700/50",
          ],
          // Selected state
          selected && "ring-2 ring-zinc-500",
          // Hover state
          !block.isActive && "hover:border-zinc-700"
        )}
        onClick={onClick}
      >
        {/* Shimmer overlay for active blocks */}
        {block.isActive && (
          <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none">
            <div
              className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-zinc-700/10 to-transparent"
              style={{
                animationDuration: "2s",
                animationIterationCount: "infinite",
              }}
            />
          </div>
        )}

        <div className="relative">{renderContent()}</div>
      </Card>
    </motion.div>
  )
}
