"""Session management for Bond server.

Handles session creation, lookup, and cleanup for streaming connections.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic_ai.messages import ModelMessage


class SessionStatus(str, Enum):
    """Status of a streaming session."""

    PENDING = "pending"  # Created, waiting for SSE connection
    STREAMING = "streaming"  # Currently streaming response
    COMPLETED = "completed"  # Response finished
    ERROR = "error"  # Error occurred
    EXPIRED = "expired"  # Session timed out


@dataclass
class Session:
    """A streaming session for an agent conversation.

    Attributes:
        session_id: Unique session identifier.
        prompt: The user's prompt for this session.
        status: Current session status.
        created_at: Unix timestamp when session was created.
        history: Conversation history for multi-turn sessions.
        result_queue: Queue for streaming results to SSE connection.
        error: Error message if status is ERROR.
    """

    session_id: str
    prompt: str
    status: SessionStatus = SessionStatus.PENDING
    created_at: float = field(default_factory=time.time)
    history: list[ModelMessage] = field(default_factory=list)
    result_queue: asyncio.Queue[dict[str, Any]] = field(default_factory=asyncio.Queue)
    error: str | None = None

    def is_expired(self, timeout_seconds: int) -> bool:
        """Check if session has expired based on timeout."""
        return time.time() - self.created_at > timeout_seconds


class SessionManager:
    """Manages active streaming sessions.

    Thread-safe session storage with automatic cleanup of expired sessions.

    Example:
        ```python
        manager = SessionManager(timeout_seconds=3600)

        # Create a session
        session = manager.create_session("What is 2+2?")

        # Get the session later
        session = manager.get_session(session.session_id)

        # Update status
        manager.update_status(session.session_id, SessionStatus.STREAMING)

        # Cleanup expired sessions periodically
        await manager.cleanup_expired()
        ```
    """

    def __init__(
        self,
        timeout_seconds: int = 3600,
        max_sessions: int = 100,
    ) -> None:
        """Initialize session manager.

        Args:
            timeout_seconds: Time before sessions expire.
            max_sessions: Maximum concurrent sessions allowed.
        """
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._timeout_seconds = timeout_seconds
        self._max_sessions = max_sessions

    async def create_session(
        self,
        prompt: str,
        history: list[ModelMessage] | None = None,
        session_id: str | None = None,
    ) -> Session:
        """Create a new streaming session.

        Args:
            prompt: The user's prompt.
            history: Optional conversation history.
            session_id: Optional session ID to reuse (for continuing conversations).

        Returns:
            The created Session object.

        Raises:
            ValueError: If max sessions reached.
        """
        async with self._lock:
            # Cleanup expired first to make room
            await self._cleanup_expired_locked()

            if len(self._sessions) >= self._max_sessions:
                raise ValueError(f"Maximum concurrent sessions ({self._max_sessions}) reached")

            # Use provided session_id or generate new one
            if session_id and session_id in self._sessions:
                # Continuing existing session
                session = self._sessions[session_id]
                session.prompt = prompt
                session.status = SessionStatus.PENDING
                session.created_at = time.time()
                session.result_queue = asyncio.Queue()
                session.error = None
            else:
                # New session
                new_id = session_id or str(uuid.uuid4())
                session = Session(
                    session_id=new_id,
                    prompt=prompt,
                    history=list(history) if history else [],
                )
                self._sessions[new_id] = session

            return session

    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The Session if found and not expired, None otherwise.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_expired(self._timeout_seconds):
                session.status = SessionStatus.EXPIRED
                del self._sessions[session_id]
                return None
            return session

    async def update_status(
        self,
        session_id: str,
        status: SessionStatus,
        error: str | None = None,
    ) -> None:
        """Update session status.

        Args:
            session_id: The session to update.
            status: New status.
            error: Optional error message (for ERROR status).
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.status = status
                if error:
                    session.error = error

    async def update_history(
        self,
        session_id: str,
        history: list[ModelMessage],
    ) -> None:
        """Update session conversation history.

        Args:
            session_id: The session to update.
            history: New conversation history.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.history = list(history)

    async def remove_session(self, session_id: str) -> None:
        """Remove a session.

        Args:
            session_id: The session to remove.
        """
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def cleanup_expired(self) -> int:
        """Remove all expired sessions.

        Returns:
            Number of sessions removed.
        """
        async with self._lock:
            return await self._cleanup_expired_locked()

    async def _cleanup_expired_locked(self) -> int:
        """Internal cleanup (must hold lock).

        Returns:
            Number of sessions removed.
        """
        expired = [
            sid
            for sid, session in self._sessions.items()
            if session.is_expired(self._timeout_seconds)
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    @property
    def active_count(self) -> int:
        """Number of active sessions."""
        return len(self._sessions)
