from typing import List

from .base import SocketInstance
from ..core.client import MinecraftClient
from ..types import (
    BlockState, Weather, WorldBorder, SpawnPoint,
    LevelData, ChunkInfo, LevelInfo
)


class Level(SocketInstance):
    """Level object for interacting with world-related operations.

    This class provides methods to manage world/dimension properties including blocks,
    time, weather, world border, spawn point, and other level-specific settings.
    """

    def __init__(self, client: MinecraftClient, identifier: str):
        super().__init__("level", client, identifier)

    async def setBlock(self, block_id: str, x: int, y: int, z: int) -> bool:
        """Set block at coordinates.

        Args:
            block_id: Namespaced ID of the block
            x: X coordinate
            y: Y coordinate
            z: Z coordinate

        Examples:
            >>> await level.setBlock("minecraft:diamond_block", 10, 64, 20)
            >>> await level.setBlock("minecraft:stone", 0, 0, 0)

        Common block IDs:
            - "minecraft:diamond_block", "minecraft:gold_block", "minecraft:iron_block"
            - "minecraft:stone", "minecraft:grass_block", "minecraft:dirt"
            - "minecraft:oak_log", "minecraft:oak_planks"

        Returns:
            True if block was set successfully
        """
        return await super().__getattr__("setBlock")(block_id, x, y, z)

    async def getBlock(self, x: int, y: int, z: int) -> str:
        """Get block type at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate

        Examples:
            >>> block_type = await level.getBlock(10, 64, 20)
            >>> print(f"Block at position: {block_type}")

        Returns:
            Namespaced ID of the block (e.g., "minecraft:stone")
        """
        return await super().__getattr__("getBlock")(x, y, z)

    async def getBlockState(self, x: int, y: int, z: int) -> BlockState:
        """Get detailed block state.

        Retrieves block type and properties (like facing direction, waterlogged, etc.).

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate

        Examples:
            >>> state = await level.getBlockState(10, 64, 20)
            >>> print(f"Block: {state.type}, Properties: {state.properties}")

        Returns:
            BlockState object with type and properties
        """
        data = await super().__getattr__("getBlockState")(x, y, z)
        return BlockState(**data)

    async def getDayTime(self) -> int:
        """Get world day time.

        Examples:
            >>> time = await level.getDayTime()
            >>> print(f"Current time: {time} ticks")

        Time values:
            - 0 = Dawn
            - 6000 = Noon
            - 12000 = Dusk
            - 18000 = Midnight
            - 24000 = Next day (wraps to 0)

        Returns:
            Current time in ticks (0-23999)
        """
        return await super().__getattr__("getDayTime")()

    async def setDayTime(self, time: int) -> bool:
        """Set world day time.

        Args:
            time: Time in ticks (0-23999)

        Examples:
            >>> await level.setDayTime(0)  # Set to dawn
            >>> await level.setDayTime(6000)  # Set to noon
            >>> await level.setDayTime(12000)  # Set to dusk
            >>> await level.setDayTime(18000)  # Set to midnight

        Time values:
            - 0 = Dawn (sunrise)
            - 6000 = Noon (midday)
            - 12000 = Dusk (sunset)
            - 18000 = Midnight

        Returns:
            True if time was set successfully
        """
        return await super().__getattr__("setDayTime")(time)

    async def getSeed(self) -> int:
        """Get world seed.

        Examples:
            >>> seed = await level.getSeed()
            >>> print(f"World seed: {seed}")

        Returns:
            World generation seed as integer
        """
        return await super().__getattr__("getSeed")()

    async def getWeather(self) -> Weather:
        """Get weather information.

        Examples:
            >>> weather = await level.getWeather()
            >>> print(f"Raining: {weather.raining}, Thunder: {weather.thundering}")

        Returns:
            Weather object with rain and thunder status
        """
        data = await super().__getattr__("getWeather")()
        return Weather(**data)

    async def setWeather(self, raining: bool, thundering: bool) -> bool:
        """Set weather.

        Args:
            raining: True to enable rain, False to clear
            thundering: True to enable thunder, False to disable

        Examples:
            >>> await level.setWeather(True, False)  # Rain without thunder
            >>> await level.setWeather(True, True)  # Thunderstorm
            >>> await level.setWeather(False, False)  # Clear weather

        Note:
            Thunder requires rain to be enabled (thundering=True with raining=False has no effect)

        Returns:
            True if weather was set successfully
        """
        return await super().__getattr__("setWeather")(raining, thundering)

    async def getWorldBorder(self) -> WorldBorder:
        """Get world border information."""
        data = await super().__getattr__("getWorldBorder")()
        return WorldBorder(**data)

    async def setWorldBorder(self, center_x: float, center_z: float, size: float) -> bool:
        """Set world border."""
        return await super().__getattr__("setWorldBorder")(center_x, center_z, size)

    async def getHeight(self, x: int, z: int, heightmap_type: str) -> int:
        """Get height at coordinates.

        Gets the Y coordinate of the highest block at the given X, Z position
        based on the specified heightmap type.

        Args:
            x: X coordinate
            z: Z coordinate
            heightmap_type: Type of heightmap to use

        Examples:
            >>> height = await level.getHeight(10, 20, "MOTION_BLOCKING")
            >>> height = await level.getHeight(0, 0, "WORLD_SURFACE")

        Heightmap types:
            - "MOTION_BLOCKING" - Highest block that blocks motion or contains a fluid
            - "MOTION_BLOCKING_NO_LEAVES" - Like MOTION_BLOCKING but ignoring leaves
            - "OCEAN_FLOOR" - Highest solid block
            - "WORLD_SURFACE" - Highest non-air block

        Returns:
            Y coordinate of the highest block
        """
        return await super().__getattr__("getHeight")(x, z, heightmap_type)

    async def getSpawnPoint(self) -> SpawnPoint:
        """Get world spawn point.

        Examples:
            >>> spawn = await level.getSpawnPoint()
            >>> print(f"Spawn at x={spawn.x}, y={spawn.y}, z={spawn.z}, angle={spawn.angle}")

        Returns:
            SpawnPoint object with coordinates and angle
        """
        data = await super().__getattr__("getSpawnPoint")()
        return SpawnPoint(**data)

    async def setSpawnPoint(self, x: int, y: int, z: int, angle: float) -> bool:
        """Set world spawn point.

        Args:
            x: X coordinate of spawn point
            y: Y coordinate of spawn point
            z: Z coordinate of spawn point
            angle: Spawn angle in degrees (0-360)

        Examples:
            >>> await level.setSpawnPoint(0, 64, 0, 0.0)  # Spawn at origin facing north
            >>> await level.setSpawnPoint(100, 70, 100, 180.0)  # Spawn facing south

        Returns:
            True if spawn point was set successfully
        """
        return await super().__getattr__("setSpawnPoint")(x, y, z, angle)

    async def getDifficulty(self) -> str:
        """Get world difficulty.

        Examples:
            >>> difficulty = await level.getDifficulty()
            >>> print(f"Difficulty: {difficulty}")

        Returns:
            Difficulty as string ("peaceful", "easy", "normal", "hard")
        """
        return await super().__getattr__("getDifficulty")()

    async def setDifficulty(self, difficulty: str) -> bool:
        """Set world difficulty.

        Args:
            difficulty: Difficulty level to set

        Examples:
            >>> await level.setDifficulty("peaceful")
            >>> await level.setDifficulty("easy")
            >>> await level.setDifficulty("normal")
            >>> await level.setDifficulty("hard")

        Valid difficulty levels:
            - "peaceful" - Peaceful (no hostile mobs, health regenerates)
            - "easy" - Easy (less damage from mobs)
            - "normal" - Normal (standard difficulty)
            - "hard" - Hard (more damage, additional challenges)

        Returns:
            True if difficulty was set successfully
        """
        return await super().__getattr__("setDifficulty")(difficulty)

    async def getPlayers(self) -> List[str]:
        """Get list of players in world."""
        return await super().__getattr__("getPlayers")()

    async def getEntities(self) -> List[str]:
        """Get list of entities in world."""
        return await super().__getattr__("getEntities")()

    async def getEntityCount(self) -> int:
        """Get entity count in world."""
        return await super().__getattr__("getEntityCount")()

    async def getPlayerCount(self) -> int:
        """Get player count in world."""
        return await super().__getattr__("getPlayerCount")()

    async def getChunkInfo(self, chunk_x: int, chunk_z: int) -> ChunkInfo:
        """Get chunk information."""
        data = await super().__getattr__("getChunkInfo")(chunk_x, chunk_z)
        return ChunkInfo(**data)

    async def loadChunk(self, chunk_x: int, chunk_z: int) -> bool:
        """Load chunk in the world."""
        return await super().__getattr__("loadChunk")(chunk_x, chunk_z)

    async def unloadChunk(self, chunk_x: int, chunk_z: int) -> bool:
        """Unload chunk in the world."""
        return await super().__getattr__("unloadChunk")(chunk_x, chunk_z)

    async def getLightLevel(self, x: int, y: int, z: int) -> int:
        """Get light level at coordinates."""
        return await super().__getattr__("getLightLevel")(x, y, z)

    async def getMoonPhase(self) -> int:
        """Get moon phase."""
        return await super().__getattr__("getMoonPhase")()

    async def isDay(self) -> bool:
        """Check if it's daytime."""
        return await super().__getattr__("isDay")()

    async def isNight(self) -> bool:
        """Check if it's nighttime."""
        return await super().__getattr__("isNight")()

    async def getTotalTime(self) -> float:
        """Get total time."""
        return await super().__getattr__("getTotalTime")()

    async def getLevelData(self) -> LevelData:
        """Get level metadata."""
        data = await super().__getattr__("getLevelData")()
        return LevelData(**data)

    async def sendMessageToAll(self, message: str) -> bool:
        """Send message to all entities."""
        return await super().__getattr__("sendMessageToAll")(message)

    async def explode(self, x: float, y: float, z: float, power: float, fire: bool) -> bool:
        """Create explosion at coordinates."""
        return await super().__getattr__("explode")(x, y, z, power, fire)

    async def getAvailableLevels(self):
        """Get available levels."""
        return await super().__getattr__("getAvailableLevels")()

    async def getLevelInfo(self) -> LevelInfo:
        """Get complete level information."""
        data = await super().__getattr__("getLevelInfo")()
        return LevelInfo(**data)
