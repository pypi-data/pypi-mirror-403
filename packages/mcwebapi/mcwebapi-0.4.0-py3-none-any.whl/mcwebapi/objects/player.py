from typing import List

from .base import SocketInstance
from ..core.client import MinecraftClient
from ..types import (
    Position, Rotation, Velocity, Experience, ItemStack,
    MobEffect, Advancements, PlayerInfo
)


class Player(SocketInstance):
    """Player object for interacting with player-related operations.

    This class provides methods to manage players, including health, position,
    inventory, effects, experience, and other player-specific attributes.
    """

    def __init__(self, client: MinecraftClient, identifier: str):
        super().__init__("player", client, identifier)

    async def sendMessage(self, message: str) -> bool:
        """Send message to player."""
        return await super().__getattr__("sendMessage")(message)

    async def getHealth(self) -> float:
        """Get player health."""
        return await super().__getattr__("getHealth")()

    async def setHealth(self, health: float) -> bool:
        """Set player health."""
        return await super().__getattr__("setHealth")(health)

    async def getMaxHealth(self) -> float:
        """Get player maximum health."""
        return await super().__getattr__("getMaxHealth")()

    async def getX(self) -> float:
        """Get player X coordinate."""
        return await super().__getattr__("getX")()

    async def getY(self) -> float:
        """Get player Y coordinate."""
        return await super().__getattr__("getY")()

    async def getZ(self) -> float:
        """Get player Z coordinate."""
        return await super().__getattr__("getZ")()

    async def getPosition(self) -> Position:
        """Get player position."""
        data = await super().__getattr__("getPosition")()
        return Position(**data)

    async def teleport(self, x: float, y: float, z: float) -> bool:
        """Teleport player to coordinates.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            z: Target Z coordinate

        Examples:
            >>> await player.teleport(0.0, 64.0, 0.0)  # Teleport to spawn
            >>> await player.teleport(100.5, 70.0, -50.5)

        Returns:
            True if player was teleported successfully
        """
        return await super().__getattr__("teleport")(x, y, z)

    async def teleportTo(self, target_id: str) -> bool:
        """Teleport player to target.

        Args:
            target_id: Username or UUID of target player/entity

        Examples:
            >>> await player.teleportTo("Steve")  # Teleport to player Steve
            >>> await player.teleportTo("550e8400-e29b-41d4-a716-446655440000")  # Teleport to entity UUID

        Returns:
            True if player was teleported successfully
        """
        return await super().__getattr__("teleportTo")(target_id)

    async def teleportToDimension(self, dimension: str, x: float, y: float, z: float) -> bool:
        """Teleport player to dimension.

        Args:
            dimension: Dimension ID to teleport to
            x: Target X coordinate in the dimension
            y: Target Y coordinate in the dimension
            z: Target Z coordinate in the dimension

        Examples:
            >>> await player.teleportToDimension("minecraft:the_nether", 0.0, 64.0, 0.0)
            >>> await player.teleportToDimension("minecraft:the_end", 100.0, 48.0, 0.0)
            >>> await player.teleportToDimension("minecraft:overworld", 0.0, 64.0, 0.0)

        Common dimension IDs:
            - "minecraft:overworld" - The main world
            - "minecraft:the_nether" - The Nether
            - "minecraft:the_end" - The End

        Returns:
            True if player was teleported successfully
        """
        return await super().__getattr__("teleportToDimension")(dimension, x, y, z)

    async def kick(self, reason: str) -> bool:
        """Kick player from server."""
        return await super().__getattr__("kick")(reason)

    async def getFood(self) -> int:
        """Get player food level."""
        return await super().__getattr__("getFood")()

    async def setFood(self, food: int) -> bool:
        """Set player food level."""
        return await super().__getattr__("setFood")(food)

    async def getSaturation(self) -> float:
        """Get player saturation level."""
        return await super().__getattr__("getSaturation")()

    async def setSaturation(self, saturation: float) -> bool:
        """Set player saturation level."""
        return await super().__getattr__("setSaturation")(saturation)

    async def getExperience(self) -> Experience:
        """Get player experience."""
        data = await super().__getattr__("getExperience")()
        return Experience(**data)

    async def setExperience(self, level: int) -> bool:
        """Set player experience."""
        return await super().__getattr__("setExperience")(level)

    async def getGameMode(self) -> str:
        """Get player game mode.

        Examples:
            >>> mode = await player.getGameMode()
            >>> print(f"Current game mode: {mode}")

        Returns:
            Game mode as string (e.g., "survival", "creative", "adventure", "spectator")
        """
        return await super().__getattr__("getGameMode")()

    async def setGameMode(self, gamemode: str) -> bool:
        """Set player game mode.

        Args:
            gamemode: Game mode to set

        Examples:
            >>> await player.setGameMode("creative")
            >>> await player.setGameMode("survival")
            >>> await player.setGameMode("adventure")
            >>> await player.setGameMode("spectator")

        Valid game modes:
            - "survival" - Survival mode
            - "creative" - Creative mode
            - "adventure" - Adventure mode
            - "spectator" - Spectator mode

        Returns:
            True if game mode was set successfully
        """
        return await super().__getattr__("setGameMode")(gamemode)

    async def getInventory(self) -> List[ItemStack]:
        """Get player inventory.

        Retrieves all items in the player's main inventory (excludes armor and offhand).

        Examples:
            >>> inventory = await player.getInventory()
            >>> for item in inventory:
            ...     print(f"Slot {item.slot}: {item.type} x{item.count}")

        Returns:
            List of ItemStack objects representing inventory items
        """
        data = await super().__getattr__("getInventory")()
        return [ItemStack(**item) for item in data]

    async def clearInventory(self) -> bool:
        """Clear player inventory.

        Removes all items from the player's inventory.

        Examples:
            >>> await player.clearInventory()

        Returns:
            True if inventory was cleared successfully
        """
        return await super().__getattr__("clearInventory")()

    async def getEffects(self) -> List[MobEffect]:
        """Get active potion effects.

        Examples:
            >>> effects = await player.getEffects()
            >>> for effect in effects:
            ...     print(f"Effect: {effect.type}, Duration: {effect.duration}, Level: {effect.amplifier + 1}")

        Returns:
            List of MobEffect objects representing active effects
        """
        data = await super().__getattr__("getEffects")()
        return [MobEffect(**effect) for effect in data]

    async def addEffect(self, effect_id: str, duration: int, amplifier: int) -> bool:
        """Add effect to player.

        Args:
            effect_id: Namespaced ID of the effect
            duration: Duration in ticks (20 ticks = 1 second)
            amplifier: Effect level (0 = level I, 1 = level II, etc.)

        Examples:
            >>> await player.addEffect("minecraft:speed", 600, 1)  # Speed II for 30 seconds
            >>> await player.addEffect("minecraft:regeneration", 200, 0)  # Regeneration I for 10 seconds
            >>> await player.addEffect("minecraft:strength", 1200, 2)  # Strength III for 1 minute
            >>> await player.addEffect("minecraft:night_vision", 6000, 0)  # Night Vision for 5 minutes

        Returns:
            True if effect was added successfully
        """
        return await super().__getattr__("addEffect")(effect_id, duration, amplifier)

    async def clearEffects(self) -> bool:
        """Clear player effects.

        Removes all active potion effects from the player.

        Examples:
            >>> await player.clearEffects()

        Returns:
            True if effects were cleared successfully
        """
        return await super().__getattr__("clearEffects")()

    async def getScore(self, objective_id: str) -> int:
        """Get player score."""
        return await super().__getattr__("getScore")(objective_id)

    async def setScore(self, objective_id: str, score: int) -> bool:
        """Set player score."""
        return await super().__getattr__("setScore")(objective_id, score)

    async def grantAdvancement(self, advancement_id: str) -> bool:
        """Grant advancement to player.

        Args:
            advancement_id: Namespaced ID of the advancement

        Examples:
            >>> await player.grantAdvancement("minecraft:story/mine_stone")
            >>> await player.grantAdvancement("minecraft:story/enter_the_nether")
            >>> await player.grantAdvancement("minecraft:nether/find_fortress")

        Returns:
            True if advancement was granted successfully
        """
        return await super().__getattr__("grantAdvancement")(advancement_id)

    async def revokeAdvancement(self, advancement_id: str) -> bool:
        """Revoke player advancement.

        Args:
            advancement_id: Namespaced ID of the advancement to revoke

        Examples:
            >>> await player.revokeAdvancement("minecraft:story/mine_diamond")
            >>> await player.revokeAdvancement("minecraft:nether/find_fortress")

        Returns:
            True if advancement was revoked successfully
        """
        return await super().__getattr__("revokeAdvancement")(advancement_id)

    async def getAdvancements(self) -> Advancements:
        """Get player advancements.

        Retrieves all advancements and their completion status for the player.

        Examples:
            >>> advancements = await player.getAdvancements()
            >>> print(f"Completed: {len(advancements.completed)}")

        Returns:
            Advancements object with completed and progress data
        """
        data = await super().__getattr__("getAdvancements")()
        return Advancements.from_dict(data)

    async def getUUID(self) -> str:
        """Get player UUID."""
        return await super().__getattr__("getUUID")()

    async def isOnline(self) -> bool:
        """Check if player is online."""
        return await super().__getattr__("isOnline")()

    async def getPing(self) -> int:
        """Get player ping/latency."""
        return await super().__getattr__("getPing")()

    async def getWorld(self) -> str:
        """Get player's current world/dimension."""
        return await super().__getattr__("getWorld")()

    async def getRotation(self) -> Rotation:
        """Get player rotation."""
        data = await super().__getattr__("getRotation")()
        return Rotation(**data)

    async def setRotation(self, yaw: float, pitch: float) -> bool:
        """Set player rotation."""
        return await super().__getattr__("setRotation")(yaw, pitch)

    async def getVelocity(self) -> Velocity:
        """Get player velocity."""
        data = await super().__getattr__("getVelocity")()
        return Velocity(**data)

    async def setVelocity(self, x: float, y: float, z: float) -> bool:
        """Set player velocity."""
        return await super().__getattr__("setVelocity")(x, y, z)

    async def getArmor(self) -> List[ItemStack]:
        """Get player armor."""
        return await super().__getattr__("getArmor")()

    async def getEnderChest(self) -> List[ItemStack]:
        """Get player enderchest inventory."""
        return await super().__getattr__("getEnderChest")()

    async def giveItem(self, item_id: str, count: int) -> bool:
        """Give item to player.

        Args:
            item_id: Namespaced ID of the item
            count: Number of items to give (1-64 for most items)

        Examples:
            >>> await player.giveItem("minecraft:diamond", 64)
            >>> await player.giveItem("minecraft:golden_apple", 1)
            >>> await player.giveItem("minecraft:iron_sword", 1)
            >>> await player.giveItem("minecraft:ender_pearl", 16)

        Returns:
            True if item was given successfully
        """
        return await super().__getattr__("giveItem")(item_id, count)

    async def getPlayerInfo(self) -> PlayerInfo:
        """Get complete player information."""
        data = await super().__getattr__("getPlayerInfo")()
        return PlayerInfo(**data)

