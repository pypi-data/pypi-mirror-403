"""
Entity Spawner
Spawns various entities around the player.
"""

import asyncio
import math
from mcwebapi import MinecraftAPI


async def main():
    """Spawn entities in a circle around player."""
    async with MinecraftAPI() as api:
        print("=== 🐕 Entity Spawner ===\n")

        player = api.Player("Dev")
        entity_api = api.Entity("minecraft:overworld")

        # Get player position
        position = await player.getPosition()
        center_x = position.x
        center_y = position.y
        center_z = position.z

        print(f"Spawning entities around player at ({center_x:.1f}, {center_y:.1f}, {center_z:.1f})\n")

        mobs = [
            "minecraft:cow",
            "minecraft:sheep",
            "minecraft:pig",
            "minecraft:chicken",
            "minecraft:wolf",
            "minecraft:cat",
            "minecraft:horse",
            "minecraft:rabbit",
        ]

        radius = 5.0
        spawned_entities = []

        print("🌀 Spawning entities in a circle...\n")

        for i, mob in enumerate(mobs):
            # Calculate position on circle
            angle = (2 * math.pi * i) / len(mobs)
            x = center_x + radius * math.cos(angle)
            z = center_z + radius * math.sin(angle)
            y = center_y

            # Spawn entity
            result = await entity_api.spawn(mob, x, y, z)

            if result.success:
                spawned_entities.append(result.uuid)
                mob_name = mob.split(":")[1].title()
                print(f"✅ Spawned {mob_name} at ({x:.1f}, {y:.1f}, {z:.1f})")
                print(f"   UUID: {result.uuid}")
            else:
                print(f"❌ Failed to spawn {mob}: {result.error}")

            await asyncio.sleep(0.3)

        # Wait a bit, then get info on first entity
        if spawned_entities:
            print("\n📊 Getting info on first spawned entity...")
            await asyncio.sleep(2)

            first_uuid = spawned_entities[0]
            entity_info = await entity_api.getInfo(first_uuid)

            print(f"\nEntity Info:")
            print(f"  Type: {entity_info.type}")
            print(f"  Position: ({entity_info.x:.1f}, {entity_info.y:.1f}, {entity_info.z:.1f})")
            print(f"  Alive: {entity_info.isAlive}")
            print(f"  On Ground: {entity_info.isOnGround}")

            # Set custom name
            print(f"\n✨ Setting custom name...")
            await entity_api.setCustomName(first_uuid, "Python Spawned!")

            # Make it glow
            print(f"✨ Making it glow...")
            await entity_api.setGlowing(first_uuid, True)

        print(f"\n✅ Spawned {len(spawned_entities)} entities!")
        await player.sendMessage(f"Spawned {len(spawned_entities)} friendly mobs around you!")


if __name__ == "__main__":
    asyncio.run(main())
