/**
 * Event normalization layer
 *
 * Converts various event formats to the internal BondEvent type:
 * - WireEvent (WebSocket JSON)
 * - SSE events (named event types)
 * - TraceEvent (replay/demo NDJSON)
 */

import type { WireEvent, TraceEvent, BondEvent, BlockKind } from "./types"

/**
 * Normalize block kind string to internal format
 * Maps PydanticAI part_kind values to our BlockKind
 */
function normalizeKind(kind: string): BlockKind {
  // Handle known PydanticAI part kinds
  const kindMap: Record<string, BlockKind> = {
    text: "text",
    "text-part": "text",
    thinking: "thinking",
    "thinking-part": "thinking",
    "tool-call": "tool_call",
    "tool-call-part": "tool_call",
    tool_call: "tool_call",
  }
  return kindMap[kind.toLowerCase()] ?? kind
}

/**
 * Normalize WebSocket wire event to BondEvent
 */
export function normalizeWireEvent(wire: WireEvent): BondEvent {
  switch (wire.t) {
    case "block_start":
      return {
        type: "block_start",
        kind: normalizeKind(wire.kind),
        index: wire.idx,
      }

    case "block_end":
      return {
        type: "block_end",
        kind: normalizeKind(wire.kind),
        index: wire.idx,
      }

    case "text":
      return { type: "text_delta", delta: wire.c }

    case "thinking":
      return { type: "thinking_delta", delta: wire.c }

    case "tool_delta":
      return { type: "tool_call_delta", nameDelta: wire.n, argsDelta: wire.a }

    case "tool_exec":
      return {
        type: "tool_execute",
        id: wire.id,
        name: wire.name,
        args: wire.args,
      }

    case "tool_result":
      return {
        type: "tool_result",
        id: wire.id,
        name: wire.name,
        result: wire.result,
      }

    case "complete":
      return { type: "complete", data: wire.data }
  }
}

/**
 * SSE event data types (after JSON.parse of data field)
 */
type SSEBlockData = { kind: string; idx: number }
type SSETextData = { c: string } | { content: string }
type SSEToolDeltaData = { n?: string; a?: string; name?: string; args?: string }
type SSEToolExecData = { id: string; name: string; args: Record<string, unknown> }
type SSEToolResultData = { id: string; name: string; result: string }
type SSECompleteData = { data: unknown }

/**
 * Normalize SSE event (named event type + data payload)
 * SSE uses: event: <type>\ndata: <json>
 */
export function normalizeSSEEvent(
  eventType: string,
  data: unknown
): BondEvent | null {
  switch (eventType) {
    case "block_start": {
      const d = data as SSEBlockData
      return {
        type: "block_start",
        kind: normalizeKind(d.kind),
        index: d.idx,
      }
    }

    case "block_end": {
      const d = data as SSEBlockData
      return {
        type: "block_end",
        kind: normalizeKind(d.kind),
        index: d.idx,
      }
    }

    case "text": {
      const d = data as SSETextData
      const content = "c" in d ? d.c : d.content
      return { type: "text_delta", delta: content }
    }

    case "thinking": {
      const d = data as SSETextData
      const content = "c" in d ? d.c : d.content
      return { type: "thinking_delta", delta: content }
    }

    case "tool_delta": {
      const d = data as SSEToolDeltaData
      const name = d.name ?? d.n ?? ""
      const args = d.args ?? d.a ?? ""
      return { type: "tool_call_delta", nameDelta: name, argsDelta: args }
    }

    case "tool_exec": {
      const d = data as SSEToolExecData
      return { type: "tool_execute", id: d.id, name: d.name, args: d.args }
    }

    case "tool_result": {
      const d = data as SSEToolResultData
      return { type: "tool_result", id: d.id, name: d.name, result: d.result }
    }

    case "complete": {
      const d = data as SSECompleteData
      return { type: "complete", data: d.data }
    }

    default:
      // Unknown event type - ignore gracefully
      console.warn(`Unknown SSE event type: ${eventType}`)
      return null
  }
}

/**
 * Normalize TraceEvent from replay/demo files
 * TraceEvent has richer metadata including timestamps
 */
export function normalizeTraceEvent(trace: TraceEvent): BondEvent | null {
  const { event_type, payload } = trace

  switch (event_type) {
    case "block_start":
      return {
        type: "block_start",
        kind: normalizeKind(payload.kind as string),
        index: payload.index as number,
      }

    case "block_end":
      return {
        type: "block_end",
        kind: normalizeKind(payload.kind as string),
        index: payload.index as number,
      }

    case "text_delta":
      return { type: "text_delta", delta: payload.text as string }

    case "thinking_delta":
      return { type: "thinking_delta", delta: payload.text as string }

    case "tool_call_delta":
      return {
        type: "tool_call_delta",
        nameDelta: (payload.name as string) ?? "",
        argsDelta: (payload.args as string) ?? "",
      }

    case "tool_execute":
      return {
        type: "tool_execute",
        id: payload.id as string,
        name: payload.name as string,
        args: payload.args as Record<string, unknown>,
      }

    case "tool_result":
      return {
        type: "tool_result",
        id: payload.id as string,
        name: payload.name as string,
        result: payload.result as string,
      }

    case "complete":
      return { type: "complete", data: payload.data }

    default:
      console.warn(`Unknown TraceEvent type: ${event_type}`)
      return null
  }
}
