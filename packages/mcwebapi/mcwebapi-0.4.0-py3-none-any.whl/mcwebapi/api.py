import asyncio
from typing import Optional

from .core import MinecraftClient
from .objects import Player, Level, Command, Block, Server, Entity, Scoreboard

from .events.manager import EventManager

class MinecraftAPI:
    """
    High-level async API client for Minecraft WebSocket API.

    Provides easy access to various entities (player, world, command, system)
    with a clean, intuitive async/await interface.

    Example:
        async with MinecraftAPI() as api:
            player = api.Player("Steve")
            health = await player.getHealth()
            print(f"Health: {health}")
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 8765,
            auth_key: str = "default-secret-key-change-me",
            timeout: float = 10.0,
    ):
        self.client = MinecraftClient(host, port, auth_key, timeout)
        self.timeout = timeout
        self._event_manager: Optional[EventManager] = None

    async def connect(self) -> None:
        """Connect to the Minecraft server."""
        await self.client.connect()

    async def disconnect(self) -> None:
        """Disconnect from the Minecraft server."""
        await self.client.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self.client.is_connected()

    def is_authenticated(self) -> bool:
        """Check if authenticated with server."""
        return self.client.is_authenticated()

    async def wait_for_pending(self) -> None:
        """Wait for all pending requests to complete."""
        while self.client.has_pending_requests():
            await asyncio.sleep(0.1)

    async def __aenter__(self) -> "MinecraftAPI":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Wait for all requests to complete before disconnecting"""
        await self.wait_for_pending()
        await self.disconnect()

    def Player(self, identifier: str) -> Player:
        """Create a Player instance."""
        return Player(self.client, identifier)

    def Level(self, identifier: str) -> Level:
        """Create a Level instance."""
        return Level(self.client, identifier)

    def Block(self, level_id: str) -> Block:
        """Create a Block instance."""
        return Block(self.client, level_id)

    def Server(self) -> Server:
        """Create a Server instance."""
        return Server(self.client)

    def Entity(self, level_id: str) -> Entity:
        """Create an Entity instance."""
        return Entity(self.client, level_id)

    def Scoreboard(self) -> Scoreboard:
        """Create a Scoreboard instance."""
        return Scoreboard(self.client)

    def Command(self) -> Command:
        """Create a Command instance."""
        return Command(self.client)

    def events(self) -> EventManager:
        """
        Get or create the EventManager for handling game events.

        The EventManager allows you to subscribe to Minecraft events
        using decorators and handle them asynchronously.

        Returns:
            EventManager instance for this API connection

        Example:
            @PlayerChatEvent
            async def on_chat(event):
                print(f"{event.player_name}: {event.message}")

            async with MinecraftAPI() as api:
                events = api.events()
                await events.start()
        """
        if self._event_manager is None:
            from .events.manager import EventManager
            self._event_manager = EventManager(self.client)
            self.client.set_event_manager(self._event_manager)
        return self._event_manager
