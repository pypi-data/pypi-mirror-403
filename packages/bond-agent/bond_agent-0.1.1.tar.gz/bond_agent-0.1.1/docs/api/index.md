# API Reference

This section provides auto-generated documentation from the Bond source code.

## Modules

| Module | Description |
|--------|-------------|
| [Agent](agent.md) | Core `BondAgent` and `StreamHandlers` classes |
| [Utilities](utils.md) | Handler factory functions for WebSocket, SSE, and print |
| [Tools](tools.md) | Tool patterns and bundled toolsets |

## Quick Links

### Core Classes

- [`BondAgent`](agent.md#bond.BondAgent) - The main agent runtime
- [`StreamHandlers`](agent.md#bond.StreamHandlers) - Streaming callbacks

### Handler Factories

- [`create_websocket_handlers`](utils.md#bond.create_websocket_handlers) - WebSocket streaming
- [`create_sse_handlers`](utils.md#bond.create_sse_handlers) - SSE streaming
- [`create_print_handlers`](utils.md#bond.create_print_handlers) - Console output

### Tools

- [Memory Toolset](tools.md#memory-toolset) - Semantic memory storage
- [Schema Toolset](tools.md#schema-toolset) - Database schema lookup
