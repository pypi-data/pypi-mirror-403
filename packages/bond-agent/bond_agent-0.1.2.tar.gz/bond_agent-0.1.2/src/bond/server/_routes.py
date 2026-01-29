"""Route handlers for Bond server.

SSE, WebSocket, and REST endpoints for agent streaming.
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from bond.server._session import SessionManager, SessionStatus
from bond.server._types import (
    AskRequest,
    HealthResponse,
    ServerConfig,
    SessionResponse,
)
from bond.utils import create_websocket_handlers

if TYPE_CHECKING:
    from bond.agent import BondAgent


class BondRoutes:
    """Route handlers for Bond server.

    Creates route handlers that stream agent responses via SSE and WebSocket.
    """

    def __init__(
        self,
        agent: BondAgent[Any, Any],
        session_manager: SessionManager,
        config: ServerConfig,
    ) -> None:
        """Initialize routes.

        Args:
            agent: The BondAgent to run.
            session_manager: Session manager instance.
            config: Server configuration.
        """
        self.agent = agent
        self.session_manager = session_manager
        self.config = config

    async def health(self, _request: Request) -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON with service status and agent name.
        """
        response = HealthResponse(
            status="healthy",
            agent_name=self.agent.name,
        )
        return JSONResponse(response.model_dump())

    async def ask(self, request: Request) -> JSONResponse:
        """Start a new streaming session.

        Accepts POST with prompt, creates session, returns session_id.
        Client then connects to /stream/{session_id} for SSE.

        Args:
            request: Starlette request with JSON body.

        Returns:
            JSON with session_id and stream_url.
        """
        try:
            body = await request.json()
            ask_request = AskRequest.model_validate(body)
        except Exception as e:
            return JSONResponse(
                {"error": f"Invalid request: {e}"},
                status_code=400,
            )

        try:
            # Get existing history if continuing session
            history = None
            if ask_request.session_id:
                existing = await self.session_manager.get_session(ask_request.session_id)
                if existing:
                    history = existing.history

            session = await self.session_manager.create_session(
                prompt=ask_request.prompt,
                history=history,
                session_id=ask_request.session_id,
            )
        except ValueError as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=503,
            )

        response = SessionResponse(
            session_id=session.session_id,
            stream_url=self.config.get_stream_url(session.session_id),
        )
        return JSONResponse(response.model_dump())

    async def stream(self, request: Request) -> Response:
        """SSE streaming endpoint.

        Connects to a session and streams agent response events.

        Args:
            request: Starlette request with session_id path param.

        Returns:
            SSE event stream.
        """
        from sse_starlette.sse import EventSourceResponse

        session_id = request.path_params["session_id"]
        session = await self.session_manager.get_session(session_id)

        if not session:
            return JSONResponse(
                {"error": "Session not found or expired"},
                status_code=404,
            )

        async def event_generator() -> Any:
            """Generate SSE events from agent streaming."""
            try:
                await self.session_manager.update_status(session_id, SessionStatus.STREAMING)

                # Set up agent history
                self.agent.set_message_history(session.history)

                # Create synchronous handlers that put directly to queue
                # This avoids race conditions with async task scheduling
                from bond.agent import StreamHandlers

                handlers = StreamHandlers(
                    on_block_start=lambda kind, idx: session.result_queue.put_nowait(
                        {"event": "block_start", "data": {"kind": kind, "idx": idx}}
                    ),
                    on_block_end=lambda kind, idx: session.result_queue.put_nowait(
                        {"event": "block_end", "data": {"kind": kind, "idx": idx}}
                    ),
                    on_text_delta=lambda txt: session.result_queue.put_nowait(
                        {"event": "text", "data": {"content": txt}}
                    ),
                    on_thinking_delta=lambda txt: session.result_queue.put_nowait(
                        {"event": "thinking", "data": {"content": txt}}
                    ),
                    on_tool_call_delta=lambda n, a: session.result_queue.put_nowait(
                        {"event": "tool_delta", "data": {"name": n, "args": a}}
                    ),
                    on_tool_execute=lambda i, n, a: session.result_queue.put_nowait(
                        {"event": "tool_exec", "data": {"id": i, "name": n, "args": a}}
                    ),
                    on_tool_result=lambda i, n, r: session.result_queue.put_nowait(
                        {"event": "tool_result", "data": {"id": i, "name": n, "result": r}}
                    ),
                    on_complete=lambda data: session.result_queue.put_nowait(
                        {"event": "complete", "data": {"data": data}}
                    ),
                )

                # Start agent task
                agent_task = asyncio.create_task(
                    self._run_agent(session_id, session.prompt, handlers)
                )

                # Yield events from queue
                while True:
                    try:
                        # Wait for event with timeout
                        event_data = await asyncio.wait_for(
                            session.result_queue.get(),
                            timeout=1.0,
                        )

                        if event_data.get("event") == "_done":
                            # Agent completed
                            break

                        yield {
                            "event": event_data["event"],
                            "data": json.dumps(event_data["data"]),
                        }

                    except TimeoutError:
                        # Check if agent task failed
                        if agent_task.done():
                            exc = agent_task.exception()
                            if exc:
                                yield {
                                    "event": "error",
                                    "data": json.dumps({"error": str(exc)}),
                                }
                            break

            except Exception as e:
                await self.session_manager.update_status(session_id, SessionStatus.ERROR, str(e))
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                }

        return EventSourceResponse(event_generator())

    async def _run_agent(
        self,
        session_id: str,
        prompt: str,
        handlers: Any,
    ) -> None:
        """Run agent and signal completion.

        Args:
            session_id: Session to update.
            prompt: User prompt.
            handlers: StreamHandlers for streaming.
        """
        session = await self.session_manager.get_session(session_id)
        if not session:
            return

        try:
            await self.agent.ask(prompt, handlers=handlers)

            # Update history after completion
            await self.session_manager.update_history(
                session_id,
                self.agent.get_message_history(),
            )
            await self.session_manager.update_status(session_id, SessionStatus.COMPLETED)

        except Exception as e:
            await self.session_manager.update_status(session_id, SessionStatus.ERROR, str(e))
            raise
        finally:
            # Signal completion to event generator
            await session.result_queue.put({"event": "_done", "data": {}})

    async def websocket_handler(self, websocket: WebSocket) -> None:
        """WebSocket endpoint for bidirectional streaming.

        Protocol:
            1. Client connects
            2. Client sends {"prompt": "..."} messages
            3. Server streams response events
            4. Repeat or close

        Args:
            websocket: Starlette WebSocket connection.
        """
        await websocket.accept()

        try:
            while True:
                # Wait for prompt from client
                data = await websocket.receive_json()
                prompt = data.get("prompt")

                if not prompt:
                    await websocket.send_json({"error": "Missing 'prompt' field"})
                    continue

                # Set history if provided
                history = data.get("history")
                if history:
                    self.agent.set_message_history(history)

                # Create WebSocket handlers
                handlers = create_websocket_handlers(websocket.send_json)

                try:
                    # Run agent with streaming
                    await self.agent.ask(prompt, handlers=handlers)

                    # Send completion marker
                    await websocket.send_json({"t": "done"})

                except Exception as e:
                    await websocket.send_json({"t": "error", "error": str(e)})

        except WebSocketDisconnect:
            pass
        except Exception:
            await websocket.close()

    def get_routes(self) -> list[Route | WebSocketRoute]:
        """Get all route definitions.

        Returns:
            List of Starlette routes.
        """
        return [
            Route("/health", self.health, methods=["GET"]),
            Route("/ask", self.ask, methods=["POST"]),
            Route("/stream/{session_id}", self.stream, methods=["GET"]),
            WebSocketRoute("/ws", self.websocket_handler),
        ]
