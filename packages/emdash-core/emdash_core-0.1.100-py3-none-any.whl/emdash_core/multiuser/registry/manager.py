"""Registry Manager for Team Registry operations.

Handles CRUD operations for team registries, including:
- Local storage management
- Firebase sync
- Version conflict resolution
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Protocol, Union

from .models import (
    AgentConfig,
    MCPConfig,
    RegistryItemType,
    Rule,
    Skill,
    TeamRegistry,
)

if TYPE_CHECKING:
    from ..providers.base import SyncProvider

logger = logging.getLogger(__name__)


class RegistryStorageProvider(Protocol):
    """Protocol for registry storage backends."""

    async def get_registry(self, team_id: str) -> Optional[dict[str, Any]]:
        """Get registry data for a team."""
        ...

    async def save_registry(self, team_id: str, registry: dict[str, Any]) -> bool:
        """Save registry data for a team."""
        ...

    async def delete_registry(self, team_id: str) -> bool:
        """Delete registry for a team."""
        ...


class RegistryManager:
    """Manages team registries with local and remote sync.

    The RegistryManager provides:
    - CRUD operations for rules, agents, MCPs, and skills
    - Local file storage in .emdash/teams/{team_id}/registry.json
    - Remote sync with Firebase (when configured)
    - Version-based conflict detection

    Example:
        manager = RegistryManager(base_path=".emdash")
        registry = await manager.get_registry("team-123")
        registry.add_rule(Rule(name="Code Style", content="Use PEP 8"))
        await manager.save_registry(registry)
    """

    def __init__(
        self,
        base_path: Union[str, Path] = ".emdash",
        remote_provider: Optional["SyncProvider"] = None,
    ):
        """Initialize the registry manager.

        Args:
            base_path: Base path for local storage (default: .emdash)
            remote_provider: Optional remote sync provider (Firebase)
        """
        self.base_path = Path(base_path)
        self.remote_provider = remote_provider
        self._cache: dict[str, TeamRegistry] = {}

    # ─────────────────────────────────────────────────────────────
    # Path helpers
    # ─────────────────────────────────────────────────────────────

    def _get_team_dir(self, team_id: str) -> Path:
        """Get the directory for a team's data."""
        return self.base_path / "teams" / team_id

    def _get_registry_path(self, team_id: str) -> Path:
        """Get the path to a team's registry file."""
        return self._get_team_dir(team_id) / "registry.json"

    def _ensure_team_dir(self, team_id: str) -> Path:
        """Ensure the team directory exists."""
        team_dir = self._get_team_dir(team_id)
        team_dir.mkdir(parents=True, exist_ok=True)
        return team_dir

    # ─────────────────────────────────────────────────────────────
    # Local storage operations
    # ─────────────────────────────────────────────────────────────

    def _load_local(self, team_id: str) -> Optional[TeamRegistry]:
        """Load registry from local storage."""
        registry_path = self._get_registry_path(team_id)
        if not registry_path.exists():
            return None

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TeamRegistry.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load registry for team {team_id}: {e}")
            return None

    def _save_local(self, registry: TeamRegistry) -> bool:
        """Save registry to local storage."""
        self._ensure_team_dir(registry.team_id)
        registry_path = self._get_registry_path(registry.team_id)

        try:
            with open(registry_path, "w", encoding="utf-8") as f:
                json.dump(registry.to_dict(), f, indent=2)
            return True
        except IOError as e:
            logger.error(f"Failed to save registry for team {registry.team_id}: {e}")
            return False

    def _delete_local(self, team_id: str) -> bool:
        """Delete registry from local storage."""
        registry_path = self._get_registry_path(team_id)
        if registry_path.exists():
            try:
                registry_path.unlink()
                return True
            except IOError as e:
                logger.error(f"Failed to delete registry for team {team_id}: {e}")
                return False
        return True

    # ─────────────────────────────────────────────────────────────
    # Main registry operations
    # ─────────────────────────────────────────────────────────────

    async def get_registry(
        self,
        team_id: str,
        force_refresh: bool = False,
    ) -> TeamRegistry:
        """Get or create a registry for a team.

        Attempts to load from cache, then local storage, then remote.
        Creates a new empty registry if none exists.

        Args:
            team_id: Team ID
            force_refresh: If True, bypass cache and reload

        Returns:
            TeamRegistry for the team
        """
        # Check cache first
        if not force_refresh and team_id in self._cache:
            return self._cache[team_id]

        # Try local storage
        registry = self._load_local(team_id)

        # Try remote if local doesn't exist and provider is configured
        if registry is None and self.remote_provider is not None:
            try:
                remote_data = await self._load_remote(team_id)
                if remote_data:
                    registry = TeamRegistry.from_dict(remote_data)
                    # Save locally for offline access
                    self._save_local(registry)
            except Exception as e:
                logger.warning(f"Failed to load remote registry for {team_id}: {e}")

        # Create new if doesn't exist
        if registry is None:
            registry = TeamRegistry(team_id=team_id)

        # Update cache
        self._cache[team_id] = registry
        return registry

    async def save_registry(
        self,
        registry: TeamRegistry,
        sync_remote: bool = True,
    ) -> bool:
        """Save a registry to local and optionally remote storage.

        Args:
            registry: Registry to save
            sync_remote: If True, also sync to remote provider

        Returns:
            True if save succeeded
        """
        # Save locally
        if not self._save_local(registry):
            return False

        # Update cache
        self._cache[registry.team_id] = registry

        # Sync to remote if configured
        if sync_remote and self.remote_provider is not None:
            try:
                await self._save_remote(registry)
            except Exception as e:
                logger.warning(f"Failed to sync registry to remote: {e}")
                # Local save succeeded, so return True but log warning

        return True

    async def delete_registry(self, team_id: str) -> bool:
        """Delete a registry entirely.

        Args:
            team_id: Team ID

        Returns:
            True if deletion succeeded
        """
        # Delete locally
        if not self._delete_local(team_id):
            return False

        # Remove from cache
        self._cache.pop(team_id, None)

        # Delete from remote
        if self.remote_provider is not None:
            try:
                await self._delete_remote(team_id)
            except Exception as e:
                logger.warning(f"Failed to delete remote registry: {e}")

        return True

    # ─────────────────────────────────────────────────────────────
    # Remote operations
    # ─────────────────────────────────────────────────────────────

    async def _load_remote(self, team_id: str) -> Optional[dict[str, Any]]:
        """Load registry from remote provider."""
        if self.remote_provider is None:
            return None

        # Check if provider has registry support
        if hasattr(self.remote_provider, "get_registry"):
            return await self.remote_provider.get_registry(team_id)
        return None

    async def _save_remote(self, registry: TeamRegistry) -> bool:
        """Save registry to remote provider."""
        if self.remote_provider is None:
            return False

        if hasattr(self.remote_provider, "save_registry"):
            return await self.remote_provider.save_registry(
                registry.team_id,
                registry.to_dict(),
            )
        return False

    async def _delete_remote(self, team_id: str) -> bool:
        """Delete registry from remote provider."""
        if self.remote_provider is None:
            return False

        if hasattr(self.remote_provider, "delete_registry"):
            return await self.remote_provider.delete_registry(team_id)
        return False

    # ─────────────────────────────────────────────────────────────
    # Sync operations
    # ─────────────────────────────────────────────────────────────

    async def sync_registry(
        self,
        team_id: str,
        strategy: str = "remote_wins",
    ) -> TeamRegistry:
        """Sync registry between local and remote.

        Args:
            team_id: Team ID
            strategy: Conflict resolution strategy:
                - "remote_wins": Remote version takes precedence
                - "local_wins": Local version takes precedence
                - "merge": Merge both (may result in duplicates)

        Returns:
            Synced TeamRegistry
        """
        local = self._load_local(team_id)
        remote_data = await self._load_remote(team_id) if self.remote_provider else None
        remote = TeamRegistry.from_dict(remote_data) if remote_data else None

        # No conflict if one is missing
        if local is None and remote is None:
            return TeamRegistry(team_id=team_id)
        if local is None:
            self._save_local(remote)
            self._cache[team_id] = remote
            return remote
        if remote is None:
            await self._save_remote(local)
            self._cache[team_id] = local
            return local

        # Both exist - resolve conflict
        if strategy == "remote_wins":
            result = remote
        elif strategy == "local_wins":
            result = local
        elif strategy == "merge":
            result = self._merge_registries(local, remote)
        else:
            # Default to remote wins
            result = remote

        # Save result to both
        self._save_local(result)
        if self.remote_provider:
            await self._save_remote(result)
        self._cache[team_id] = result

        return result

    def _merge_registries(
        self,
        local: TeamRegistry,
        remote: TeamRegistry,
    ) -> TeamRegistry:
        """Merge two registries, keeping unique items from both.

        Uses item IDs to detect duplicates. Items with the same ID
        take the version with the later updated_at timestamp.
        """
        merged = TeamRegistry(team_id=local.team_id)
        merged.version = max(local.version, remote.version) + 1

        # Merge rules
        rules_by_id: dict[str, Rule] = {}
        for rule in local.rules + remote.rules:
            if rule.rule_id not in rules_by_id:
                rules_by_id[rule.rule_id] = rule
            else:
                existing = rules_by_id[rule.rule_id]
                if rule.updated_at > existing.updated_at:
                    rules_by_id[rule.rule_id] = rule
        merged.rules = list(rules_by_id.values())

        # Merge agents
        agents_by_id: dict[str, AgentConfig] = {}
        for agent in local.agents + remote.agents:
            if agent.agent_id not in agents_by_id:
                agents_by_id[agent.agent_id] = agent
            else:
                existing = agents_by_id[agent.agent_id]
                if agent.updated_at > existing.updated_at:
                    agents_by_id[agent.agent_id] = agent
        merged.agents = list(agents_by_id.values())

        # Merge MCPs
        mcps_by_id: dict[str, MCPConfig] = {}
        for mcp in local.mcps + remote.mcps:
            if mcp.mcp_id not in mcps_by_id:
                mcps_by_id[mcp.mcp_id] = mcp
            else:
                existing = mcps_by_id[mcp.mcp_id]
                if mcp.updated_at > existing.updated_at:
                    mcps_by_id[mcp.mcp_id] = mcp
        merged.mcps = list(mcps_by_id.values())

        # Merge skills
        skills_by_id: dict[str, Skill] = {}
        for skill in local.skills + remote.skills:
            if skill.skill_id not in skills_by_id:
                skills_by_id[skill.skill_id] = skill
            else:
                existing = skills_by_id[skill.skill_id]
                if skill.updated_at > existing.updated_at:
                    skills_by_id[skill.skill_id] = skill
        merged.skills = list(skills_by_id.values())

        return merged

    # ─────────────────────────────────────────────────────────────
    # Convenience methods for individual items
    # ─────────────────────────────────────────────────────────────

    async def add_rule(
        self,
        team_id: str,
        rule: Rule,
        sync_remote: bool = True,
    ) -> bool:
        """Add a rule to a team's registry."""
        registry = await self.get_registry(team_id)
        registry.add_rule(rule)
        return await self.save_registry(registry, sync_remote)

    async def update_rule(
        self,
        team_id: str,
        rule: Rule,
        sync_remote: bool = True,
    ) -> bool:
        """Update a rule in a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.update_rule(rule):
            return False
        return await self.save_registry(registry, sync_remote)

    async def remove_rule(
        self,
        team_id: str,
        rule_id: str,
        sync_remote: bool = True,
    ) -> bool:
        """Remove a rule from a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.remove_rule(rule_id):
            return False
        return await self.save_registry(registry, sync_remote)

    async def add_agent(
        self,
        team_id: str,
        agent: AgentConfig,
        sync_remote: bool = True,
    ) -> bool:
        """Add an agent config to a team's registry."""
        registry = await self.get_registry(team_id)
        registry.add_agent(agent)
        return await self.save_registry(registry, sync_remote)

    async def update_agent(
        self,
        team_id: str,
        agent: AgentConfig,
        sync_remote: bool = True,
    ) -> bool:
        """Update an agent config in a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.update_agent(agent):
            return False
        return await self.save_registry(registry, sync_remote)

    async def remove_agent(
        self,
        team_id: str,
        agent_id: str,
        sync_remote: bool = True,
    ) -> bool:
        """Remove an agent config from a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.remove_agent(agent_id):
            return False
        return await self.save_registry(registry, sync_remote)

    async def add_mcp(
        self,
        team_id: str,
        mcp: MCPConfig,
        sync_remote: bool = True,
    ) -> bool:
        """Add an MCP config to a team's registry."""
        registry = await self.get_registry(team_id)
        registry.add_mcp(mcp)
        return await self.save_registry(registry, sync_remote)

    async def update_mcp(
        self,
        team_id: str,
        mcp: MCPConfig,
        sync_remote: bool = True,
    ) -> bool:
        """Update an MCP config in a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.update_mcp(mcp):
            return False
        return await self.save_registry(registry, sync_remote)

    async def remove_mcp(
        self,
        team_id: str,
        mcp_id: str,
        sync_remote: bool = True,
    ) -> bool:
        """Remove an MCP config from a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.remove_mcp(mcp_id):
            return False
        return await self.save_registry(registry, sync_remote)

    async def add_skill(
        self,
        team_id: str,
        skill: Skill,
        sync_remote: bool = True,
    ) -> bool:
        """Add a skill to a team's registry."""
        registry = await self.get_registry(team_id)
        registry.add_skill(skill)
        return await self.save_registry(registry, sync_remote)

    async def update_skill(
        self,
        team_id: str,
        skill: Skill,
        sync_remote: bool = True,
    ) -> bool:
        """Update a skill in a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.update_skill(skill):
            return False
        return await self.save_registry(registry, sync_remote)

    async def remove_skill(
        self,
        team_id: str,
        skill_id: str,
        sync_remote: bool = True,
    ) -> bool:
        """Remove a skill from a team's registry."""
        registry = await self.get_registry(team_id)
        if not registry.remove_skill(skill_id):
            return False
        return await self.save_registry(registry, sync_remote)

    # ─────────────────────────────────────────────────────────────
    # Bulk operations
    # ─────────────────────────────────────────────────────────────

    async def import_registry(
        self,
        team_id: str,
        data: dict[str, Any],
        merge: bool = True,
    ) -> TeamRegistry:
        """Import registry data from a dict (e.g., from JSON file).

        Args:
            team_id: Team ID
            data: Registry data dict
            merge: If True, merge with existing; if False, replace

        Returns:
            Updated TeamRegistry
        """
        imported = TeamRegistry.from_dict({"team_id": team_id, **data})

        if merge:
            existing = await self.get_registry(team_id)
            registry = self._merge_registries(existing, imported)
        else:
            registry = imported

        await self.save_registry(registry)
        return registry

    async def export_registry(self, team_id: str) -> dict[str, Any]:
        """Export registry to a dict (e.g., for JSON file).

        Args:
            team_id: Team ID

        Returns:
            Registry data dict
        """
        registry = await self.get_registry(team_id)
        return registry.to_dict()

    def clear_cache(self, team_id: Optional[str] = None) -> None:
        """Clear the registry cache.

        Args:
            team_id: If provided, only clear that team's cache
        """
        if team_id:
            self._cache.pop(team_id, None)
        else:
            self._cache.clear()
