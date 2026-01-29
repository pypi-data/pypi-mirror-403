/**
 * Timeline Component
 *
 * Main timeline view that renders blocks with:
 * - Framer Motion animations (AnimatePresence)
 * - Auto-scroll when at bottom
 * - "Scroll to bottom" button when scrolled up
 */

import { useEffect, useRef, useState } from "react"
import { AnimatePresence } from "motion/react"
import { ArrowDown, Circle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { Block } from "@/bond/types"
import { BlockCard } from "./BlockCard"

interface TimelineProps {
  blocks: Block[]
  selectedBlockId?: string
  onSelectBlock?: (blockId: string) => void
}

export function Timeline({
  blocks,
  selectedBlockId,
  onSelectBlock,
}: TimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)

  // Intersection Observer to track if user is at bottom
  useEffect(() => {
    const bottom = bottomRef.current
    if (!bottom) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsAtBottom(entry.isIntersecting)
      },
      { threshold: 0.1 }
    )

    observer.observe(bottom)
    return () => observer.disconnect()
  }, [])

  // Auto-scroll when at bottom and new blocks arrive
  useEffect(() => {
    if (isAtBottom && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [blocks.length, isAtBottom])

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  if (blocks.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center">
          <Circle className="mx-auto h-8 w-8 text-zinc-700 animate-pulse" />
          <div className="mt-3 text-sm text-zinc-400">
            Waiting for events...
          </div>
          <div className="mt-1 text-xs text-zinc-500">
            Connect to a stream to see the agent timeline
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-full">
      <ScrollArea className="h-full" ref={scrollRef}>
        <div className="space-y-3 p-4">
          <AnimatePresence initial={false} mode="popLayout">
            {blocks.map((block) => (
              <BlockCard
                key={block.id}
                block={block}
                selected={selectedBlockId === block.id}
                onClick={() => onSelectBlock?.(block.id)}
              />
            ))}
          </AnimatePresence>

          {/* Bottom sentinel for scroll detection */}
          <div ref={bottomRef} className="h-1" />
        </div>
      </ScrollArea>

      {/* Scroll to bottom button */}
      {!isAtBottom && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
          <Button
            variant="secondary"
            size="sm"
            onClick={scrollToBottom}
            className="shadow-lg gap-1"
          >
            <ArrowDown className="h-3 w-3" />
            Scroll to bottom
          </Button>
        </div>
      )}
    </div>
  )
}
