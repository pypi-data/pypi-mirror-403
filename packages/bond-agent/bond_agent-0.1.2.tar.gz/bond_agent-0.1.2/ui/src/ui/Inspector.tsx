/**
 * Inspector Panel Component
 *
 * Shows detailed information about a selected block:
 * - Block type, ID, and status
 * - Full content (not truncated)
 * - Tool details (for tool blocks)
 * - Copy as JSON functionality
 */

import { useState, useCallback, useEffect } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  X,
  Copy,
  Check,
  FileText,
  Brain,
  Wrench,
  HelpCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { Block } from "@/bond/types"
import {
  isTextBlock,
  isThinkingBlock,
  isToolBlock,
  isUnknownBlock,
} from "@/bond/types"

interface InspectorProps {
  /** Selected block to inspect */
  block: Block | undefined
  /** Close the inspector */
  onClose: () => void
}

function BlockIcon({ kind }: { kind: string }) {
  switch (kind) {
    case "text":
      return <FileText className="h-4 w-4" />
    case "thinking":
      return <Brain className="h-4 w-4" />
    case "tool_call":
      return <Wrench className="h-4 w-4" />
    default:
      return <HelpCircle className="h-4 w-4" />
  }
}

function KindBadge({ kind }: { kind: string }) {
  const variants: Record<string, "default" | "secondary" | "warning"> = {
    text: "default",
    thinking: "secondary",
    tool_call: "warning",
  }

  return (
    <Badge variant={variants[kind] || "secondary"} className="text-xs gap-1">
      <BlockIcon kind={kind} />
      {kind}
    </Badge>
  )
}

export function Inspector({ block, onClose }: InspectorProps) {
  const [copied, setCopied] = useState(false)

  // Reset copied state when block changes
  useEffect(() => {
    setCopied(false)
  }, [block?.id])

  const handleCopy = useCallback(async () => {
    if (!block) return

    try {
      const json = JSON.stringify(block, null, 2)
      await navigator.clipboard.writeText(json)
      setCopied(true)

      // Reset after 2 seconds
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }, [block])

  return (
    <AnimatePresence>
      {block && (
        <motion.div
          initial={{ x: "100%", opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="fixed top-0 right-0 h-full w-96 z-50"
        >
          <Card className="h-full rounded-none border-l border-zinc-800 bg-zinc-900/95 backdrop-blur">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Inspector</span>
                <KindBadge kind={block.kind} />
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Content */}
            <div className="overflow-y-auto h-[calc(100%-60px)] p-4 space-y-4">
              {/* ID and Index */}
              <Section title="Identification">
                <InfoRow label="Block ID" value={block.id} mono />
                <InfoRow label="Index" value={block.index.toString()} />
                <InfoRow
                  label="Status"
                  value={
                    <div className="flex items-center gap-2">
                      {block.isActive && (
                        <Badge variant="success" className="text-xs">
                          Active
                        </Badge>
                      )}
                      {block.isClosed && (
                        <Badge variant="secondary" className="text-xs">
                          Closed
                        </Badge>
                      )}
                      {!block.isActive && !block.isClosed && (
                        <Badge variant="secondary" className="text-xs">
                          Open
                        </Badge>
                      )}
                    </div>
                  }
                />
              </Section>

              {/* Content (for text/thinking blocks) */}
              {(isTextBlock(block) || isThinkingBlock(block)) && (
                <Section title="Content">
                  <pre className="text-sm text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-950/50 rounded-lg p-3 max-h-64 overflow-y-auto">
                    {block.content || "(empty)"}
                  </pre>
                  <div className="text-xs text-zinc-500 mt-1">
                    {block.content.length} characters
                  </div>
                </Section>
              )}

              {/* Tool Details (for tool blocks) */}
              {isToolBlock(block) && (
                <>
                  <Section title="Tool Info">
                    <InfoRow
                      label="Tool ID"
                      value={block.toolId || "(pending)"}
                      mono
                    />
                    <InfoRow
                      label="Tool Name"
                      value={block.toolName || block.toolNameDraft || "(forming)"}
                      mono
                    />
                    <InfoRow
                      label="Status"
                      value={
                        <Badge
                          variant={
                            block.status === "done"
                              ? "success"
                              : block.status === "executing"
                                ? "warning"
                                : "secondary"
                          }
                          className="text-xs"
                        >
                          {block.status}
                        </Badge>
                      }
                    />
                  </Section>

                  <Section title="Arguments">
                    <pre className="text-sm text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-950/50 rounded-lg p-3 max-h-48 overflow-y-auto">
                      {block.toolArgs
                        ? JSON.stringify(block.toolArgs, null, 2)
                        : block.toolArgsDraft || "(forming)"}
                    </pre>
                  </Section>

                  {block.result && (
                    <Section title="Result">
                      <pre className="text-sm text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-950/50 rounded-lg p-3 max-h-48 overflow-y-auto">
                        {block.result}
                      </pre>
                      <div className="text-xs text-zinc-500 mt-1">
                        {block.result.length} characters
                      </div>
                    </Section>
                  )}
                </>
              )}

              {/* Unknown block content */}
              {isUnknownBlock(block) && (
                <Section title="Content">
                  <InfoRow label="Original Kind" value={block.originalKind} mono />
                  <pre className="text-sm text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-950/50 rounded-lg p-3 max-h-64 overflow-y-auto mt-2">
                    {block.content || "(empty)"}
                  </pre>
                </Section>
              )}

              {/* Copy as JSON */}
              <div className="pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleCopy}
                  className={cn(
                    "w-full gap-2 transition-colors",
                    copied && "bg-emerald-900/30 text-emerald-400"
                  )}
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy as JSON
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// Helper components

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div>
      <div className="text-xs font-medium text-zinc-500 mb-2">{title}</div>
      {children}
    </div>
  )
}

function InfoRow({
  label,
  value,
  mono = false,
}: {
  label: string
  value: React.ReactNode
  mono?: boolean
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-zinc-400">{label}</span>
      <span
        className={cn("text-sm text-zinc-200", mono && "font-mono text-xs")}
      >
        {value}
      </span>
    </div>
  )
}
