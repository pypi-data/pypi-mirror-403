/**
 * Bond Event Types and Block Models
 *
 * Two-mode event story:
 * - Live Mode: WireEvent from WebSocket/SSE (compact format)
 * - Replay/Demo Mode: TraceEvent from NDJSON files (with timestamps)
 */

// =============================================================================
// Wire Format (Live Mode)
// =============================================================================

/**
 * Wire events from create_websocket_handlers() - compact format for streaming
 */
export type WireEvent =
  | { t: "block_start"; kind: string; idx: number }
  | { t: "block_end"; kind: string; idx: number }
  | { t: "text"; c: string }
  | { t: "thinking"; c: string }
  | { t: "tool_delta"; n: string; a: string }
  | { t: "tool_exec"; id: string; name: string; args: Record<string, unknown> }
  | { t: "tool_result"; id: string; name: string; result: string }
  | { t: "complete"; data: unknown }

// =============================================================================
// Trace Format (Replay/Demo Mode)
// =============================================================================

/**
 * TraceEvent from backend - matches src/bond/trace/_models.py
 */
export interface TraceEvent {
  trace_id: string
  sequence: number
  timestamp: number // Monotonic clock (perf_counter)
  wall_time: string // ISO datetime string
  event_type: string // One of 8 types
  payload: Record<string, unknown>
}

// =============================================================================
// Normalized Internal Format
// =============================================================================

/**
 * Block kinds - treat as opaque strings from PydanticAI
 * Known values: text, thinking, tool-call
 */
export type BlockKind = "text" | "thinking" | "tool_call" | string

/**
 * Normalized events used internally after normalization
 */
export type BondEvent =
  | { type: "block_start"; kind: BlockKind; index: number }
  | { type: "block_end"; kind: BlockKind; index: number }
  | { type: "text_delta"; delta: string }
  | { type: "thinking_delta"; delta: string }
  | { type: "tool_call_delta"; nameDelta: string; argsDelta: string }
  | {
      type: "tool_execute"
      id: string
      name: string
      args: Record<string, unknown>
    }
  | { type: "tool_result"; id: string; name: string; result: string }
  | { type: "complete"; data: unknown }

// =============================================================================
// Block Types (UI State)
// =============================================================================

interface BaseBlock {
  id: string
  index: number
  isClosed: boolean
  isActive: boolean
}

export interface TextBlock extends BaseBlock {
  kind: "text"
  content: string
}

export interface ThinkingBlock extends BaseBlock {
  kind: "thinking"
  content: string
}

export interface ToolBlock extends BaseBlock {
  kind: "tool_call"
  // Draft state (streaming)
  toolNameDraft: string
  toolArgsDraft: string
  // Final state (after tool_execute)
  toolId?: string
  toolName?: string
  toolArgs?: Record<string, unknown>
  // Execution state
  status: "forming" | "executing" | "done"
  result?: string
}

export interface UnknownBlock extends BaseBlock {
  kind: "unknown"
  originalKind: string // Store the original unknown kind
  content: string
}

export type Block = TextBlock | ThinkingBlock | ToolBlock | UnknownBlock

// Type guards
export function isTextBlock(block: Block): block is TextBlock {
  return block.kind === "text"
}

export function isThinkingBlock(block: Block): block is ThinkingBlock {
  return block.kind === "thinking"
}

export function isToolBlock(block: Block): block is ToolBlock {
  return block.kind === "tool_call"
}

export function isUnknownBlock(block: Block): block is UnknownBlock {
  return block.kind === "unknown"
}

// =============================================================================
// State Types
// =============================================================================

export interface BondState {
  blocks: Block[]
  activeBlockId: string | undefined
  eventCount: number
}

export const initialBondState: BondState = {
  blocks: [],
  activeBlockId: undefined,
  eventCount: 0,
}
