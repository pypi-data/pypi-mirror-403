"""Tests for server session management."""

from __future__ import annotations

import asyncio
import time

import pytest

from bond.server._session import Session, SessionManager, SessionStatus


class TestSession:
    """Tests for Session dataclass."""

    def test_session_creation(self) -> None:
        """Test session is created with correct defaults."""
        session = Session(session_id="test-123", prompt="Hello")

        assert session.session_id == "test-123"
        assert session.prompt == "Hello"
        assert session.status == SessionStatus.PENDING
        assert session.history == []
        assert session.error is None

    def test_session_is_expired(self) -> None:
        """Test session expiry detection."""
        session = Session(session_id="test", prompt="test")
        session.created_at = time.time() - 100  # 100 seconds ago

        assert session.is_expired(50) is True  # 50 second timeout
        assert session.is_expired(200) is False  # 200 second timeout


class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        """Test creating a new session."""
        manager = SessionManager(timeout_seconds=3600)

        session = await manager.create_session("What is 2+2?")

        assert session.prompt == "What is 2+2?"
        assert session.status == SessionStatus.PENDING
        assert session.session_id is not None
        assert manager.active_count == 1

    @pytest.mark.asyncio
    async def test_create_session_with_custom_id(self) -> None:
        """Test creating session with custom ID."""
        manager = SessionManager()

        session = await manager.create_session("test", session_id="custom-id-123")

        assert session.session_id == "custom-id-123"

    @pytest.mark.asyncio
    async def test_get_session(self) -> None:
        """Test retrieving a session."""
        manager = SessionManager()
        created = await manager.create_session("Hello")

        retrieved = await manager.get_session(created.session_id)

        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.prompt == "Hello"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self) -> None:
        """Test retrieving non-existent session returns None."""
        manager = SessionManager()

        result = await manager.get_session("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_expired_session_returns_none(self) -> None:
        """Test expired session is removed and returns None."""
        manager = SessionManager(timeout_seconds=1)
        session = await manager.create_session("test")

        # Manually expire the session
        session.created_at = time.time() - 10

        result = await manager.get_session(session.session_id)

        assert result is None
        assert manager.active_count == 0

    @pytest.mark.asyncio
    async def test_update_status(self) -> None:
        """Test updating session status."""
        manager = SessionManager()
        session = await manager.create_session("test")

        await manager.update_status(session.session_id, SessionStatus.STREAMING)

        updated = await manager.get_session(session.session_id)
        assert updated is not None
        assert updated.status == SessionStatus.STREAMING

    @pytest.mark.asyncio
    async def test_update_status_with_error(self) -> None:
        """Test updating session status with error message."""
        manager = SessionManager()
        session = await manager.create_session("test")

        await manager.update_status(session.session_id, SessionStatus.ERROR, "Something went wrong")

        updated = await manager.get_session(session.session_id)
        assert updated is not None
        assert updated.status == SessionStatus.ERROR
        assert updated.error == "Something went wrong"

    @pytest.mark.asyncio
    async def test_update_history(self) -> None:
        """Test updating session history."""
        manager = SessionManager()
        session = await manager.create_session("test")

        # Mock message history (simplified)
        new_history = [{"role": "user", "content": "test"}]  # type: ignore[list-item]
        await manager.update_history(session.session_id, new_history)  # type: ignore[arg-type]

        updated = await manager.get_session(session.session_id)
        assert updated is not None
        assert len(updated.history) == 1

    @pytest.mark.asyncio
    async def test_remove_session(self) -> None:
        """Test removing a session."""
        manager = SessionManager()
        session = await manager.create_session("test")
        assert manager.active_count == 1

        await manager.remove_session(session.session_id)

        assert manager.active_count == 0
        assert await manager.get_session(session.session_id) is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self) -> None:
        """Test cleaning up expired sessions."""
        manager = SessionManager(timeout_seconds=1)
        session1 = await manager.create_session("test1")
        session2 = await manager.create_session("test2")

        # Expire only session1
        session1.created_at = time.time() - 10

        removed = await manager.cleanup_expired()

        assert removed == 1
        assert manager.active_count == 1
        assert await manager.get_session(session2.session_id) is not None

    @pytest.mark.asyncio
    async def test_max_sessions_limit(self) -> None:
        """Test max concurrent sessions limit."""
        manager = SessionManager(max_sessions=2)
        await manager.create_session("test1")
        await manager.create_session("test2")

        with pytest.raises(ValueError, match="Maximum concurrent sessions"):
            await manager.create_session("test3")

    @pytest.mark.asyncio
    async def test_reuse_session_id(self) -> None:
        """Test continuing an existing session with same ID."""
        manager = SessionManager()
        session1 = await manager.create_session("first prompt", session_id="shared-id")
        original_time = session1.created_at

        # Small delay to ensure different timestamp
        await asyncio.sleep(0.01)

        # Continue with same session_id
        session2 = await manager.create_session("second prompt", session_id="shared-id")

        assert session2.session_id == "shared-id"
        assert session2.prompt == "second prompt"
        assert session2.status == SessionStatus.PENDING
        assert session2.created_at > original_time
        assert manager.active_count == 1


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    def test_status_values(self) -> None:
        """Test all expected status values exist."""
        assert SessionStatus.PENDING.value == "pending"
        assert SessionStatus.STREAMING.value == "streaming"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.ERROR.value == "error"
        assert SessionStatus.EXPIRED.value == "expired"
