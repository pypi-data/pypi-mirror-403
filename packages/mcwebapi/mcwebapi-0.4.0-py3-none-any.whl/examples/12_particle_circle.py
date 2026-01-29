"""
Particle Circle
Creates a visual circle of blocks that appears and disappears.
"""

import asyncio
import math
from mcwebapi import MinecraftAPI


async def main():
    """Create an animated circle of glowstone blocks."""
    async with MinecraftAPI() as api:
        print("=== ✨ Particle Circle ===\n")

        player = api.Player("Dev")
        block_api = api.Block("minecraft:overworld")

        # Get player position
        position = await player.getPosition()
        center_x = int(position.x)
        center_y = int(position.y)
        center_z = int(position.z)

        print(f"Creating circle at ({center_x}, {center_y}, {center_z})")
        print("Watch the glowing circle appear and disappear!\n")

        radius = 5
        num_points = 8
        blocks_placed = []

        # Create circle of glowstone
        print("✨ Creating glowing circle...")
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points

            x = center_x + int(radius * math.cos(angle))
            z = center_z + int(radius * math.sin(angle))
            y = center_y

            # Place glowstone
            await block_api.setBlock(x, y, z, "minecraft:glowstone")
            blocks_placed.append((x, y, z))

            # Visual feedback
            if i % 4 == 0:
                print(f"  Progress: {(i / num_points) * 100:.0f}%")

            await asyncio.sleep(0.05)

        print("✅ Circle created!")
        await player.sendMessage("Glowing circle created!")

        # Animate - make it pulse
        print("\n💫 Pulsing animation...")
        for pulse in range(3):
            # Switch to sea lanterns
            print(f"  Pulse {pulse + 1}/3 - Brightening...")
            for x, y, z in blocks_placed:
                await block_api.setBlock(x, y, z, "minecraft:sea_lantern")
            await asyncio.sleep(1)

            # Switch back to glowstone
            print(f"  Pulse {pulse + 1}/3 - Dimming...")
            for x, y, z in blocks_placed:
                await block_api.setBlock(x, y, z, "minecraft:glowstone")
            await asyncio.sleep(1)

        # Remove circle block by block
        print("\n🌟 Removing circle...")
        for i, (x, y, z) in enumerate(blocks_placed):
            await block_api.setBlock(x, y, z, "minecraft:air")

            if i % 4 == 0:
                print(f"  Progress: {(i / len(blocks_placed)) * 100:.0f}%")

            await asyncio.sleep(0.05)

        print("\n✅ Animation complete!")
        await player.sendMessage("Particle circle animation finished!")


if __name__ == "__main__":
    asyncio.run(main())
