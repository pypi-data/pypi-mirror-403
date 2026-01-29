"""Trace storage backends.

Provides implementations of TraceStorageProtocol for different
storage systems.
"""

from bond.trace.backends.json_file import JSONFileTraceStore

__all__ = [
    "JSONFileTraceStore",
]
