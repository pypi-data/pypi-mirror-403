"""Bond Server - Production-ready streaming server for Bond agents.

This module provides a complete ASGI server that any Bond agent can use
for SSE and WebSocket streaming to UIs and clients.

Example:
    ```python
    from bond import BondAgent
    from bond.server import create_bond_server

    agent = BondAgent(
        name="assistant",
        instructions="You are helpful.",
        model="openai:gpt-4o",
    )

    # Create ASGI app
    app = create_bond_server(agent)

    # Run with uvicorn
    # uvicorn main:app --reload
    ```

Endpoints:
    - POST /ask: Send prompt, get session_id for streaming
    - GET /stream/{session_id}: SSE stream for agent response
    - WS /ws: WebSocket bidirectional streaming
    - GET /health: Health check
"""

from bond.server._app import create_bond_server
from bond.server._session import Session, SessionManager, SessionStatus
from bond.server._types import (
    AskRequest,
    HealthResponse,
    ServerConfig,
    SessionResponse,
)

__all__ = [
    # Main factory
    "create_bond_server",
    # Session management
    "SessionManager",
    "Session",
    "SessionStatus",
    # Types
    "ServerConfig",
    "AskRequest",
    "SessionResponse",
    "HealthResponse",
]
