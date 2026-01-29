from typing import List

from .base import SocketInstance
from ..core.client import MinecraftClient
from ..types import ServerInfo, MemoryUsage, CommandResult


class Server(SocketInstance):
    """Server object for server management.

    This class provides methods to manage server properties, execute commands,
    monitor performance, and control server settings.
    """

    def __init__(self, client: MinecraftClient):
        super().__init__("server", client)

    async def getInfo(self) -> ServerInfo:
        """Get server information."""
        data = await super().__getattr__("getInfo")()
        return ServerInfo(**data)

    async def getVersion(self) -> str:
        """Get server version."""
        return await super().__getattr__("getVersion")()

    async def getBrand(self) -> str:
        """Get server brand."""
        return await super().__getattr__("getBrand")()

    async def getMotd(self) -> str:
        """Get server MOTD."""
        return await super().__getattr__("getMotd")()

    async def getMaxPlayers(self) -> int:
        """Get maximum player count."""
        return await super().__getattr__("getMaxPlayers")()

    async def getOnlinePlayerCount(self) -> int:
        """Get online player count."""
        return await super().__getattr__("getOnlinePlayerCount")()

    async def getOnlinePlayers(self) -> List[str]:
        """Get list of online player names."""
        return await super().__getattr__("getOnlinePlayers")()

    async def getOnlinePlayerUUIDs(self) -> List[str]:
        """Get list of online player UUIDs."""
        return await super().__getattr__("getOnlinePlayerUUIDs")()

    async def getTPS(self) -> float:
        """Get server TPS (ticks per second)."""
        return await super().__getattr__("getTPS")()

    async def getUptime(self) -> float:
        """Get server uptime (milliseconds)."""
        return await super().__getattr__("getUptime")()

    async def getMemoryUsage(self) -> MemoryUsage:
        """Get server memory usage."""
        data = await super().__getattr__("getMemoryUsage")()
        return MemoryUsage(**data)

    async def getDifficulty(self) -> str:
        """Get server difficulty.

        Examples:
            >>> difficulty = await server.getDifficulty()
            >>> print(f"Server difficulty: {difficulty}")

        Returns:
            Difficulty as string ("peaceful", "easy", "normal", "hard")
        """
        return await super().__getattr__("getDifficulty")()

    async def setDifficulty(self, difficulty: str) -> bool:
        """Set server difficulty.

        Args:
            difficulty: Difficulty level to set

        Examples:
            >>> await server.setDifficulty("peaceful")
            >>> await server.setDifficulty("easy")
            >>> await server.setDifficulty("normal")
            >>> await server.setDifficulty("hard")

        Valid difficulty levels:
            - "peaceful" - Peaceful (no hostile mobs, health regenerates)
            - "easy" - Easy (less damage from mobs)
            - "normal" - Normal (standard difficulty)
            - "hard" - Hard (more damage, additional challenges)

        Returns:
            True if difficulty was set successfully
        """
        return await super().__getattr__("setDifficulty")(difficulty)

    async def isHardcore(self) -> bool:
        """Check if server is in hardcore mode.

        Examples:
            >>> is_hardcore = await server.isHardcore()
            >>> print(f"Hardcore mode: {is_hardcore}")

        Returns:
            True if server is in hardcore mode
        """
        return await super().__getattr__("isHardcore")()

    async def getDefaultGameMode(self) -> str:
        """Get default game mode.

        Examples:
            >>> mode = await server.getDefaultGameMode()
            >>> print(f"Default game mode: {mode}")

        Returns:
            Game mode as string ("survival", "creative", "adventure", "spectator")
        """
        return await super().__getattr__("getDefaultGameMode")()

    async def setDefaultGameMode(self, gamemode: str) -> bool:
        """Set default game mode.

        Args:
            gamemode: Game mode to set as default

        Examples:
            >>> await server.setDefaultGameMode("survival")
            >>> await server.setDefaultGameMode("creative")
            >>> await server.setDefaultGameMode("adventure")
            >>> await server.setDefaultGameMode("spectator")

        Valid game modes:
            - "survival" - Survival mode (default)
            - "creative" - Creative mode
            - "adventure" - Adventure mode
            - "spectator" - Spectator mode

        Returns:
            True if default game mode was set successfully
        """
        return await super().__getattr__("setDefaultGameMode")(gamemode)

    async def executeCommand(self, command: str) -> CommandResult:
        """Execute server command."""
        data = await super().__getattr__("executeCommand")(command)
        return CommandResult(**data)

    async def broadcast(self, message: str) -> bool:
        """Broadcast message to all players."""
        return await super().__getattr__("broadcast")(message)

    async def save(self) -> bool:
        """Save all worlds."""
        return await super().__getattr__("save")()

    async def stop(self) -> bool:
        """Stop the server."""
        return await super().__getattr__("stop")()

    async def getWhitelist(self) -> List[str]:
        """Get whitelist."""
        return await super().__getattr__("getWhitelist")()

    async def isWhitelistEnabled(self) -> bool:
        """Check if whitelist is enabled."""
        return await super().__getattr__("isWhitelistEnabled")()

    async def setWhitelistEnabled(self, enabled: bool) -> bool:
        """Enable or disable whitelist."""
        return await super().__getattr__("setWhitelistEnabled")(enabled)

    async def getOperators(self) -> List[str]:
        """Get list of operators."""
        return await super().__getattr__("getOperators")()

    async def getBannedPlayers(self) -> List[str]:
        """Get list of banned players."""
        return await super().__getattr__("getBannedPlayers")()

    async def getBannedIPs(self) -> List[str]:
        """Get list of banned IPs."""
        return await super().__getattr__("getBannedIPs")()
