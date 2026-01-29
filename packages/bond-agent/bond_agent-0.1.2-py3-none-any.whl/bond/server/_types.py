"""Server configuration and request types.

Type definitions for the Bond server module.
"""

from dataclasses import dataclass, field
from typing import Annotated

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request to start a new agent conversation.

    Sent to POST /ask endpoint to initiate a streaming session.
    """

    prompt: Annotated[
        str,
        Field(description="The user's message/question for the agent"),
    ]

    session_id: Annotated[
        str | None,
        Field(default=None, description="Optional session ID to continue a conversation"),
    ]


class SessionResponse(BaseModel):
    """Response from POST /ask with session information.

    Contains the session_id needed to connect to the SSE stream.
    """

    session_id: Annotated[
        str,
        Field(description="Unique session identifier"),
    ]

    stream_url: Annotated[
        str,
        Field(description="URL to connect for SSE streaming"),
    ]


class HealthResponse(BaseModel):
    """Health check response."""

    status: Annotated[str, Field(description="Service status")]
    agent_name: Annotated[str, Field(description="Name of the configured agent")]


@dataclass
class ServerConfig:
    """Configuration for the Bond server.

    Attributes:
        host: Host to bind to (default: "0.0.0.0").
        port: Port to bind to (default: 8000).
        cors_origins: Allowed CORS origins (default: ["*"]).
        session_timeout_seconds: Session expiry time (default: 3600).
        max_concurrent_sessions: Maximum concurrent sessions (default: 100).
    """

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    session_timeout_seconds: int = 3600
    max_concurrent_sessions: int = 100

    def get_stream_url(self, session_id: str) -> str:
        """Generate the stream URL for a session."""
        return f"/stream/{session_id}"
