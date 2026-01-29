from typing import List

from .base import SocketInstance
from ..core.client import MinecraftClient
from ..types import EntitySpawnResult, EntityInfo, EntitySummary, Position


class Entity(SocketInstance):
    """Entity object for entity management.

    This class provides methods to spawn, remove, teleport, and manage entities
    in the Minecraft world, including mobs, items, and other game objects.
    """

    def __init__(self, client: MinecraftClient, level_id: str):
        super().__init__("entity", client, level_id)

    async def spawn(self, entity_type_id: str, x: float, y: float, z: float) -> EntitySpawnResult:
        """Spawn entity at coordinates.

        Args:
            entity_type_id: Namespaced ID of the entity type to spawn
            x: X coordinate where to spawn the entity
            y: Y coordinate where to spawn the entity
            z: Z coordinate where to spawn the entity

        Examples:
            >>> result = await entity.spawn("minecraft:zombie", 10.5, 64.0, 20.5)
            >>> result = await entity.spawn("minecraft:cow", 0.0, 70.0, 0.0)
            >>> result = await entity.spawn("minecraft:villager", 5.0, 64.0, 5.0)

        Returns:
            EntitySpawnResult with UUID and spawn success status
        """
        data = await super().__getattr__("spawn")(entity_type_id, x, y, z)
        return EntitySpawnResult(**data)

    async def remove(self, entity_uuid: str) -> bool:
        """Remove entity by UUID.

        Removes the entity from the world without triggering death effects.

        Args:
            entity_uuid: UUID of the entity to remove

        Examples:
            >>> await entity.remove("550e8400-e29b-41d4-a716-446655440000")

        Returns:
            True if entity was removed successfully
        """
        return await super().__getattr__("remove")(entity_uuid)

    async def kill(self, entity_uuid: str) -> bool:
        """Kill entity by UUID.

        Kills the entity, triggering death effects and dropping items.

        Args:
            entity_uuid: UUID of the entity to kill

        Examples:
            >>> await entity.kill("550e8400-e29b-41d4-a716-446655440000")

        Returns:
            True if entity was killed successfully
        """
        return await super().__getattr__("kill")(entity_uuid)

    async def getInfo(self, entity_uuid: str) -> EntityInfo:
        """Get entity information.

        Retrieves detailed information about an entity including type, position,
        health, and other properties.

        Args:
            entity_uuid: UUID of the entity

        Examples:
            >>> info = await entity.getInfo("550e8400-e29b-41d4-a716-446655440000")
            >>> print(f"Entity type: {info.type}, Health: {info.health}")

        Returns:
            EntityInfo object with complete entity data
        """
        data = await super().__getattr__("getInfo")(entity_uuid)
        return EntityInfo.from_dict(data)

    async def getPosition(self, entity_uuid: str) -> Position:
        """Get entity position.

        Args:
            entity_uuid: UUID of the entity

        Examples:
            >>> pos = await entity.getPosition("550e8400-e29b-41d4-a716-446655440000")
            >>> print(f"Entity at x={pos.x}, y={pos.y}, z={pos.z}")

        Returns:
            Position object with x, y, z coordinates
        """
        data = await super().__getattr__("getPosition")(entity_uuid)
        return Position(**data)

    async def teleport(self, entity_uuid: str, x: float, y: float, z: float) -> bool:
        """Teleport entity to coordinates.

        Args:
            entity_uuid: UUID of the entity to teleport
            x: Target X coordinate
            y: Target Y coordinate
            z: Target Z coordinate

        Examples:
            >>> await entity.teleport("550e8400-e29b-41d4-a716-446655440000", 0.0, 64.0, 0.0)

        Returns:
            True if entity was teleported successfully
        """
        return await super().__getattr__("teleport")(entity_uuid, x, y, z)

    async def setVelocity(self, entity_uuid: str, x: float, y: float, z: float) -> bool:
        """Set entity velocity.

        Args:
            entity_uuid: UUID of the entity
            x: Velocity in X direction
            y: Velocity in Y direction (positive = upward)
            z: Velocity in Z direction

        Examples:
            >>> await entity.setVelocity("550e8400-e29b-41d4-a716-446655440000", 0.0, 1.0, 0.0)  # Launch upward
            >>> await entity.setVelocity("550e8400-e29b-41d4-a716-446655440000", 1.0, 0.5, 0.0)  # Push forward and up

        Returns:
            True if velocity was set successfully
        """
        return await super().__getattr__("setVelocity")(entity_uuid, x, y, z)

    async def getCustomName(self, entity_uuid: str) -> str:
        """Get entity custom name.

        Args:
            entity_uuid: UUID of the entity

        Examples:
            >>> name = await entity.getCustomName("550e8400-e29b-41d4-a716-446655440000")
            >>> print(f"Entity name: {name}")

        Returns:
            Custom name of the entity, or empty string if no name is set
        """
        return await super().__getattr__("getCustomName")(entity_uuid)

    async def setCustomName(self, entity_uuid: str, name: str) -> bool:
        """Set entity custom name.

        Args:
            entity_uuid: UUID of the entity
            name: Custom name to set (supports color codes)

        Examples:
            >>> await entity.setCustomName("550e8400-e29b-41d4-a716-446655440000", "My Pet Zombie")
            >>> await entity.setCustomName("550e8400-e29b-41d4-a716-446655440000", "§aBoss Mob")

        Returns:
            True if name was set successfully
        """
        return await super().__getattr__("setCustomName")(entity_uuid, name)

    async def setGlowing(self, entity_uuid: str, glowing: bool) -> bool:
        """Set entity glowing.

        Makes the entity glow with an outline visible through walls.

        Args:
            entity_uuid: UUID of the entity
            glowing: True to make entity glow, False to remove glow

        Examples:
            >>> await entity.setGlowing("550e8400-e29b-41d4-a716-446655440000", True)  # Make glow
            >>> await entity.setGlowing("550e8400-e29b-41d4-a716-446655440000", False)  # Remove glow

        Returns:
            True if glowing state was set successfully
        """
        return await super().__getattr__("setGlowing")(entity_uuid, glowing)

    async def setInvulnerable(self, entity_uuid: str, invulnerable: bool) -> bool:
        """Set entity invulnerable.

        Makes the entity immune to all damage.

        Args:
            entity_uuid: UUID of the entity
            invulnerable: True to make invulnerable, False to make vulnerable

        Examples:
            >>> await entity.setInvulnerable("550e8400-e29b-41d4-a716-446655440000", True)

        Returns:
            True if invulnerability was set successfully
        """
        return await super().__getattr__("setInvulnerable")(entity_uuid, invulnerable)

    async def setFireTicks(self, entity_uuid: str, ticks: int) -> bool:
        """Set entity fire ticks.

        Sets how long the entity will be on fire.

        Args:
            entity_uuid: UUID of the entity
            ticks: Number of ticks to be on fire (20 ticks = 1 second, 0 = extinguish)

        Examples:
            >>> await entity.setFireTicks("550e8400-e29b-41d4-a716-446655440000", 200)
            >>> await entity.setFireTicks("550e8400-e29b-41d4-a716-446655440000", 0)

        Returns:
            True if fire ticks were set successfully
        """
        return await super().__getattr__("setFireTicks")(entity_uuid, ticks)

    async def getEntitiesInRadius(self, x: float, y: float, z: float, radius: float) -> List[EntitySummary]:
        """Get entities within radius.

        Finds all entities within a spherical radius from specified coordinates.

        Args:
            x: Center X coordinate
            y: Center Y coordinate
            z: Center Z coordinate
            radius: Search radius in blocks

        Examples:
            >>> entities = await entity.getEntitiesInRadius(0.0, 64.0, 0.0, 10.0)
            >>> for ent in entities:
            ...     print(f"Found {ent.type} at distance {ent.distance}")

        Returns:
            List of EntitySummary objects for entities within radius
        """
        data = await super().__getattr__("getEntitiesInRadius")(x, y, z, radius)
        return [EntitySummary(**entity) for entity in data]

    async def getEntitiesByType(self, entity_type_id: str) -> List[EntitySummary]:
        """Get all entities of specific type.

        Args:
            entity_type_id: Namespaced ID of the entity type

        Examples:
            >>> zombies = await entity.getEntitiesByType("minecraft:zombie")
            >>> cows = await entity.getEntitiesByType("minecraft:cow")
            >>> villagers = await entity.getEntitiesByType("minecraft:villager")

        Returns:
            List of EntitySummary objects for all entities of the specified type
        """
        data = await super().__getattr__("getEntitiesByType")(entity_type_id)
        return [EntitySummary(**entity) for entity in data]

    async def getAllEntities(self) -> List[EntitySummary]:
        """Get all entities in level.

        Retrieves summary information for all entities in the world.

        Examples:
            >>> all_entities = await entity.getAllEntities()
            >>> print(f"Total entities: {len(all_entities)}")

        Returns:
            List of EntitySummary objects for all entities
        """
        data = await super().__getattr__("getAllEntities")()
        return [EntitySummary(**entity) for entity in data]

    async def getEntityCount(self) -> int:
        """Get total entity count.

        Examples:
            >>> count = await entity.getEntityCount()
            >>> print(f"Total entities: {count}")

        Returns:
            Total number of entities in the world
        """
        return await super().__getattr__("getEntityCount")()

    async def getEntityCountByType(self, type_id) -> int:
        """Get entity count by type.

        Args:
            type_id: Namespaced ID of the entity type

        Examples:
            >>> zombie_count = await entity.getEntityCountByType("minecraft:zombie")
            >>> cow_count = await entity.getEntityCountByType("minecraft:cow")

        Returns:
            Number of entities of the specified type
        """
        return await super().__getattr__("getEntityCountByType")(type_id)
