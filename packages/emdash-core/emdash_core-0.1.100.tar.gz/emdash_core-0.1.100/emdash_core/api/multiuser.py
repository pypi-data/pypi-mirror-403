"""API endpoints for multiuser shared sessions.

This module provides REST and SSE endpoints for creating, joining,
and managing shared agent sessions with multiple participants.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..multiuser import (
    SharedSessionManager,
    get_or_init_manager,
    SharedSession,
    SharedSessionState,
    Participant,
    ParticipantRole,
    SessionNotFoundError,
    InvalidInviteCodeError,
    NotAuthorizedError,
    UserIdentity,
    Team,
    TeamMember,
    TeamRole,
    TeamSessionInfo,
    TeamNotFoundError,
    TeamPermissionError,
)
from ..sse.stream import SSEHandler, EventType
from ..utils.logger import log

router = APIRouter(prefix="/multiuser", tags=["multiuser"])


# ─────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    """Request to create a new shared session."""

    user_id: Optional[str] = Field(None, description="User ID (generated if not provided)")
    display_name: str = Field(..., description="Display name for the session owner")
    model: str = Field("", description="LLM model to use")
    plan_mode: bool = Field(False, description="Whether to run in plan mode")


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session_id: str
    invite_code: str
    owner_id: str
    created_at: str
    state: str
    participants: list[dict]


class JoinSessionRequest(BaseModel):
    """Request to join a session via invite code."""

    invite_code: str = Field(..., description="The invite code")
    user_id: Optional[str] = Field(None, description="User ID (generated if not provided)")
    display_name: str = Field(..., description="Display name for the joining user")


class JoinSessionResponse(BaseModel):
    """Response after joining a session."""

    session_id: str
    invite_code: str
    state: str
    participants: list[dict]
    message_count: int
    queue_length: int


class SendMessageRequest(BaseModel):
    """Request to send a message in a shared session."""

    user_id: str = Field(..., description="User sending the message")
    content: str = Field(..., description="Message content")
    images: Optional[list[dict]] = Field(None, description="Optional images")
    priority: int = Field(0, description="Message priority (higher = more urgent)")
    trigger_agent: bool = Field(True, description="Whether to trigger agent processing (False for chat-only)")


class SendMessageResponse(BaseModel):
    """Response after sending/queueing a message."""

    message_id: str
    queued_at: str
    queue_position: Optional[int]
    agent_busy: bool


class LeaveSessionRequest(BaseModel):
    """Request to leave a session."""

    user_id: str = Field(..., description="User leaving the session")


class CloseSessionRequest(BaseModel):
    """Request to close a session (owner only)."""

    user_id: str = Field(..., description="User requesting close (must be owner)")


class SessionStateResponse(BaseModel):
    """Response with session state."""

    session_id: str
    invite_code: str
    owner_id: str
    state: str
    participants: list[dict]
    queue_length: int
    agent_busy: bool
    message_count: int


class ParticipantResponse(BaseModel):
    """Response with participant info."""

    user_id: str
    display_name: str
    role: str
    joined_at: str
    last_seen: str
    is_online: bool


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────


@router.post("/session/create", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new shared session.

    Returns the session info including an invite code that can be
    shared with other users to join the session.
    """
    manager = await get_or_init_manager()

    # Generate user ID if not provided
    user_id = request.user_id
    if not user_id:
        identity = UserIdentity.from_machine()
        user_id = identity.user_id

    try:
        session, invite_code = await manager.create_session(
            owner_id=user_id,
            display_name=request.display_name,
            model=request.model,
            plan_mode=request.plan_mode,
        )

        return CreateSessionResponse(
            session_id=session.session_id,
            invite_code=invite_code,
            owner_id=session.owner_id,
            created_at=session.created_at,
            state=session.state.value,
            participants=[p.to_dict() for p in session.participants],
        )

    except Exception as e:
        log.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/join", response_model=JoinSessionResponse)
async def join_session(request: JoinSessionRequest):
    """Join an existing session via invite code.

    The invite code is case-insensitive and ignores spaces/dashes.
    """
    manager = await get_or_init_manager()

    # Generate user ID if not provided
    user_id = request.user_id
    if not user_id:
        identity = UserIdentity.from_machine()
        user_id = identity.user_id

    try:
        session = await manager.join_session(
            invite_code=request.invite_code,
            user_id=user_id,
            display_name=request.display_name,
        )

        queue_status = manager.get_queue_status(session.session_id)

        return JoinSessionResponse(
            session_id=session.session_id,
            invite_code=session.invite_code,
            state=session.state.value,
            participants=[p.to_dict() for p in session.participants],
            message_count=len(session.messages),
            queue_length=queue_status.get("length", 0),
        )

    except InvalidInviteCodeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error(f"Failed to join session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/message", response_model=SendMessageResponse)
async def send_message(session_id: str, request: SendMessageRequest):
    """Send a message in a shared session.

    If trigger_agent is True and the agent is busy processing another message,
    this message will be queued and processed in order.
    If trigger_agent is False, the message is only broadcast to participants (chat-only).
    """
    manager = await get_or_init_manager()

    try:
        # Get session first to get participant info
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Broadcast the user message immediately so all participants see it right away
        participant = session.get_participant(request.user_id)
        display_name = participant.display_name if participant else "User"
        await manager.broadcast_event(
            session_id,
            "user_message",
            {
                "user_id": request.user_id,
                "content": request.content,
                "display_name": display_name,
            },
            source_user_id=request.user_id,
        )

        # If trigger_agent is False, just return without queueing for agent
        if not request.trigger_agent:
            from datetime import datetime
            return SendMessageResponse(
                message_id=f"chat-{datetime.utcnow().isoformat()}",
                queued_at=datetime.utcnow().isoformat(),
                queue_position=None,
                agent_busy=False,
            )

        # Queue for agent processing
        message = await manager.send_message(
            session_id=session_id,
            user_id=request.user_id,
            content=request.content,
            images=request.images,
            priority=request.priority,
        )

        queue_status = manager.get_queue_status(session_id)

        return SendMessageResponse(
            message_id=message.id,
            queued_at=message.queued_at,
            queue_position=queue_status.get("length", 1) - 1 if queue_status.get("agent_busy") else None,
            agent_busy=queue_status.get("agent_busy", False),
        )

    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAuthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        log.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """Get current state of a shared session."""
    manager = await get_or_init_manager()

    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    queue_status = manager.get_queue_status(session_id)

    return SessionStateResponse(
        session_id=session.session_id,
        invite_code=session.invite_code,
        owner_id=session.owner_id,
        state=session.state.value,
        participants=[p.to_dict() for p in session.participants],
        queue_length=queue_status.get("length", 0),
        agent_busy=queue_status.get("agent_busy", False),
        message_count=len(session.messages),
    )


@router.get("/session/{session_id}/participants")
async def get_participants(session_id: str) -> list[ParticipantResponse]:
    """Get list of participants in a session."""
    manager = await get_or_init_manager()

    participants = manager.get_session_participants(session_id)
    if not participants:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return [
        ParticipantResponse(
            user_id=p.user_id,
            display_name=p.display_name,
            role=p.role.value,
            joined_at=p.joined_at,
            last_seen=p.last_seen,
            is_online=p.is_online,
        )
        for p in participants
    ]


@router.post("/session/{session_id}/leave")
async def leave_session(session_id: str, request: LeaveSessionRequest):
    """Leave a shared session."""
    manager = await get_or_init_manager()

    try:
        success = await manager.leave_session(session_id, request.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session or user not found")

        return {"success": True, "message": f"Left session {session_id}"}

    except Exception as e:
        log.error(f"Failed to leave session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def close_session(session_id: str, request: CloseSessionRequest):
    """Close a shared session (owner only).

    This removes all participants and cleans up session resources.
    """
    manager = await get_or_init_manager()

    try:
        success = await manager.close_session(session_id, request.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": f"Closed session {session_id}"}

    except NotAuthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        log.error(f"Failed to close session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/heartbeat")
async def heartbeat(session_id: str, user_id: str = Query(...)):
    """Send a heartbeat to indicate the user is still connected.

    Should be called periodically (e.g., every 30 seconds) to maintain
    online presence status.
    """
    manager = await get_or_init_manager()

    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.update_participant_presence(user_id, is_online=True)

    return {"success": True}


@router.get("/session/{session_id}/stream")
async def stream_session(
    session_id: str,
    user_id: str = Query(..., description="User ID for this connection"),
):
    """Stream session events via Server-Sent Events (SSE).

    This endpoint provides real-time updates for:
    - Agent responses and tool calls
    - Participant joins/leaves
    - Queue status changes
    - State changes

    The stream should be kept open for the duration of the session.
    """
    manager = await get_or_init_manager()

    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify user is a participant
    if not session.get_participant(user_id):
        raise HTTPException(status_code=403, detail="User is not a participant")

    # Create SSE handler for this user
    sse_handler = SSEHandler(agent_name="Emdash Multiuser")

    # Register with manager (async to ensure broadcaster is set up)
    await manager.add_sse_handler_async(session_id, user_id, sse_handler)

    # Send initial state
    sse_handler.emit(EventType.SESSION_START, {
        "session_id": session_id,
        "participants": [p.to_dict() for p in session.participants],
        "message_count": len(session.messages),
        "state": session.state.value,
    })

    async def event_generator():
        """Generate SSE events."""
        try:
            async for event in sse_handler:
                yield event
        finally:
            # Cleanup on disconnect
            manager.remove_sse_handler(session_id, user_id)
            log.info(f"SSE stream closed for user {user_id} in session {session_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/session/{session_id}/messages")
async def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get conversation messages from a session.

    Returns messages in chronological order, most recent last.
    """
    manager = await get_or_init_manager()

    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session.messages[offset : offset + limit]

    return {
        "session_id": session_id,
        "total": len(session.messages),
        "offset": offset,
        "limit": limit,
        "messages": messages,
    }


class ConversationMessageRequest(BaseModel):
    """Request to send a message via the unified conversation endpoint."""

    user_id: str = Field(..., description="User sending the message")
    content: str = Field(..., description="Message content")
    trigger_agent: bool = Field(False, description="Whether this message should trigger agent processing")


@router.post("/conversation/{session_id}/message")
async def conversation_message(session_id: str, request: ConversationMessageRequest):
    """Unified message endpoint for shared sessions.

    This is the single source of truth for message handling in shared mode:
    - ALL participants (including owner) receive events via SSE only
    - No local display, no filtering needed

    Flow:
    1. Broadcasts user_message to all participants via SSE
    2. If trigger_agent:
       - If owner sent the message: returns signal for owner to process locally
       - If joiner sent the message: sends process_message_request to owner via SSE
    """
    import re

    manager = await get_or_init_manager()

    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify user is a participant
    participant = session.get_participant(request.user_id)
    if not participant:
        raise HTTPException(status_code=403, detail="User is not a participant")

    display_name = participant.display_name

    log.info(f"[CONVERSATION] Broadcasting user_message: user_id={request.user_id}, display_name={display_name}, content={request.content[:50]}...")

    # 1. Broadcast user message to all participants
    await manager.broadcast_event(
        session_id,
        "user_message",
        {
            "user_id": request.user_id,
            "content": request.content,
            "display_name": display_name,
        },
        source_user_id=request.user_id,
    )

    # 2. Handle agent triggering
    if request.trigger_agent:
        is_owner = session.owner_id == request.user_id

        # Strip @agent/@emdash from content for agent processing
        agent_content = re.sub(r'@agent|@emdash', '', request.content, flags=re.IGNORECASE).strip()
        if not agent_content:
            agent_content = request.content

        if is_owner:
            # Owner will process locally - return signal
            return {
                "status": "process_locally",
                "content": agent_content,
                "message": "Owner should process this message through their local agent",
            }
        else:
            # Non-owner: send process_message_request to owner via SSE
            await manager.broadcast_event(
                session_id,
                "process_message_request",
                {
                    "user_id": request.user_id,
                    "content": agent_content,
                    "display_name": display_name,
                },
                source_user_id=request.user_id,
            )
            return {
                "status": "queued",
                "message": "Message sent to session owner for processing",
            }

    # Chat-only message (no agent trigger)
    return {
        "status": "broadcast",
        "message": "Message broadcast to all participants",
    }


class BroadcastResponseRequest(BaseModel):
    """Request to broadcast an agent response to all participants."""

    user_id: str = Field(..., description="Owner's user ID (must be session owner)")
    original_message_id: Optional[str] = Field(None, description="ID of the message being responded to")
    original_user_id: Optional[str] = Field(None, description="User ID who sent the original message")
    original_content: str = Field(..., description="Original message content")
    response_content: str = Field(..., description="Agent's response content")


class BroadcastEventRequest(BaseModel):
    """Request to broadcast a generic event to all participants."""

    user_id: str = Field(..., description="User sending the event")
    event_type: str = Field(..., description="Event type (e.g., user_typing, tool_start)")
    data: dict = Field(default_factory=dict, description="Event data payload")


@router.post("/session/{session_id}/broadcast_response")
async def broadcast_response(session_id: str, request: BroadcastResponseRequest):
    """Broadcast an agent response to all participants in a shared session.

    This endpoint is used by the session owner's CLI to broadcast responses
    after processing messages locally. The owner processes messages with their
    local agent and uses this endpoint to relay responses to all participants.
    """
    manager = await get_or_init_manager()

    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify caller is the owner
    if session.owner_id != request.user_id:
        raise HTTPException(status_code=403, detail="Only session owner can broadcast responses")

    try:
        # Determine who sent the original message
        msg_user_id = request.original_user_id or request.user_id

        # Only broadcast user_message for owner's messages here.
        # Joiner messages are already broadcast immediately via /message endpoint.
        is_owner_message = (request.original_user_id is None or
                           request.original_user_id == request.user_id)

        if is_owner_message:
            participant = session.get_participant(msg_user_id)
            display_name = participant.display_name if participant else "User"
            await manager.broadcast_event(
                session_id,
                "user_message",
                {
                    "user_id": msg_user_id,
                    "content": request.original_content,
                    "display_name": display_name,
                },
                source_user_id=msg_user_id,
            )

        # Broadcast the agent response (no source user - it's from the agent)
        await manager.broadcast_event(
            session_id,
            "assistant_text",
            {
                "text": request.response_content,
                "complete": True,
            },
        )

        # Update session messages
        session.messages.append({"role": "user", "content": request.original_content})
        session.messages.append({"role": "assistant", "content": request.response_content})

        return {"success": True, "message": "Response broadcast to all participants"}

    except Exception as e:
        log.error(f"Failed to broadcast response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/broadcast_event")
async def broadcast_event(session_id: str, request: BroadcastEventRequest):
    """Broadcast a generic event to all participants in a shared session.

    Used for typing indicators, tool events, thinking, etc.
    """
    manager = await get_or_init_manager()

    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify user is a participant
    if not session.get_participant(request.user_id):
        raise HTTPException(status_code=403, detail="User is not a participant")

    try:
        # Add user info to event data
        participant = session.get_participant(request.user_id)
        event_data = {
            **request.data,
            "user_id": request.user_id,
            "display_name": participant.display_name if participant else "User",
        }

        await manager.broadcast_event(
            session_id,
            request.event_type,
            event_data,
            source_user_id=request.user_id,  # Pass source user for filtering
        )

        return {"success": True}

    except Exception as e:
        log.error(f"Failed to broadcast event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/by-invite/{invite_code}")
async def get_session_by_invite(invite_code: str):
    """Look up session info by invite code (without joining).

    Useful for previewing a session before joining.
    """
    manager = await get_or_init_manager()

    session = manager.get_session_by_invite(invite_code)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    return {
        "session_id": session.session_id,
        "owner_id": session.owner_id,
        "created_at": session.created_at,
        "state": session.state.value,
        "participant_count": len(session.participants),
        "message_count": len(session.messages),
    }


@router.get("/sessions")
async def list_user_sessions(user_id: str = Query(...)):
    """List all sessions a user is participating in."""
    manager = await get_or_init_manager()

    sessions = manager.get_user_sessions(user_id)

    return {
        "user_id": user_id,
        "sessions": [
            {
                "session_id": s.session_id,
                "invite_code": s.invite_code,
                "owner_id": s.owner_id,
                "state": s.state.value,
                "participant_count": len(s.participants),
                "created_at": s.created_at,
                "is_owner": s.owner_id == user_id,
            }
            for s in sessions
        ],
    }


# ─────────────────────────────────────────────────────────────
# Team Request/Response Models
# ─────────────────────────────────────────────────────────────


class CreateTeamRequest(BaseModel):
    """Request to create a new team."""

    name: str = Field(..., description="Team name")
    user_id: str = Field(..., description="Creator's user ID")
    display_name: str = Field(..., description="Creator's display name")
    description: str = Field("", description="Optional team description")


class CreateTeamResponse(BaseModel):
    """Response after creating a team."""

    team_id: str
    name: str
    invite_code: str
    created_at: str
    member_count: int


class JoinTeamRequest(BaseModel):
    """Request to join a team."""

    invite_code: str = Field(..., description="Team invite code")
    user_id: str = Field(..., description="Joining user's ID")
    display_name: str = Field(..., description="Joining user's display name")


class JoinTeamResponse(BaseModel):
    """Response after joining a team."""

    team_id: str
    name: str
    member_count: int
    your_role: str


class LeaveTeamRequest(BaseModel):
    """Request to leave a team."""

    user_id: str = Field(..., description="User leaving the team")


class AddSessionToTeamRequest(BaseModel):
    """Request to add a session to a team."""

    session_id: str = Field(..., description="Session to add")
    user_id: str = Field(..., description="User adding the session")
    title: Optional[str] = Field(None, description="Optional title for the session")


class JoinTeamSessionRequest(BaseModel):
    """Request to join a team session."""

    session_id: str = Field(..., description="Session to join")
    user_id: str = Field(..., description="User joining")
    display_name: str = Field(..., description="User's display name")


# ─────────────────────────────────────────────────────────────
# Team Endpoints
# ─────────────────────────────────────────────────────────────


@router.post("/team/create", response_model=CreateTeamResponse)
async def create_team(request: CreateTeamRequest):
    """Create a new team.

    The creating user becomes an admin of the team.
    Returns an invite code that can be shared with others to join.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.create_team(
            name=request.name,
            user_id=request.user_id,
            display_name=request.display_name,
            description=request.description,
        )

        return CreateTeamResponse(
            team_id=team.team_id,
            name=team.name,
            invite_code=team.invite_code,
            created_at=team.created_at,
            member_count=len(team.members),
        )

    except Exception as e:
        log.error(f"Failed to create team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/join", response_model=JoinTeamResponse)
async def join_team(request: JoinTeamRequest):
    """Join a team using invite code.

    Team invite codes start with 'T-' prefix.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.join_team(
            invite_code=request.invite_code,
            user_id=request.user_id,
            display_name=request.display_name,
        )

        member = team.get_member(request.user_id)
        your_role = member.role.value if member else "member"

        return JoinTeamResponse(
            team_id=team.team_id,
            name=team.name,
            member_count=len(team.members),
            your_role=your_role,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error(f"Failed to join team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}")
async def get_team(team_id: str, user_id: str = Query(...)):
    """Get team information.

    Only team members can view team details.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Check membership
        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        member = team.get_member(user_id)
        your_role = member.role.value if member else "member"

        # Get session count
        team_sessions = await manager.list_team_sessions(team_id, user_id)

        return {
            "team_id": team.team_id,
            "name": team.name,
            "description": team.description,
            "invite_code": team.invite_code,
            "created_at": team.created_at,
            "created_by": team.created_by,
            "members": [m.to_dict() for m in team.members],
            "session_count": len(team_sessions),
            "your_role": your_role,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/leave")
async def leave_team(team_id: str, request: LeaveTeamRequest):
    """Leave a team."""
    manager = await get_or_init_manager()

    try:
        success = await manager.leave_team(team_id, request.user_id)
        if not success:
            raise HTTPException(status_code=400, detail="Could not leave team")

        return {"success": True}

    except Exception as e:
        log.error(f"Failed to leave team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams")
async def list_user_teams(user_id: str = Query(...)):
    """List all teams a user is a member of."""
    manager = await get_or_init_manager()

    try:
        teams = await manager.get_user_teams(user_id)

        return [
            {
                "team_id": t.team_id,
                "name": t.name,
                "invite_code": t.invite_code,
                "member_count": len(t.members),
                "your_role": t.get_member(user_id).role.value if t.get_member(user_id) else "member",
            }
            for t in teams
        ]

    except Exception as e:
        log.error(f"Failed to list teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}/sessions")
async def list_team_sessions(team_id: str, user_id: str = Query(...)):
    """List all sessions in a team.

    Only team members can view team sessions.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        sessions = await manager.list_team_sessions(team_id, user_id)

        return {
            "team_id": team_id,
            "team_name": team.name,
            "sessions": [s.to_dict() for s in sessions],
        }

    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        log.error(f"Failed to list team sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/add-session")
async def add_session_to_team(team_id: str, request: AddSessionToTeamRequest):
    """Add a session to a team.

    The user must be the session owner or a team admin.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        success = await manager.add_session_to_team(
            team_id=team_id,
            session_id=request.session_id,
            user_id=request.user_id,
            title=request.title,
        )

        return {
            "success": success,
            "team_name": team.name,
        }

    except TeamNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TeamPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        log.error(f"Failed to add session to team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/join-session")
async def join_team_session(team_id: str, request: JoinTeamSessionRequest):
    """Join a session as a team member.

    Team members can join any team session without needing an invite code.
    """
    manager = await get_or_init_manager()

    try:
        session = await manager.join_team_session(
            team_id=team_id,
            session_id=request.session_id,
            user_id=request.user_id,
            display_name=request.display_name,
        )

        return {
            "session_id": session.session_id,
            "title": session.title,
            "participants": [p.to_dict() for p in session.participants],
            "message_count": len(session.messages),
            "state": session.state.value,
        }

    except TeamNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TeamPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error(f"Failed to join team session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Registry Request/Response Models
# ─────────────────────────────────────────────────────────────


class AddRuleRequest(BaseModel):
    """Request to add a rule to team registry."""

    user_id: str = Field(..., description="User adding the rule (must be admin)")
    name: str = Field(..., description="Rule name")
    content: str = Field(..., description="Rule content (prompt text)")
    description: str = Field("", description="Optional description")
    priority: int = Field(0, description="Rule priority (higher = applied first)")
    tags: list[str] = Field(default_factory=list, description="Optional tags")


class AddAgentRequest(BaseModel):
    """Request to add an agent config to team registry."""

    user_id: str = Field(..., description="User adding the agent (must be admin)")
    name: str = Field(..., description="Agent name")
    description: str = Field("", description="Optional description")
    model: str = Field("", description="LLM model identifier")
    system_prompt: str = Field("", description="Custom system prompt")
    tools: list[str] = Field(default_factory=list, description="Enabled tool names")
    settings: dict = Field(default_factory=dict, description="Additional settings")


class AddMCPRequest(BaseModel):
    """Request to add an MCP config to team registry."""

    user_id: str = Field(..., description="User adding the MCP (must be admin)")
    name: str = Field(..., description="MCP name")
    description: str = Field("", description="Optional description")
    command: str = Field(..., description="Command to launch MCP server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict = Field(default_factory=dict, description="Environment variables")
    auto_start: bool = Field(False, description="Auto-start with sessions")


class AddSkillRequest(BaseModel):
    """Request to add a skill to team registry."""

    user_id: str = Field(..., description="User adding the skill (must be admin)")
    name: str = Field(..., description="Skill name")
    description: str = Field("", description="Optional description")
    prompt_template: str = Field(..., description="Prompt template with {{var}} placeholders")
    tags: list[str] = Field(default_factory=list, description="Optional tags")


class SyncRegistryRequest(BaseModel):
    """Request to sync registry."""

    user_id: str = Field(..., description="User requesting sync")
    strategy: str = Field("remote_wins", description="Conflict strategy: remote_wins, local_wins, merge")


class ImportRegistryRequest(BaseModel):
    """Request to import registry data."""

    user_id: str = Field(..., description="User importing (must be admin)")
    registry: dict = Field(..., description="Registry data to import")
    merge: bool = Field(True, description="Whether to merge with existing")


# ─────────────────────────────────────────────────────────────
# Registry Endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/team/{team_id}/registry")
async def get_team_registry(team_id: str, user_id: str = Query(...)):
    """Get the full team registry.

    Only team members can access the registry.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        return registry.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Rules Endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/team/{team_id}/registry/rules")
async def list_registry_rules(team_id: str, user_id: str = Query(...)):
    """List all rules in the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        return [r.to_dict() for r in registry.rules]

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to list rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}/registry/rules/{rule_name}")
async def get_registry_rule(team_id: str, rule_name: str, user_id: str = Query(...)):
    """Get a specific rule by name or ID."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        # Try by name first, then by ID
        rule = registry.get_rule_by_name(rule_name)
        if not rule:
            rule = registry.get_rule(rule_name)

        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")

        return rule.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/registry/rules")
async def add_registry_rule(team_id: str, request: AddRuleRequest):
    """Add a rule to the team registry.

    Only team admins can add rules.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(request.user_id):
            raise HTTPException(status_code=403, detail="Only admins can add rules")

        from ..multiuser.registry import Rule

        rule = Rule(
            rule_id="",  # Will be auto-generated
            name=request.name,
            content=request.content,
            description=request.description,
            priority=request.priority,
            tags=request.tags,
            created_by=request.user_id,
        )

        registry = await manager.get_team_registry(team_id, request.user_id)
        registry.add_rule(rule)
        await manager.save_team_registry(registry, request.user_id)

        return rule.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to add rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/team/{team_id}/registry/rules/{rule_id}")
async def remove_registry_rule(team_id: str, rule_id: str, user_id: str = Query(...)):
    """Remove a rule from the team registry.

    Only team admins can remove rules.
    """
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(user_id):
            raise HTTPException(status_code=403, detail="Only admins can remove rules")

        registry = await manager.get_team_registry(team_id, user_id)

        # Try to find and remove by name or ID
        rule = registry.get_rule_by_name(rule_id)
        target_id = rule.rule_id if rule else rule_id

        if not registry.remove_rule(target_id):
            raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")

        await manager.save_team_registry(registry, user_id)

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to remove rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Agents Endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/team/{team_id}/registry/agents")
async def list_registry_agents(team_id: str, user_id: str = Query(...)):
    """List all agent configs in the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        return [a.to_dict() for a in registry.agents]

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}/registry/agents/{agent_name}")
async def get_registry_agent(team_id: str, agent_name: str, user_id: str = Query(...)):
    """Get a specific agent config by name or ID."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        agent = registry.get_agent_by_name(agent_name)
        if not agent:
            agent = registry.get_agent(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        return agent.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/registry/agents")
async def add_registry_agent(team_id: str, request: AddAgentRequest):
    """Add an agent config to the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(request.user_id):
            raise HTTPException(status_code=403, detail="Only admins can add agents")

        from ..multiuser.registry import AgentConfig

        agent = AgentConfig(
            agent_id="",
            name=request.name,
            description=request.description,
            model=request.model,
            system_prompt=request.system_prompt,
            tools=request.tools,
            settings=request.settings,
            created_by=request.user_id,
        )

        registry = await manager.get_team_registry(team_id, request.user_id)
        registry.add_agent(agent)
        await manager.save_team_registry(registry, request.user_id)

        return agent.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to add agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/team/{team_id}/registry/agents/{agent_id}")
async def remove_registry_agent(team_id: str, agent_id: str, user_id: str = Query(...)):
    """Remove an agent config from the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(user_id):
            raise HTTPException(status_code=403, detail="Only admins can remove agents")

        registry = await manager.get_team_registry(team_id, user_id)

        agent = registry.get_agent_by_name(agent_id)
        target_id = agent.agent_id if agent else agent_id

        if not registry.remove_agent(target_id):
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        await manager.save_team_registry(registry, user_id)

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to remove agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# MCPs Endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/team/{team_id}/registry/mcps")
async def list_registry_mcps(team_id: str, user_id: str = Query(...)):
    """List all MCP configs in the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        return [m.to_dict() for m in registry.mcps]

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to list MCPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}/registry/mcps/{mcp_name}")
async def get_registry_mcp(team_id: str, mcp_name: str, user_id: str = Query(...)):
    """Get a specific MCP config by name or ID."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        mcp = registry.get_mcp_by_name(mcp_name)
        if not mcp:
            mcp = registry.get_mcp(mcp_name)

        if not mcp:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_name}' not found")

        return mcp.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get MCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/registry/mcps")
async def add_registry_mcp(team_id: str, request: AddMCPRequest):
    """Add an MCP config to the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(request.user_id):
            raise HTTPException(status_code=403, detail="Only admins can add MCPs")

        from ..multiuser.registry import MCPConfig

        mcp = MCPConfig(
            mcp_id="",
            name=request.name,
            description=request.description,
            command=request.command,
            args=request.args,
            env=request.env,
            auto_start=request.auto_start,
            created_by=request.user_id,
        )

        registry = await manager.get_team_registry(team_id, request.user_id)
        registry.add_mcp(mcp)
        await manager.save_team_registry(registry, request.user_id)

        return mcp.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to add MCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/team/{team_id}/registry/mcps/{mcp_id}")
async def remove_registry_mcp(team_id: str, mcp_id: str, user_id: str = Query(...)):
    """Remove an MCP config from the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(user_id):
            raise HTTPException(status_code=403, detail="Only admins can remove MCPs")

        registry = await manager.get_team_registry(team_id, user_id)

        mcp = registry.get_mcp_by_name(mcp_id)
        target_id = mcp.mcp_id if mcp else mcp_id

        if not registry.remove_mcp(target_id):
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_id}' not found")

        await manager.save_team_registry(registry, user_id)

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to remove MCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Skills Endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/team/{team_id}/registry/skills")
async def list_registry_skills(team_id: str, user_id: str = Query(...)):
    """List all skills in the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        return [s.to_dict() for s in registry.skills]

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to list skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}/registry/skills/{skill_name}")
async def get_registry_skill(team_id: str, skill_name: str, user_id: str = Query(...)):
    """Get a specific skill by name or ID."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.get_team_registry(team_id, user_id)

        skill = registry.get_skill_by_name(skill_name)
        if not skill:
            skill = registry.get_skill(skill_name)

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

        return skill.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/registry/skills")
async def add_registry_skill(team_id: str, request: AddSkillRequest):
    """Add a skill to the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(request.user_id):
            raise HTTPException(status_code=403, detail="Only admins can add skills")

        from ..multiuser.registry import Skill

        skill = Skill(
            skill_id="",
            name=request.name,
            description=request.description,
            prompt_template=request.prompt_template,
            tags=request.tags,
            created_by=request.user_id,
        )

        registry = await manager.get_team_registry(team_id, request.user_id)
        registry.add_skill(skill)
        await manager.save_team_registry(registry, request.user_id)

        return skill.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to add skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/team/{team_id}/registry/skills/{skill_id}")
async def remove_registry_skill(team_id: str, skill_id: str, user_id: str = Query(...)):
    """Remove a skill from the team registry."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(user_id):
            raise HTTPException(status_code=403, detail="Only admins can remove skills")

        registry = await manager.get_team_registry(team_id, user_id)

        skill = registry.get_skill_by_name(skill_id)
        target_id = skill.skill_id if skill else skill_id

        if not registry.remove_skill(target_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

        await manager.save_team_registry(registry, user_id)

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to remove skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Registry Sync/Import/Export
# ─────────────────────────────────────────────────────────────


@router.post("/team/{team_id}/registry/sync")
async def sync_team_registry(team_id: str, request: SyncRegistryRequest):
    """Sync team registry between local and remote storage."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_member(request.user_id):
            raise HTTPException(status_code=403, detail="Not a team member")

        registry = await manager.sync_team_registry(
            team_id, request.user_id, request.strategy
        )

        return {
            "success": True,
            "rules_count": len(registry.rules),
            "agents_count": len(registry.agents),
            "mcps_count": len(registry.mcps),
            "skills_count": len(registry.skills),
            "version": registry.version,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to sync registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/registry/import")
async def import_team_registry(team_id: str, request: ImportRegistryRequest):
    """Import registry data from JSON."""
    manager = await get_or_init_manager()

    try:
        team = await manager.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team.is_admin(request.user_id):
            raise HTTPException(status_code=403, detail="Only admins can import registry")

        from ..multiuser.registry import TeamRegistry

        imported = TeamRegistry.from_dict({"team_id": team_id, **request.registry})

        if request.merge:
            existing = await manager.get_team_registry(team_id, request.user_id)
            # Merge logic - add items that don't exist
            for rule in imported.rules:
                if not existing.get_rule_by_name(rule.name):
                    existing.add_rule(rule)
            for agent in imported.agents:
                if not existing.get_agent_by_name(agent.name):
                    existing.add_agent(agent)
            for mcp in imported.mcps:
                if not existing.get_mcp_by_name(mcp.name):
                    existing.add_mcp(mcp)
            for skill in imported.skills:
                if not existing.get_skill_by_name(skill.name):
                    existing.add_skill(skill)
            registry = existing
        else:
            registry = imported

        await manager.save_team_registry(registry, request.user_id)

        return {
            "success": True,
            "rules_count": len(registry.rules),
            "agents_count": len(registry.agents),
            "mcps_count": len(registry.mcps),
            "skills_count": len(registry.skills),
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to import registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
