/**
 * Bond Event Reducer
 *
 * Transforms streaming BondEvents into renderable Block state.
 * Handles active block tracking for streaming UX.
 */

import type {
  BondEvent,
  BondState,
  Block,
  TextBlock,
  ThinkingBlock,
  ToolBlock,
  UnknownBlock,
} from "./types"
import { isTextBlock, isThinkingBlock, isToolBlock } from "./types"

/**
 * Generate block ID from kind and index
 */
function makeBlockId(kind: string, index: number): string {
  return `${kind}:${index}`
}

/**
 * Bond event reducer
 */
export function bondReducer(state: BondState, event: BondEvent): BondState {
  const newEventCount = state.eventCount + 1

  switch (event.type) {
    case "block_start": {
      const id = makeBlockId(event.kind, event.index)

      // Clear active state from previous active block
      const blocks = state.blocks.map((b) =>
        b.isActive ? { ...b, isActive: false } : b
      )

      // Create new block based on kind
      let newBlock: Block

      if (event.kind === "text") {
        newBlock = {
          id,
          kind: "text",
          index: event.index,
          content: "",
          isClosed: false,
          isActive: true,
        } satisfies TextBlock
      } else if (event.kind === "thinking") {
        newBlock = {
          id,
          kind: "thinking",
          index: event.index,
          content: "",
          isClosed: false,
          isActive: true,
        } satisfies ThinkingBlock
      } else if (event.kind === "tool_call") {
        newBlock = {
          id,
          kind: "tool_call",
          index: event.index,
          toolNameDraft: "",
          toolArgsDraft: "",
          status: "forming",
          isClosed: false,
          isActive: true,
        } satisfies ToolBlock
      } else {
        // Unknown kind - create generic block
        newBlock = {
          id,
          kind: "unknown",
          originalKind: event.kind,
          index: event.index,
          content: "",
          isClosed: false,
          isActive: true,
        } satisfies UnknownBlock
      }

      return {
        blocks: [...blocks, newBlock],
        activeBlockId: id,
        eventCount: newEventCount,
      }
    }

    case "text_delta": {
      if (!state.activeBlockId) return { ...state, eventCount: newEventCount }

      const blocks = state.blocks.map((block): Block => {
        if (block.id !== state.activeBlockId) return block
        if (!isTextBlock(block)) return block

        return {
          ...block,
          content: block.content + event.delta,
        }
      })

      return { ...state, blocks, eventCount: newEventCount }
    }

    case "thinking_delta": {
      if (!state.activeBlockId) return { ...state, eventCount: newEventCount }

      const blocks = state.blocks.map((block): Block => {
        if (block.id !== state.activeBlockId) return block
        if (!isThinkingBlock(block)) return block

        return {
          ...block,
          content: block.content + event.delta,
        }
      })

      return { ...state, blocks, eventCount: newEventCount }
    }

    case "tool_call_delta": {
      // tool_delta has no id - attach to currently active tool_call block
      if (!state.activeBlockId) return { ...state, eventCount: newEventCount }

      const blocks = state.blocks.map((block): Block => {
        if (block.id !== state.activeBlockId) return block
        if (!isToolBlock(block)) return block

        return {
          ...block,
          toolNameDraft: block.toolNameDraft + event.nameDelta,
          toolArgsDraft: block.toolArgsDraft + event.argsDelta,
        }
      })

      return { ...state, blocks, eventCount: newEventCount }
    }

    case "tool_execute": {
      // Correlate by finding the tool block that's still "forming"
      // In practice, attach to the most recent tool_call block without a toolId
      const blocks = state.blocks.map((block): Block => {
        if (!isToolBlock(block)) return block
        if (block.status !== "forming") return block

        return {
          ...block,
          toolId: event.id,
          toolName: event.name,
          toolArgs: event.args,
          status: "executing",
        }
      })

      return { ...state, blocks, eventCount: newEventCount }
    }

    case "tool_result": {
      // Correlate by toolId
      const blocks = state.blocks.map((block): Block => {
        if (!isToolBlock(block)) return block
        if (block.toolId !== event.id) return block

        return {
          ...block,
          result: event.result,
          status: "done",
        }
      })

      return { ...state, blocks, eventCount: newEventCount }
    }

    case "block_end": {
      const id = makeBlockId(event.kind, event.index)

      const blocks = state.blocks.map((block): Block => {
        if (block.id !== id) return block

        return {
          ...block,
          isClosed: true,
          isActive: false,
        }
      })

      // Clear active block if it was the one that ended
      const newActiveBlockId =
        state.activeBlockId === id ? undefined : state.activeBlockId

      return {
        blocks,
        activeBlockId: newActiveBlockId,
        eventCount: newEventCount,
      }
    }

    case "complete": {
      // Mark all blocks as closed and inactive
      const blocks = state.blocks.map((block): Block => ({
        ...block,
        isClosed: true,
        isActive: false,
      }))

      return {
        blocks,
        activeBlockId: undefined,
        eventCount: newEventCount,
      }
    }

    default:
      // Unknown event type - ignore
      return { ...state, eventCount: newEventCount }
  }
}

/**
 * Reduce a sequence of events to state
 * Useful for replay: derive visible state from events[0..K]
 */
export function reduceEvents(
  events: BondEvent[],
  initialState: BondState = { blocks: [], activeBlockId: undefined, eventCount: 0 }
): BondState {
  return events.reduce(bondReducer, initialState)
}
