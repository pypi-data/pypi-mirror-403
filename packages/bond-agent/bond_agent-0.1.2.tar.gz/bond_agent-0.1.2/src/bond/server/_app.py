"""ASGI application factory for Bond server.

Creates a production-ready Starlette application for any BondAgent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from bond.server._routes import BondRoutes
from bond.server._session import SessionManager
from bond.server._types import ServerConfig

if TYPE_CHECKING:
    from bond.agent import BondAgent


def create_bond_server(
    agent: BondAgent[Any, Any],
    config: ServerConfig | None = None,
) -> Starlette:
    """Create a production-ready ASGI server for a BondAgent.

    Creates a Starlette application with SSE and WebSocket endpoints
    for streaming agent responses to UIs and clients.

    Args:
        agent: The BondAgent to serve.
        config: Optional server configuration. Uses defaults if not provided.

    Returns:
        Starlette ASGI application ready for uvicorn or other ASGI servers.

    Example:
        ```python
        from bond import BondAgent
        from bond.server import create_bond_server, ServerConfig

        agent = BondAgent(
            name="assistant",
            instructions="You are helpful.",
            model="openai:gpt-4o",
        )

        # Default configuration
        app = create_bond_server(agent)

        # Custom configuration
        app = create_bond_server(
            agent,
            config=ServerConfig(
                port=3000,
                cors_origins=["http://localhost:5173"],
            ),
        )

        # Run with uvicorn
        # uvicorn main:app --host 0.0.0.0 --port 8000
        ```

    Endpoints:
        POST /ask:
            Request: {"prompt": "...", "session_id": "..." (optional)}
            Response: {"session_id": "...", "stream_url": "/stream/..."}

        GET /stream/{session_id}:
            SSE stream with events: text, thinking, tool_exec, tool_result, etc.

        WS /ws:
            WebSocket endpoint. Send {"prompt": "..."}, receive streaming events.

        GET /health:
            Response: {"status": "healthy", "agent_name": "..."}
    """
    if config is None:
        config = ServerConfig()

    # Create session manager
    session_manager = SessionManager(
        timeout_seconds=config.session_timeout_seconds,
        max_sessions=config.max_concurrent_sessions,
    )

    # Create routes
    routes = BondRoutes(agent, session_manager, config)

    # Configure CORS middleware
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]

    # Create Starlette app
    app = Starlette(
        routes=routes.get_routes(),
        middleware=middleware,
        debug=False,
    )

    # Store references for access
    app.state.agent = agent
    app.state.session_manager = session_manager
    app.state.config = config

    return app
