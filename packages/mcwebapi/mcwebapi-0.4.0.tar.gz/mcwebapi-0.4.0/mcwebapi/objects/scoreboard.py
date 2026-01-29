from typing import List, Dict, Optional

from .base import SocketInstance
from ..core.client import MinecraftClient
from ..types import ObjectiveInfo, TeamInfo


class Scoreboard(SocketInstance):
    """Scoreboard object for scoreboard management.

    This class provides methods to manage scoreboards including objectives,
    teams, scores, and display settings.
    """

    def __init__(self, client: MinecraftClient):
        super().__init__("scoreboard", client)

    # Objectives
    async def createObjective(self, name: str, criteria_id: str, display_name: str) -> bool:
        """Create scoreboard objective.

        Args:
            name: Internal name of the objective (no spaces)
            criteria_id: Criteria type ID
            display_name: Display name shown to players (can include colors)

        Examples:
            >>> await scoreboard.createObjective("kills", "playerKillCount", "Total Kills")
            >>> await scoreboard.createObjective("deaths", "deathCount", "§cDeaths")
            >>> await scoreboard.createObjective("health", "health", "❤ Health")

        Common criteria IDs:
            - "dummy" - Manual score tracking
            - "playerKillCount" - Player kills
            - "deathCount" - Deaths
            - "totalKillCount" - Total kills (mobs + players)
            - "health" - Current health (0-20)
            - "xp" - Experience points
            - "level" - Experience level
            - "food" - Food level
            - "air" - Air level (underwater)
            - "armor" - Armor points

        Returns:
            True if objective was created successfully
        """
        return await super().__getattr__("createObjective")(name, criteria_id, display_name)

    async def removeObjective(self, name: str) -> bool:
        """Remove scoreboard objective.

        Args:
            name: Name of the objective to remove

        Examples:
            >>> await scoreboard.removeObjective("kills")

        Returns:
            True if objective was removed successfully
        """
        return await super().__getattr__("removeObjective")(name)

    async def getObjectives(self) -> List[ObjectiveInfo]:
        """Get all objectives.

        Examples:
            >>> objectives = await scoreboard.getObjectives()
            >>> for obj in objectives:
            ...     print(f"{obj.name}: {obj.display_name}")

        Returns:
            List of ObjectiveInfo objects
        """
        data = await super().__getattr__("getObjectives")()
        return [ObjectiveInfo(**obj) for obj in data]

    async def getObjective(self, name: str) -> ObjectiveInfo:
        """Get objective information.

        Args:
            name: Name of the objective

        Examples:
            >>> obj = await scoreboard.getObjective("kills")
            >>> print(f"Display: {obj.display_name}, Criteria: {obj.criteria}")

        Returns:
            ObjectiveInfo object with objective details
        """
        data = await super().__getattr__("getObjective")(name)
        return ObjectiveInfo(**data)

    async def setDisplaySlot(self, slot: str, objective_name: Optional[str]) -> bool:
        """Set objective display slot.

        Args:
            slot: Display slot name
            objective_name: Name of objective to display (None to clear)

        Examples:
            >>> await scoreboard.setDisplaySlot("sidebar", "kills")
            >>> await scoreboard.setDisplaySlot("belowName", "health")
            >>> await scoreboard.setDisplaySlot("list", "deaths")
            >>> await scoreboard.setDisplaySlot("sidebar", None)  # Clear sidebar

        Valid display slots:
            - "sidebar" - Right side of screen
            - "list" - Player list (Tab menu)
            - "belowName" - Below player names

        Returns:
            True if display slot was set successfully
        """
        return await super().__getattr__("setDisplaySlot")(slot, objective_name)

    async def getDisplaySlots(self) -> Dict[str, Optional[str]]:
        """Get all display slots."""
        return await super().__getattr__("getDisplaySlots")()

    # Teams
    async def createTeam(self, name: str) -> bool:
        """Create team.

        Args:
            name: Internal name of the team

        Examples:
            >>> await scoreboard.createTeam("red_team")
            >>> await scoreboard.createTeam("blue_team")

        Returns:
            True if team was created successfully
        """
        return await super().__getattr__("createTeam")(name)

    async def removeTeam(self, name: str) -> bool:
        """Remove team.

        Args:
            name: Name of the team to remove

        Examples:
            >>> await scoreboard.removeTeam("red_team")

        Returns:
            True if team was removed successfully
        """
        return await super().__getattr__("removeTeam")(name)

    async def getTeams(self) -> List[TeamInfo]:
        """Get all teams.

        Examples:
            >>> teams = await scoreboard.getTeams()
            >>> for team in teams:
            ...     print(f"{team.name}: {len(team.members)} members")

        Returns:
            List of TeamInfo objects
        """
        data = await super().__getattr__("getTeams")()
        return [TeamInfo(**team) for team in data]

    async def getTeam(self, name: str) -> TeamInfo:
        """Get team information.

        Args:
            name: Name of the team

        Examples:
            >>> team = await scoreboard.getTeam("red_team")
            >>> print(f"Color: {team.color}, Members: {team.members}")

        Returns:
            TeamInfo object with team details
        """
        data = await super().__getattr__("getTeam")(name)
        return TeamInfo(**data)

    async def addPlayerToTeam(self, team_name: str, player_name: str) -> bool:
        """Add player to team.

        Args:
            team_name: Name of the team
            player_name: Name of the player to add

        Examples:
            >>> await scoreboard.addPlayerToTeam("red_team", "Steve")
            >>> await scoreboard.addPlayerToTeam("blue_team", "Alex")

        Returns:
            True if player was added successfully
        """
        return await super().__getattr__("addPlayerToTeam")(team_name, player_name)

    async def removePlayerFromTeam(self, player_name: str) -> bool:
        """Remove player from team.

        Args:
            player_name: Name of the player to remove from their current team

        Examples:
            >>> await scoreboard.removePlayerFromTeam("Steve")

        Returns:
            True if player was removed successfully
        """
        return await super().__getattr__("removePlayerFromTeam")(player_name)

    async def setTeamDisplayName(self, team_name: str, display_name: str) -> bool:
        """Set team display name.

        Args:
            team_name: Name of the team
            display_name: Display name (can include color codes)

        Examples:
            >>> await scoreboard.setTeamDisplayName("red_team", "§cRed Team")
            >>> await scoreboard.setTeamDisplayName("blue_team", "§9Blue Team")

        Returns:
            True if display name was set successfully
        """
        return await super().__getattr__("setTeamDisplayName")(team_name, display_name)

    async def setTeamColor(self, team_name: str, color: str) -> bool:
        """Set team color.

        Args:
            team_name: Name of the team
            color: Color name

        Examples:
            >>> await scoreboard.setTeamColor("red_team", "red")
            >>> await scoreboard.setTeamColor("blue_team", "blue")
            >>> await scoreboard.setTeamColor("green_team", "green")

        Valid colors:
            - "black", "dark_blue", "dark_green", "dark_aqua"
            - "dark_red", "dark_purple", "gold", "gray"
            - "dark_gray", "blue", "green", "aqua"
            - "red", "light_purple", "yellow", "white"

        Returns:
            True if color was set successfully
        """
        return await super().__getattr__("setTeamColor")(team_name, color)

    async def setTeamPrefix(self, team_name: str, prefix: str) -> bool:
        """Set team prefix.

        The prefix is displayed before player names.

        Args:
            team_name: Name of the team
            prefix: Prefix text (can include color codes)

        Examples:
            >>> await scoreboard.setTeamPrefix("red_team", "§c[RED] ")
            >>> await scoreboard.setTeamPrefix("vip_team", "§6[VIP] ")

        Returns:
            True if prefix was set successfully
        """
        return await super().__getattr__("setTeamPrefix")(team_name, prefix)

    async def setTeamSuffix(self, team_name: str, suffix: str) -> bool:
        """Set team suffix.

        The suffix is displayed after player names.

        Args:
            team_name: Name of the team
            suffix: Suffix text (can include color codes)

        Examples:
            >>> await scoreboard.setTeamSuffix("admin_team", " §7[Admin]")
            >>> await scoreboard.setTeamSuffix("mod_team", " §a[Mod]")

        Returns:
            True if suffix was set successfully
        """
        return await super().__getattr__("setTeamSuffix")(team_name, suffix)

    async def setTeamFriendlyFire(self, team_name: str, enabled: bool) -> bool:
        """Set team friendly fire setting.

        Controls whether team members can damage each other.

        Args:
            team_name: Name of the team
            enabled: True to allow friendly fire, False to prevent it

        Examples:
            >>> await scoreboard.setTeamFriendlyFire("red_team", False)  # Prevent friendly fire
            >>> await scoreboard.setTeamFriendlyFire("pvp_team", True)  # Allow friendly fire

        Returns:
            True if setting was changed successfully
        """
        return await super().__getattr__("setTeamFriendlyFire")(team_name, enabled)

    async def setTeamSeeFriendlyInvisibles(self, team_name: str, enabled: bool) -> bool:
        """Set team see friendly invisibles setting.

        Controls whether team members can see invisible teammates.

        Args:
            team_name: Name of the team
            enabled: True to see invisible teammates, False to hide them

        Examples:
            >>> await scoreboard.setTeamSeeFriendlyInvisibles("red_team", True)

        Returns:
            True if setting was changed successfully
        """
        return await super().__getattr__("setTeamSeeFriendlyInvisibles")(team_name, enabled)

    # Scores
    async def getScore(self, objective_name: str, target: str) -> Optional[int]:
        """Get score value."""
        return await super().__getattr__("getScore")(objective_name, target)

    async def setScore(self, objective_name: str, target: str, value: int) -> bool:
        """Set score value."""
        return await super().__getattr__("setScore")(objective_name, target, value)

    async def addScore(self, objective_name: str, target: str, value: int) -> bool:
        """Add to score value."""
        return await super().__getattr__("addScore")(objective_name, target, value)

    async def resetScore(self, objective_name: str, target: str) -> bool:
        """Reset score for objective."""
        return await super().__getattr__("resetScore")(objective_name, target)

    async def resetAllScores(self, target: str) -> bool:
        """Reset all scores for target."""
        return await super().__getattr__("resetAllScores")(target)

    async def getScores(self, target: str) -> Dict[str, int]:
        """Get all scores for target."""
        return await super().__getattr__("getScores")(target)

    async def getObjectiveScores(self, objective_name: str) -> Dict[str, int]:
        """Get all scores for objective."""
        return await super().__getattr__("getObjectiveScores")(objective_name)
