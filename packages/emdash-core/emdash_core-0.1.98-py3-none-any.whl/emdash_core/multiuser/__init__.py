"""Multiuser chat integration for shared agent sessions.

This module enables multiple users to collaborate in a single agent
conversation with real-time synchronization across machines.

Key Features:
- Shared conversation sessions with invite codes
- Message queue for concurrent user inputs
- Event broadcasting to all participants
- Pluggable sync providers (local, Firebase, WebSocket)

Basic Usage:
    from emdash_core.multiuser import (
        SharedSessionManager,
        LocalFileSyncProvider,
    )

    # Create provider and manager
    provider = LocalFileSyncProvider(Path("~/.emdash/multiuser"))
    await provider.connect()

    manager = SharedSessionManager(provider)

    # Create shared session
    session, invite_code = await manager.create_session(
        owner_id="user_123",
        display_name="Alice",
    )
    print(f"Share this code: {invite_code}")

    # Join from another machine/process
    session = await manager.join_session(
        invite_code="ABC123",
        user_id="user_456",
        display_name="Bob",
    )

    # Send message (queues if agent busy)
    message = await manager.send_message(
        session_id=session.session_id,
        user_id="user_123",
        content="Hello agent!",
    )
"""

# Protocols and exceptions
from .protocols import (
    # Enums
    ParticipantRole,
    SharedSessionState,
    SharedEventType,
    # Data classes
    Participant,
    QueuedMessage,
    SharedSessionInfo,
    SharedEvent,
    # Protocols
    SharedEventHandler,
    SyncProvider,
    # Exceptions
    MultiuserError,
    SessionNotFoundError,
    InvalidInviteCodeError,
    ConflictError,
    NotAuthorizedError,
    AgentBusyError,
    TeamNotFoundError,
    InvalidTeamInviteError,
    TeamPermissionError,
)

# Models
from .models import (
    SharedSession,
    InviteToken,
    UserIdentity,
)

# Queue
from .queue import (
    SharedMessageQueue,
    SyncedMessageQueue,
)

# Broadcaster
from .broadcaster import (
    SharedEventBroadcaster,
    SSESharedEventHandler,
    RemoteEventReceiver,
)

# Invites
from .invites import (
    generate_invite_code,
    normalize_invite_code,
    InviteManager,
    get_invite_manager,
    set_invite_manager,
)

# Providers
from .providers import LocalFileSyncProvider, FirebaseSyncProvider

# Teams
from .teams import (
    Team,
    TeamMember,
    TeamRole,
    SessionVisibility,
    TeamSessionInfo,
    TeamManager,
    get_team_manager,
    set_team_manager,
    init_team_manager,
)

# Registry
from .registry import (
    Rule,
    AgentConfig,
    MCPConfig,
    Skill,
    TeamRegistry,
    RegistryItemType,
    RegistryManager,
)

# Manager
from .manager import (
    SharedSessionManager,
    get_shared_session_manager,
    get_or_init_manager,
    set_shared_session_manager,
    init_shared_session_manager,
)

# Config
from .config import (
    MultiuserConfig,
    FirebaseConfig,
    SyncProviderType,
    get_multiuser_config,
    set_multiuser_config,
    is_multiuser_enabled,
    create_sync_provider,
    print_config_help,
)

__all__ = [
    # Enums
    "ParticipantRole",
    "SharedSessionState",
    "SharedEventType",
    "TeamRole",
    "SessionVisibility",
    # Data classes
    "Participant",
    "QueuedMessage",
    "SharedSessionInfo",
    "SharedEvent",
    "TeamSessionInfo",
    # Models
    "SharedSession",
    "InviteToken",
    "UserIdentity",
    "Team",
    "TeamMember",
    # Protocols
    "SharedEventHandler",
    "SyncProvider",
    # Queue
    "SharedMessageQueue",
    "SyncedMessageQueue",
    # Broadcaster
    "SharedEventBroadcaster",
    "SSESharedEventHandler",
    "RemoteEventReceiver",
    # Invites
    "generate_invite_code",
    "normalize_invite_code",
    "InviteManager",
    "get_invite_manager",
    "set_invite_manager",
    # Providers
    "LocalFileSyncProvider",
    "FirebaseSyncProvider",
    # Manager
    "SharedSessionManager",
    "get_shared_session_manager",
    "get_or_init_manager",
    "set_shared_session_manager",
    "init_shared_session_manager",
    # Teams
    "TeamManager",
    "get_team_manager",
    "set_team_manager",
    "init_team_manager",
    # Registry
    "Rule",
    "AgentConfig",
    "MCPConfig",
    "Skill",
    "TeamRegistry",
    "RegistryItemType",
    "RegistryManager",
    # Config
    "MultiuserConfig",
    "FirebaseConfig",
    "SyncProviderType",
    "get_multiuser_config",
    "set_multiuser_config",
    "is_multiuser_enabled",
    "create_sync_provider",
    "print_config_help",
    # Exceptions
    "MultiuserError",
    "SessionNotFoundError",
    "InvalidInviteCodeError",
    "ConflictError",
    "NotAuthorizedError",
    "AgentBusyError",
    "TeamNotFoundError",
    "InvalidTeamInviteError",
    "TeamPermissionError",
]
