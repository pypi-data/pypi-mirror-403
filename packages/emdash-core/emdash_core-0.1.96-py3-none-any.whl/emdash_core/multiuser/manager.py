"""SharedSessionManager - Main coordinator for multiuser sessions.

This module provides the central manager that ties together all multiuser
components: sessions, queues, broadcasters, and sync providers.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .protocols import (
    SyncProvider,
    SharedSessionInfo,
    SharedEvent,
    SharedEventType,
    Participant,
    ParticipantRole,
    QueuedMessage,
    SharedSessionState,
    SessionNotFoundError,
    InvalidInviteCodeError,
    NotAuthorizedError,
    TeamNotFoundError,
    TeamPermissionError,
)
from .models import SharedSession, UserIdentity
from .queue import SharedMessageQueue
from .broadcaster import SharedEventBroadcaster, SSESharedEventHandler
from .invites import generate_invite_code, InviteManager
from .teams import (
    Team,
    TeamMember,
    TeamRole,
    SessionVisibility,
    TeamSessionInfo,
    TeamManager,
)

log = logging.getLogger(__name__)


class SharedSessionManager:
    """Coordinates all multiuser session components.

    This is the main entry point for multiuser functionality. It manages:
    - Session creation and joining via invite codes
    - Message queueing when the agent is busy
    - Event broadcasting to all participants
    - State synchronization across machines

    Usage:
        from emdash_core.multiuser import SharedSessionManager, LocalFileSyncProvider

        # Create with sync provider
        provider = LocalFileSyncProvider(Path("~/.emdash/multiuser"))
        await provider.connect()

        manager = SharedSessionManager(provider=provider)

        # Create session
        session, invite_code = await manager.create_session(
            owner_id="user_123",
            display_name="Alice",
            repo_root=Path("/path/to/repo"),
        )

        # Send message (queues if agent busy)
        await manager.send_message(session.session_id, "user_123", "Hello!")

        # Another user joins
        session = await manager.join_session("ABC123", "user_456", "Bob")
    """

    def __init__(
        self,
        provider: Optional[SyncProvider] = None,
        storage_root: Optional[Path] = None,
    ):
        """Initialize the session manager.

        Args:
            provider: Sync provider for state persistence. If None, uses in-memory only.
            storage_root: Root for local storage (queues, invites). Defaults to ~/.emdash/multiuser
        """
        self._provider = provider
        self._storage_root = storage_root or Path.home() / ".emdash" / "multiuser"
        self._storage_root.mkdir(parents=True, exist_ok=True)

        # In-memory state
        self._sessions: dict[str, SharedSession] = {}
        self._queues: dict[str, SharedMessageQueue] = {}
        self._broadcasters: dict[str, SharedEventBroadcaster] = {}

        # SSE handlers per user per session: session_id -> user_id -> handler
        self._sse_handlers: dict[str, dict[str, Any]] = {}

        # Agent runners per session (set externally via integrate_runner)
        self._runners: dict[str, Any] = {}  # session_id -> AgentRunner

        # Processing tasks
        self._processing_tasks: dict[str, asyncio.Task] = {}

        # Invite manager
        self._invite_manager = InviteManager(
            storage_path=self._storage_root / "invites.json"
        )

        # Team manager
        self._team_manager = TeamManager(
            storage_root=self._storage_root,
            sync_provider=provider,
        )

        # Callbacks for session events
        self._on_session_created: list[Callable] = []
        self._on_participant_joined: list[Callable] = []
        self._on_participant_left: list[Callable] = []

    async def create_session(
        self,
        owner_id: str,
        display_name: str,
        repo_root: Optional[Path] = None,
        model: str = "",
        plan_mode: bool = False,
        initial_messages: Optional[list[dict]] = None,
    ) -> tuple[SharedSession, str]:
        """Create a new shared session.

        Args:
            owner_id: User ID of the session creator
            display_name: Display name of the owner
            repo_root: Repository root for the agent
            model: LLM model to use
            plan_mode: Whether to run in plan mode
            initial_messages: Optional pre-existing conversation history

        Returns:
            Tuple of (SharedSession, invite_code)
        """
        session_id = str(uuid.uuid4())
        invite_code = generate_invite_code()
        now = datetime.utcnow().isoformat()

        owner = Participant(
            user_id=owner_id,
            display_name=display_name,
            role=ParticipantRole.OWNER,
            joined_at=now,
            last_seen=now,
            is_online=True,
        )

        session = SharedSession(
            session_id=session_id,
            invite_code=invite_code,
            owner_id=owner_id,
            created_at=now,
            updated_at=now,
            state=SharedSessionState.ACTIVE,
            version=1,
            participants=[owner],
            message_queue=[],
            messages=initial_messages or [],
            model=model,
            plan_mode=plan_mode,
            repo_root=str(repo_root) if repo_root else "",
        )

        # Store in memory
        self._sessions[session_id] = session

        # Create queue
        queue_path = self._storage_root / "queues" / f"{session_id}.json"
        self._queues[session_id] = SharedMessageQueue(
            session_id=session_id,
            storage_path=queue_path,
            on_event=lambda t, d: self._handle_queue_event(session_id, t, d),
        )

        # Create broadcaster
        self._broadcasters[session_id] = SharedEventBroadcaster(
            session_id=session_id,
            sync_provider=self._provider,
        )

        # Initialize SSE handlers dict for this session
        self._sse_handlers[session_id] = {}

        # Persist via provider if available
        if self._provider:
            await self._provider.create_session(
                session_id=session_id,
                owner_id=owner_id,
                initial_state=session.to_dict(),
            )

        # Create invite token
        self._invite_manager.create_invite(
            session_id=session_id,
            created_by=owner_id,
        )

        # Notify callbacks
        for callback in self._on_session_created:
            try:
                result = callback(session)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                log.warning(f"Session created callback error: {e}")

        log.info(f"Created shared session {session_id} with invite {invite_code}")
        return session, invite_code

    async def join_session(
        self,
        invite_code: str,
        user_id: str,
        display_name: str,
    ) -> SharedSession:
        """Join an existing session via invite code.

        Args:
            invite_code: The invite code to join with
            user_id: Joining user's ID
            display_name: Joining user's display name

        Returns:
            The joined SharedSession

        Raises:
            InvalidInviteCodeError: If invite code is invalid
            SessionNotFoundError: If session not found
        """
        invite_code = invite_code.upper().strip()
        log.info(f"join_session called with invite_code={invite_code}, user_id={user_id}")

        # Find session by invite code
        session = None
        for s in self._sessions.values():
            if s.invite_code == invite_code:
                session = s
                log.info(f"Found session {s.session_id} in local cache")
                break

        # Try provider if not found locally
        if not session and self._provider:
            log.info(f"Session not in local cache, querying provider...")
            session_id = await self._provider.find_session_by_invite(invite_code)
            if session_id:
                log.info(f"Found session_id={session_id} via provider")
                # Load full session from provider
                session_data = await self._provider.get_full_session(session_id)
                session = SharedSession.from_dict(session_data)
                self._sessions[session_id] = session

                # Create local components
                log.info(f"Setting up session components for {session_id}")
                await self._setup_session_components(session)
                log.info(f"Queue created: {session_id in self._queues}")

        if not session:
            raise InvalidInviteCodeError(f"Invalid invite code: {invite_code}")

        # Add participant
        now = datetime.utcnow().isoformat()
        participant = Participant(
            user_id=user_id,
            display_name=display_name,
            role=ParticipantRole.EDITOR,
            joined_at=now,
            last_seen=now,
            is_online=True,
        )
        session.add_participant(participant)

        # Update provider
        if self._provider:
            await self._provider.update_session_state(
                session.session_id,
                {"participants": [p.to_dict() for p in session.participants]},
            )

        # Broadcast join event
        broadcaster = self._broadcasters.get(session.session_id)
        if broadcaster:
            await broadcaster.broadcast_participant_joined(user_id, display_name)

        # Notify callbacks
        for callback in self._on_participant_joined:
            try:
                result = callback(session, participant)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                log.warning(f"Participant joined callback error: {e}")

        log.info(f"User {user_id} joined session {session.session_id}")
        return session

    async def leave_session(
        self,
        session_id: str,
        user_id: str,
    ) -> bool:
        """Leave a shared session.

        Args:
            session_id: Session to leave
            user_id: User leaving

        Returns:
            True if left successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Get participant info before removal
        participant = session.get_participant(user_id)
        display_name = participant.display_name if participant else user_id

        # Remove participant
        removed = session.remove_participant(user_id)
        if not removed:
            return False

        # Remove SSE handler
        if session_id in self._sse_handlers:
            self._sse_handlers[session_id].pop(user_id, None)

        # Update provider
        if self._provider:
            await self._provider.update_session_state(
                session_id,
                {"participants": [p.to_dict() for p in session.participants]},
            )

        # Broadcast leave event
        broadcaster = self._broadcasters.get(session_id)
        if broadcaster:
            await broadcaster.broadcast_participant_left(user_id, display_name)

        # Notify callbacks
        for callback in self._on_participant_left:
            try:
                result = callback(session, user_id)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                log.warning(f"Participant left callback error: {e}")

        log.info(f"User {user_id} left session {session_id}")
        return True

    async def send_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        images: Optional[list[dict]] = None,
        priority: int = 0,
    ) -> QueuedMessage:
        """Send a message in a shared session.

        If the agent is busy, the message is queued. Otherwise,
        it's processed immediately.

        Args:
            session_id: Session to send message in
            user_id: User sending the message
            content: Message content
            images: Optional images to include
            priority: Message priority (higher = more urgent)

        Returns:
            The queued message

        Raises:
            SessionNotFoundError: If session not found
            NotAuthorizedError: If user can't send messages
        """
        log.info(f"send_message called: session_id={session_id!r}, user_id={user_id}, manager_id={id(self)}")
        log.info(f"Current sessions in memory: {list(self._sessions.keys())}")
        log.info(f"Current queues in memory: {list(self._queues.keys())}")
        # Direct debug - check queue lookup
        direct_q = self._queues.get(session_id)
        log.info(f"Direct queue lookup result: {direct_q!r}, bool: {bool(direct_q) if direct_q else 'N/A'}")

        session = self._sessions.get(session_id)
        need_setup = session is None

        if not session:
            # Try to load from provider if not in memory
            log.warning(f"Session {session_id} not in memory, trying provider...")
            if self._provider:
                try:
                    session_data = await self._provider.get_full_session(session_id)
                    session = SharedSession.from_dict(session_data)
                    self._sessions[session_id] = session
                    log.info(f"Loaded session {session_id} from provider")
                except Exception as e:
                    log.error(f"Failed to load session from provider: {e}")
                    raise SessionNotFoundError(f"Session {session_id} not found")
            else:
                raise SessionNotFoundError(f"Session {session_id} not found")

        # Check authorization
        if not session.can_send_message(user_id):
            raise NotAuthorizedError(f"User {user_id} cannot send messages")

        # Ensure queue exists - set up components if session was loaded from provider
        # or if queue is missing for any reason
        # NOTE: Use 'is None' not 'if not queue' because SharedMessageQueue.__len__
        # returns 0 for empty queues, making them falsy
        queue = self._queues.get(session_id)
        if queue is None:
            log.warning(f"Queue not found for session {session_id}, setting up components...")
            await self._setup_session_components(session)
            queue = self._queues.get(session_id)

        if queue is None:
            log.error(f"Queue still not found after setup for session {session_id}")
            raise SessionNotFoundError(f"Queue for session {session_id} not found")

        # Enqueue message
        message = await queue.enqueue(user_id, content, images, priority)

        # Update participant last_seen
        session.update_participant_presence(user_id, is_online=True)

        # Broadcast queue update
        broadcaster = self._broadcasters.get(session_id)
        if broadcaster:
            await broadcaster.broadcast_queue_update(
                queue_length=len(queue),
                current_message_id=queue.current_message_id,
                current_user_id=queue.current_user_id,
            )

        # Start processing if not already running
        if session_id not in self._processing_tasks or self._processing_tasks[session_id].done():
            task = asyncio.create_task(self._process_queue(session_id))
            self._processing_tasks[session_id] = task

        log.info(f"Message queued in session {session_id} by {user_id}")
        return message

    async def _process_queue(self, session_id: str) -> None:
        """Process messages from the queue using the agent runner.

        This runs as a background task, processing messages one at a time.
        """
        queue = self._queues.get(session_id)
        session = self._sessions.get(session_id)
        broadcaster = self._broadcasters.get(session_id)

        if queue is None or session is None:
            return

        while True:
            # Try to dequeue
            message = await queue.dequeue(timeout=None)
            if not message:
                break

            # Update session state
            old_state = session.state
            session.state = SharedSessionState.AGENT_BUSY
            if broadcaster:
                await broadcaster.broadcast_state_change(old_state.value, session.state.value)
                broadcaster.set_current_user(message.user_id)

            try:
                # Get or create runner
                runner = self._runners.get(session_id)
                if runner:
                    # Add user message to conversation
                    user_msg = {"role": "user", "content": message.content}
                    if message.images:
                        user_msg["images"] = message.images

                    # Run agent
                    if runner._messages:
                        response = runner.chat(message.content, images=message.images or None)
                    else:
                        response = runner.run(message.content, images=message.images or None)

                    # Update session messages
                    session.messages = runner._messages

                else:
                    # No server-side runner - broadcast request for owner's CLI to process
                    # The owner's CLI will receive this via SSE and process with its local agent
                    log.info(f"No server-side runner for session {session_id}, broadcasting process_message_request")
                    log.info(f"  Broadcaster exists: {broadcaster is not None}")
                    if broadcaster:
                        log.info(f"  Broadcaster handler count: {broadcaster.handler_count}")
                        # Get display name for the requesting user
                        participant = session.get_participant(message.user_id)
                        display_name = participant.display_name if participant else "User"
                        await broadcaster.broadcast(
                            SharedEventType.PROCESS_MESSAGE_REQUEST.value,
                            {
                                "message_id": message.id,
                                "user_id": message.user_id,
                                "display_name": display_name,
                                "content": message.content,
                                "images": message.images,
                                "queued_at": message.queued_at,
                                "owner_id": session.owner_id,
                            },
                        )
                        log.info(f"  Broadcast completed")
                    else:
                        log.warning(f"  No broadcaster for session {session_id}!")
                    # Mark message as complete since we've handed it off
                    # The owner's CLI will process and broadcast the response
                    await queue.complete(message.id)
                    session.state = SharedSessionState.ACTIVE
                    if broadcaster:
                        await broadcaster.broadcast_state_change(
                            SharedSessionState.AGENT_BUSY.value,
                            SharedSessionState.ACTIVE.value,
                        )
                    continue

                # Update session state
                session.updated_at = datetime.utcnow().isoformat()
                session.version += 1

                # Persist if provider available
                if self._provider:
                    await self._provider.update_session_state(
                        session_id,
                        {
                            "messages": session.messages,
                            "updated_at": session.updated_at,
                            "state": SharedSessionState.ACTIVE.value,
                        },
                    )

            except Exception as e:
                log.error(f"Error processing message in session {session_id}: {e}")
                if broadcaster:
                    await broadcaster.broadcast(
                        SharedEventType.STATE_CHANGED.value,
                        {"error": str(e)},
                    )

            finally:
                # Complete the message
                await queue.complete(message.id)

                # Reset state
                session.state = SharedSessionState.ACTIVE
                if broadcaster:
                    await broadcaster.broadcast_state_change(
                        SharedSessionState.AGENT_BUSY.value,
                        SharedSessionState.ACTIVE.value,
                    )
                    broadcaster.set_current_user(None)

    async def _setup_session_components(self, session: SharedSession) -> None:
        """Set up local components for a session loaded from provider."""
        session_id = session.session_id

        # Create queue
        queue_path = self._storage_root / "queues" / f"{session_id}.json"
        self._queues[session_id] = SharedMessageQueue(
            session_id=session_id,
            storage_path=queue_path,
            on_event=lambda t, d: self._handle_queue_event(session_id, t, d),
        )

        # Restore queue state from session
        for msg in session.message_queue:
            await self._queues[session_id].enqueue(
                msg.user_id, msg.content, msg.images, msg.priority
            )

        # Create broadcaster
        self._broadcasters[session_id] = SharedEventBroadcaster(
            session_id=session_id,
            sync_provider=self._provider,
        )

        # Initialize SSE handlers dict
        self._sse_handlers[session_id] = {}

    def _handle_queue_event(self, session_id: str, event_type: str, data: dict) -> None:
        """Handle events from the message queue."""
        broadcaster = self._broadcasters.get(session_id)
        if broadcaster:
            asyncio.create_task(broadcaster.broadcast(event_type, data))

    # ─────────────────────────────────────────────────────────────
    # Integration methods
    # ─────────────────────────────────────────────────────────────

    def integrate_runner(self, session_id: str, runner: Any) -> None:
        """Integrate an AgentRunner with a shared session.

        This wires up the runner's emitter to the broadcaster so events
        are fanned out to all participants.

        Args:
            session_id: Session to integrate with
            runner: AgentRunner instance
        """
        self._runners[session_id] = runner

        # Wire emitter to broadcaster
        broadcaster = self._broadcasters.get(session_id)
        if broadcaster and hasattr(runner, "emitter"):
            runner.emitter.add_handler(broadcaster)

        # Sync messages from runner to session
        session = self._sessions.get(session_id)
        if session and hasattr(runner, "_messages"):
            session.messages = runner._messages

        log.info(f"Integrated runner with session {session_id}")

    async def add_sse_handler_async(self, session_id: str, user_id: str, sse_handler: Any) -> None:
        """Add an SSE handler for a user in a session (async version).

        Args:
            session_id: Session ID
            user_id: User ID
            sse_handler: SSEHandler instance
        """
        log.info(f"[SSE] add_sse_handler_async called: session={session_id}, user={user_id}")
        log.info(f"[SSE] Current broadcasters: {list(self._broadcasters.keys())}")
        log.info(f"[SSE] Current sessions: {list(self._sessions.keys())}")

        if session_id not in self._sse_handlers:
            self._sse_handlers[session_id] = {}

        # Ensure broadcaster exists - set up session components if needed
        if session_id not in self._broadcasters:
            log.info(f"[SSE] Broadcaster missing for {session_id}, checking session...")
            session = self._sessions.get(session_id)
            if session:
                log.info(f"[SSE] Session found, setting up components...")
                await self._setup_session_components(session)
            else:
                log.warning(f"[SSE] Session {session_id} not found in memory!")

        # Create adapter and add to broadcaster
        adapter = SSESharedEventHandler(sse_handler)
        self._sse_handlers[session_id][user_id] = adapter

        broadcaster = self._broadcasters.get(session_id)
        if broadcaster:
            broadcaster.add_handler(adapter)
            log.info(f"[SSE] Handler added! session={session_id}, user={user_id}, total_handlers={broadcaster.handler_count}")
        else:
            log.error(f"[SSE] FAILED: No broadcaster for {session_id}!")

    def add_sse_handler(self, session_id: str, user_id: str, sse_handler: Any) -> None:
        """Add an SSE handler for a user in a session (sync wrapper).

        Args:
            session_id: Session ID
            user_id: User ID
            sse_handler: SSEHandler instance
        """
        # Try to run async version
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the async version
                asyncio.create_task(self.add_sse_handler_async(session_id, user_id, sse_handler))
            else:
                loop.run_until_complete(self.add_sse_handler_async(session_id, user_id, sse_handler))
        except RuntimeError:
            # Fallback: just do sync setup
            if session_id not in self._sse_handlers:
                self._sse_handlers[session_id] = {}

            # Ensure broadcaster exists
            if session_id not in self._broadcasters:
                session = self._sessions.get(session_id)
                if session:
                    log.info(f"Creating broadcaster for session {session_id} (sync fallback)")
                    self._broadcasters[session_id] = SharedEventBroadcaster(
                        session_id=session_id,
                        sync_provider=self._provider,
                    )

            adapter = SSESharedEventHandler(sse_handler)
            self._sse_handlers[session_id][user_id] = adapter

            broadcaster = self._broadcasters.get(session_id)
            if broadcaster:
                broadcaster.add_handler(adapter)
                log.info(f"SSE handler added (sync) for session {session_id}")

    def remove_sse_handler(self, session_id: str, user_id: str) -> None:
        """Remove an SSE handler for a user.

        Args:
            session_id: Session ID
            user_id: User ID
        """
        if session_id not in self._sse_handlers:
            return

        adapter = self._sse_handlers[session_id].pop(user_id, None)
        if adapter:
            broadcaster = self._broadcasters.get(session_id)
            if broadcaster:
                broadcaster.remove_handler(adapter)

    async def broadcast_event(
        self,
        session_id: str,
        event_type: str,
        data: dict,
        source_user_id: str | None = None,
    ) -> None:
        """Broadcast an event to all participants in a session.

        This is used by the owner's CLI to relay agent responses
        to all participants after processing messages locally.

        Args:
            session_id: Session ID
            event_type: Event type string
            data: Event data dict
            source_user_id: User who triggered the event (for filtering)
        """
        broadcaster = self._broadcasters.get(session_id)
        log.info(f"[BROADCAST] event={event_type}, session={session_id}, broadcaster_exists={broadcaster is not None}")
        if broadcaster:
            log.info(f"[BROADCAST] handlers={broadcaster.handler_count}, source_user={source_user_id}")
            await broadcaster.broadcast(event_type, data, source_user_id=source_user_id)
            log.info(f"[BROADCAST] Done: {event_type}")
        else:
            log.error(f"[BROADCAST] FAILED: No broadcaster for session {session_id}!")

    # ─────────────────────────────────────────────────────────────
    # Query methods
    # ─────────────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Optional[SharedSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_session_by_invite(self, invite_code: str) -> Optional[SharedSession]:
        """Get a session by invite code."""
        invite_code = invite_code.upper().strip()
        for session in self._sessions.values():
            if session.invite_code == invite_code:
                return session
        return None

    def get_user_sessions(self, user_id: str) -> list[SharedSession]:
        """Get all sessions a user is participating in."""
        return [
            session
            for session in self._sessions.values()
            if session.get_participant(user_id) is not None
        ]

    def get_session_participants(self, session_id: str) -> list[Participant]:
        """Get participants in a session."""
        session = self._sessions.get(session_id)
        return session.participants if session else []

    def get_queue_status(self, session_id: str) -> dict[str, Any]:
        """Get message queue status for a session."""
        queue = self._queues.get(session_id)
        if queue is None:
            return {"error": "Queue not found"}

        return {
            "length": len(queue),
            "agent_busy": queue.is_agent_busy,
            "current_message_id": queue.current_message_id,
            "current_user_id": queue.current_user_id,
        }

    # ─────────────────────────────────────────────────────────────
    # Callback registration
    # ─────────────────────────────────────────────────────────────

    def on_session_created(self, callback: Callable) -> None:
        """Register a callback for session creation."""
        self._on_session_created.append(callback)

    def on_participant_joined(self, callback: Callable) -> None:
        """Register a callback for participant joins."""
        self._on_participant_joined.append(callback)

    def on_participant_left(self, callback: Callable) -> None:
        """Register a callback for participant leaves."""
        self._on_participant_left.append(callback)

    # ─────────────────────────────────────────────────────────────
    # Team Management
    # ─────────────────────────────────────────────────────────────

    async def create_team(
        self,
        name: str,
        user_id: str,
        display_name: str,
        description: str = "",
    ) -> Team:
        """Create a new team.

        Args:
            name: Team name
            user_id: Creator's user ID (becomes admin)
            display_name: Creator's display name
            description: Optional team description

        Returns:
            The created Team
        """
        team = await self._team_manager.create_team(
            name=name,
            creator_id=user_id,
            creator_name=display_name,
            description=description,
        )
        log.info(f"Created team '{name}' with ID {team.team_id}")
        return team

    async def join_team(
        self,
        invite_code: str,
        user_id: str,
        display_name: str,
    ) -> Team:
        """Join a team using invite code.

        Args:
            invite_code: Team invite code (e.g., "T-ABC12345")
            user_id: Joining user's ID
            display_name: Joining user's display name

        Returns:
            The joined Team

        Raises:
            ValueError: If invite code is invalid
        """
        team = await self._team_manager.join_team(
            invite_code=invite_code,
            user_id=user_id,
            display_name=display_name,
        )
        log.info(f"User {user_id} joined team {team.team_id}")
        return team

    async def leave_team(self, team_id: str, user_id: str) -> bool:
        """Leave a team.

        Args:
            team_id: Team to leave
            user_id: User leaving

        Returns:
            True if left successfully
        """
        return await self._team_manager.leave_team(team_id, user_id)

    async def get_team(self, team_id: str) -> Optional[Team]:
        """Get a team by ID."""
        return await self._team_manager.get_team(team_id)

    async def get_user_teams(self, user_id: str) -> list[Team]:
        """Get all teams a user is a member of."""
        return await self._team_manager.get_user_teams(user_id)

    async def add_session_to_team(
        self,
        team_id: str,
        session_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> bool:
        """Add a session to a team.

        The user must own the session or be a team admin.

        Args:
            team_id: Target team
            session_id: Session to add
            user_id: User adding the session
            title: Optional title for the session in team listings

        Returns:
            True if added successfully

        Raises:
            TeamNotFoundError: If team not found
            TeamPermissionError: If user lacks permission
            SessionNotFoundError: If session not found
        """
        # Verify team exists
        team = await self._team_manager.get_team(team_id)
        if not team:
            raise TeamNotFoundError(f"Team {team_id} not found")

        # Verify session exists and user has permission
        session = self._sessions.get(session_id)
        if not session and self._provider:
            try:
                session_data = await self._provider.get_full_session(session_id)
                session = SharedSession.from_dict(session_data)
            except Exception:
                pass

        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # Check permission: must be session owner or team admin
        if not session.is_owner(user_id) and not team.is_admin(user_id):
            raise TeamPermissionError(
                "Must be session owner or team admin to add sessions"
            )

        # Update session
        session.team_id = team_id
        session.visibility = SessionVisibility.TEAM
        if title:
            session.title = title

        # Update in memory
        self._sessions[session_id] = session

        # Add via team manager
        await self._team_manager.add_session_to_team(
            team_id=team_id,
            session_id=session_id,
            user_id=user_id,
            title=title,
        )

        # Broadcast event
        broadcaster = self._broadcasters.get(session_id)
        if broadcaster:
            await broadcaster.broadcast(
                SharedEventType.SESSION_ADDED_TO_TEAM.value,
                {
                    "session_id": session_id,
                    "team_id": team_id,
                    "team_name": team.name,
                    "added_by": user_id,
                },
            )

        log.info(f"Added session {session_id} to team {team_id}")
        return True

    async def remove_session_from_team(
        self,
        session_id: str,
        user_id: str,
    ) -> bool:
        """Remove a session from its team.

        Args:
            session_id: Session to remove
            user_id: User removing the session

        Returns:
            True if removed successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        team_id = session.team_id
        if not team_id:
            return False  # Not in a team

        # Verify permission
        team = await self._team_manager.get_team(team_id)
        if team and not session.is_owner(user_id) and not team.is_admin(user_id):
            raise TeamPermissionError(
                "Must be session owner or team admin to remove sessions"
            )

        # Update session
        session.team_id = None
        session.visibility = SessionVisibility.PRIVATE

        # Remove via team manager
        await self._team_manager.remove_session_from_team(session_id, user_id)

        # Broadcast event
        broadcaster = self._broadcasters.get(session_id)
        if broadcaster:
            await broadcaster.broadcast(
                SharedEventType.SESSION_REMOVED_FROM_TEAM.value,
                {
                    "session_id": session_id,
                    "team_id": team_id,
                    "removed_by": user_id,
                },
            )

        log.info(f"Removed session {session_id} from team {team_id}")
        return True

    async def list_team_sessions(
        self,
        team_id: str,
        user_id: str,
    ) -> list[TeamSessionInfo]:
        """List all sessions in a team.

        Args:
            team_id: Team to list sessions for
            user_id: Requesting user (must be team member)

        Returns:
            List of TeamSessionInfo for team sessions
        """
        return await self._team_manager.list_team_sessions(team_id, user_id)

    async def join_team_session(
        self,
        team_id: str,
        session_id: str,
        user_id: str,
        display_name: str,
    ) -> SharedSession:
        """Join a session from a team (team members can join without invite).

        Args:
            team_id: Team the session belongs to
            session_id: Session to join
            user_id: User joining
            display_name: User's display name

        Returns:
            The joined SharedSession

        Raises:
            TeamPermissionError: If user is not a team member
            SessionNotFoundError: If session not found or not in team
        """
        # Verify team membership
        team = await self._team_manager.get_team(team_id)
        if not team:
            raise TeamNotFoundError(f"Team {team_id} not found")

        if not team.is_member(user_id):
            raise TeamPermissionError("Must be a team member to join team sessions")

        # Get session
        session = self._sessions.get(session_id)
        if not session and self._provider:
            try:
                session_data = await self._provider.get_full_session(session_id)
                session = SharedSession.from_dict(session_data)
                self._sessions[session_id] = session
                await self._setup_session_components(session)
            except Exception:
                pass

        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # Verify session is in the team
        if session.team_id != team_id:
            raise SessionNotFoundError(f"Session {session_id} is not in team {team_id}")

        # Add participant
        now = datetime.utcnow().isoformat()
        participant = Participant(
            user_id=user_id,
            display_name=display_name,
            role=ParticipantRole.EDITOR,
            joined_at=now,
            last_seen=now,
            is_online=True,
        )
        session.add_participant(participant)

        # Update provider
        if self._provider:
            await self._provider.update_session_state(
                session.session_id,
                {"participants": [p.to_dict() for p in session.participants]},
            )

        # Broadcast join event
        broadcaster = self._broadcasters.get(session.session_id)
        if broadcaster:
            await broadcaster.broadcast_participant_joined(user_id, display_name)

        log.info(f"User {user_id} joined team session {session_id}")
        return session

    def get_team_manager(self) -> TeamManager:
        """Get the underlying TeamManager instance."""
        return self._team_manager

    # ─────────────────────────────────────────────────────────────
    # Registry Operations
    # ─────────────────────────────────────────────────────────────

    async def get_team_registry(self, team_id: str, user_id: str):
        """Get the registry for a team.

        Args:
            team_id: Team ID
            user_id: Requesting user (must be team member)

        Returns:
            TeamRegistry for the team
        """
        return await self._team_manager.get_team_registry(team_id, user_id)

    async def save_team_registry(self, registry, user_id: str) -> bool:
        """Save the registry for a team.

        Args:
            registry: Registry to save
            user_id: User saving (must be team admin)

        Returns:
            True if saved successfully
        """
        return await self._team_manager.save_team_registry(registry, user_id)

    async def sync_team_registry(
        self,
        team_id: str,
        user_id: str,
        strategy: str = "remote_wins",
    ):
        """Sync the team registry between local and remote.

        Args:
            team_id: Team ID
            user_id: Requesting user (must be team member)
            strategy: Conflict resolution strategy

        Returns:
            Synced TeamRegistry
        """
        return await self._team_manager.sync_team_registry(team_id, user_id, strategy)

    # ─────────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────────

    async def close_session(self, session_id: str, user_id: str) -> bool:
        """Close a shared session (owner only).

        Args:
            session_id: Session to close
            user_id: User attempting to close (must be owner)

        Returns:
            True if closed successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        if not session.is_owner(user_id):
            raise NotAuthorizedError(f"Only the owner can close the session")

        # Cancel processing task
        if session_id in self._processing_tasks:
            self._processing_tasks[session_id].cancel()
            del self._processing_tasks[session_id]

        # Broadcast close event
        broadcaster = self._broadcasters.get(session_id)
        if broadcaster:
            await broadcaster.broadcast(
                SharedEventType.SESSION_CLOSED.value,
                {"session_id": session_id, "closed_by": user_id},
            )

        # Clean up components
        self._sessions.pop(session_id, None)
        self._queues.pop(session_id, None)
        self._broadcasters.pop(session_id, None)
        self._runners.pop(session_id, None)
        self._sse_handlers.pop(session_id, None)

        # Revoke invites
        self._invite_manager.revoke_session_invites(session_id)

        log.info(f"Closed session {session_id}")
        return True


# Global manager instance (lazily initialized)
_global_manager: Optional[SharedSessionManager] = None
_manager_initialized = False
_init_lock: asyncio.Lock = asyncio.Lock()


def _get_init_lock() -> asyncio.Lock:
    """Get the initialization lock."""
    return _init_lock


def get_shared_session_manager() -> SharedSessionManager:
    """Get the global SharedSessionManager instance (sync version).

    WARNING: This creates a manager without provider if called before
    async initialization. For API routes, use `await get_or_init_manager()` instead.
    """
    global _global_manager

    if _global_manager is None:
        log.warning("get_shared_session_manager called before async init - creating basic manager")
        _global_manager = SharedSessionManager()

    return _global_manager


async def get_or_init_manager() -> SharedSessionManager:
    """Get the global SharedSessionManager, initializing with provider if needed.

    This is the preferred way to get the manager from async contexts (API routes).
    It ensures the manager is properly initialized with the configured sync provider.
    """
    global _global_manager, _manager_initialized

    if _global_manager is not None:
        log.debug(f"Returning existing manager (id={id(_global_manager)})")
        return _global_manager

    log.info("Manager not initialized, initializing now...")

    # Use lock to prevent multiple concurrent initializations
    async with _get_init_lock():
        # Double-check after acquiring lock
        if _global_manager is not None:
            log.debug(f"Manager was initialized while waiting for lock (id={id(_global_manager)})")
            return _global_manager

        # Initialize with provider
        log.info("Calling init_shared_session_manager()...")
        manager = await init_shared_session_manager()
        if manager is None:
            # Multiuser disabled - create basic manager
            log.warning("Multiuser disabled, creating basic manager")
            _global_manager = SharedSessionManager()

        log.info(f"Manager initialized (id={id(_global_manager)}), provider={type(_global_manager._provider).__name__ if _global_manager and _global_manager._provider else 'None'}")

        # _global_manager is guaranteed to be set by init_shared_session_manager
        assert _global_manager is not None
        return _global_manager


async def init_shared_session_manager() -> Optional[SharedSessionManager]:
    """Initialize the global SharedSessionManager with configured provider.

    This should be called once at application startup. It reads the
    configuration from environment variables and creates the appropriate
    sync provider.

    Returns:
        The initialized manager, or None if multiuser is disabled

    Example:
        # At application startup
        manager = await init_shared_session_manager()
        if manager:
            print("Multiuser enabled!")
    """
    global _global_manager, _manager_initialized

    if _manager_initialized:
        return _global_manager

    from .config import (
        get_multiuser_config,
        create_sync_provider,
        is_multiuser_enabled,
    )

    config = get_multiuser_config()

    if not config.enabled:
        log.info("Multiuser is disabled")
        _manager_initialized = True
        return None

    # Create and connect provider
    try:
        provider = await create_sync_provider()
    except Exception as e:
        log.error(f"Failed to create sync provider: {e}")
        provider = None

    # Create manager with provider
    _global_manager = SharedSessionManager(
        provider=provider,
        storage_root=config.storage_root,
    )

    _manager_initialized = True
    log.info(f"Initialized SharedSessionManager with {config.provider.value} provider")

    return _global_manager


def set_shared_session_manager(manager: SharedSessionManager) -> None:
    """Set the global SharedSessionManager instance."""
    global _global_manager
    _global_manager = manager
