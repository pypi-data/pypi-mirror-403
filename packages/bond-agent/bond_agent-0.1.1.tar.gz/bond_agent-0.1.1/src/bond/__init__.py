"""Bond - The Forensic Runtime for AI agents.

Full-spectrum streaming with complete observability. Every token, every thought,
every tool call - captured and surfaced in real-time.
"""

from bond.agent import BondAgent, StreamHandlers
from bond.trace import (
    JSONFileTraceStore,
    TraceEvent,
    TraceMeta,
    TraceReplayer,
    TraceStorageProtocol,
    create_capture_handlers,
    finalize_capture,
)
from bond.utils import (
    create_print_handlers,
    create_sse_handlers,
    create_websocket_handlers,
)

__version__ = "0.1.0"

__all__ = [
    # Core
    "BondAgent",
    "StreamHandlers",
    # Utilities
    "create_websocket_handlers",
    "create_sse_handlers",
    "create_print_handlers",
    # Trace
    "TraceEvent",
    "TraceMeta",
    "TraceStorageProtocol",
    "JSONFileTraceStore",
    "create_capture_handlers",
    "finalize_capture",
    "TraceReplayer",
]
