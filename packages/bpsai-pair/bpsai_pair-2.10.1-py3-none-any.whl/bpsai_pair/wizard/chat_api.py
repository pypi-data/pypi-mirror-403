"""Chat SSE streaming API for the guided setup wizard.

This module provides:
- POST /api/chat — SSE stream of Claude responses token-by-token
- POST /api/chat/cancel — Cancel in-progress generation
- Conversation history stored in session state
- Rate limiting to prevent abuse
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from bpsai_pair.wizard.prompts import load_system_prompt
from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import get_session, update_session

# Rate limiting: max requests per session within the window
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW_SECS = 60
_rate_limit_tracker: dict[str, list[float]] = defaultdict(list)

# Active cancellation flags per session
_cancel_flags: dict[str, bool] = {}


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    message: str


def _get_anthropic_client():
    """Get an Anthropic client, using SDK's default authentication.

    The SDK will automatically find credentials from:
    1. ANTHROPIC_API_KEY environment variable
    2. Other configured auth sources

    Returns:
        AsyncAnthropic client or None if no credentials available.
    """
    import anthropic

    try:
        # Let SDK find credentials automatically
        client = anthropic.AsyncAnthropic()
        # Verify we have credentials by checking api_key is set
        if client.api_key:
            return client
    except anthropic.AuthenticationError:
        pass
    except Exception:
        pass

    return None


def _check_rate_limit(session_id: str) -> bool:
    """Check if a session has exceeded the rate limit.

    Returns True if the request is allowed, False if rate limited.
    """
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW_SECS

    # Prune old entries
    _rate_limit_tracker[session_id] = [
        t for t in _rate_limit_tracker[session_id] if t > window_start
    ]

    if not _rate_limit_tracker[session_id]:
        del _rate_limit_tracker[session_id]
        _rate_limit_tracker[session_id] = []

    if len(_rate_limit_tracker[session_id]) >= _RATE_LIMIT_MAX:
        return False

    _rate_limit_tracker[session_id].append(now)
    return True


async def _stream_claude_response(
    messages: list[dict[str, str]],
    client,
    session_id: str,
    *,
    system: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream a Claude response token-by-token.

    Args:
        messages: Full conversation messages including the latest user message.
        client: Anthropic AsyncAnthropic client.
        session_id: Session ID for cancellation tracking.
        system: Optional system prompt for guiding the conversation.

    Yields:
        Individual text tokens from the response.
    """
    kwargs: dict = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2048,
        "messages": messages,
        "temperature": 0.7,  # Balanced creativity and consistency
    }
    if system:
        kwargs["system"] = system

    async with client.messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            if _cancel_flags.pop(session_id, False):
                return
            yield text


def _get_session_or_error(
    request: Request,
) -> tuple[str, object | None, JSONResponse | None]:
    """Extract session from request cookies.

    Returns:
        (session_id, session, error_response) — error_response is None on success.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return "", None, JSONResponse(
            status_code=400,
            content={"success": False, "error": "No session"},
        )

    session = get_session(session_id)
    if not session:
        return "", None, JSONResponse(
            status_code=400,
            content={"success": False, "error": "Session not found"},
        )

    return session_id, session, None


def _validate_chat_request(
    request: Request,
    chat_request: ChatRequest,
) -> tuple[str, object, str, None] | tuple[None, None, None, JSONResponse]:
    """Validate a chat request and return session context or error.

    Returns:
        (session_id, session, message, None) on success, or
        (None, None, None, error_response) on failure.
    """
    session_id, session, error = _get_session_or_error(request)
    if error:
        return None, None, None, error

    message = chat_request.message.strip()
    if not message:
        return None, None, None, JSONResponse(
            status_code=400,
            content={"success": False, "error": "Message cannot be empty"},
        )

    if not _check_rate_limit(session_id):
        return None, None, None, JSONResponse(
            status_code=429,
            content={"success": False, "error": "Too many requests"},
        )

    return session_id, session, message, None


async def _generate_sse_events(
    history: list[dict[str, str]],
    chat_data: dict,
    client,
    session_id: str,
    *,
    system: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Generate SSE events by streaming a Claude response.

    Yields token, done, or error events. Stores the assistant
    response (or partial response on error) in session history.
    ``history`` must already include the latest user message.

    Token data is JSON-encoded to preserve special characters like < and >.
    """
    import json

    collected_tokens: list[str] = []
    try:
        async for token in _stream_claude_response(
            history, client, session_id, system=system,
        ):
            collected_tokens.append(token)
            # JSON-encode the token to preserve < > and other special chars
            yield {"event": "token", "data": json.dumps(token)}

        full_response = "".join(collected_tokens)
        history.append({"role": "assistant", "content": full_response})
        chat_data["history"] = history
        update_session(session_id, data={"chat": chat_data})

        yield {"event": "done", "data": "complete"}

    except Exception as exc:
        if collected_tokens:
            partial = "".join(collected_tokens)
            history.append({"role": "assistant", "content": partial})
            chat_data["history"] = history
            update_session(session_id, data={"chat": chat_data})

        yield {"event": "error", "data": str(exc)}


async def _handle_chat_stream(
    request: Request,
    chat_request: ChatRequest,
) -> EventSourceResponse | JSONResponse:
    """Handle a chat message and return an SSE stream."""
    session_id, session, message, error = _validate_chat_request(
        request, chat_request,
    )
    if error:
        return error

    client = _get_anthropic_client()
    if client is None:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Guided Setup requires an API key. Please set ANTHROPIC_API_KEY and restart the wizard, or use Quick Setup instead.",
            },
        )

    chat_data = session.data.get("chat", {})
    history: list[dict[str, str]] = chat_data.get("history", [])

    history.append({"role": "user", "content": message})
    chat_data["history"] = history
    update_session(session_id, data={"chat": chat_data})

    system_prompt = load_system_prompt(tier=session.tier)

    return EventSourceResponse(
        _generate_sse_events(
            history, chat_data, client, session_id, system=system_prompt,
        )
    )


async def _handle_cancel(request: Request) -> JSONResponse:
    """Handle chat cancellation."""
    session_id, _session, error = _get_session_or_error(request)
    if error:
        return error

    _cancel_flags[session_id] = True
    return JSONResponse(content={"status": "cancelled"})


def setup_chat_api_routes(app: FastAPI) -> None:
    """Set up chat API routes."""

    @app.post("/api/chat", response_model=None)
    async def chat_stream(
        request: Request, chat_request: ChatRequest,
    ) -> EventSourceResponse | JSONResponse:
        return await _handle_chat_stream(request, chat_request)

    @app.post("/api/chat/cancel")
    async def cancel_chat(request: Request) -> JSONResponse:
        return await _handle_cancel(request)
