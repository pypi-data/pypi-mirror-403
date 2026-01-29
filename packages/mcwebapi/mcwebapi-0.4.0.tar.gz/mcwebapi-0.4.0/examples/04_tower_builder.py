"""
Tower Builder
Builds a colorful tower at the player's location.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def main():
    """Build a tower with different colored blocks."""
    async with MinecraftAPI() as api:
        print("=== 🏗️  Tower Builder ===\n")

        player = api.Player("Dev")
        block_api = api.Block("minecraft:overworld")

        # Get player position as base
        position = await player.getPosition()
        base_x = int(position.x)
        base_y = int(position.y)
        base_z = int(position.z)

        print(f"Building tower at ({base_x}, {base_y}, {base_z})\n")

        blocks = [
            "minecraft:white_wool",
            "minecraft:orange_wool",
            "minecraft:magenta_wool",
            "minecraft:light_blue_wool",
            "minecraft:yellow_wool",
            "minecraft:lime_wool",
            "minecraft:pink_wool",
            "minecraft:gray_wool",
            "minecraft:light_gray_wool",
            "minecraft:cyan_wool",
            "minecraft:purple_wool",
            "minecraft:blue_wool",
            "minecraft:brown_wool",
            "minecraft:green_wool",
            "minecraft:red_wool",
            "minecraft:black_wool",
        ]

        tower_height = 20

        print("🏗️  Building tower...")
        for i in range(tower_height):
            # Choose block color based on height
            block_type = blocks[i % len(blocks)]
            y = base_y + i

            # Build 3x3 platform
            for dx in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    x = base_x + dx
                    z = base_z + dz

                    await block_api.setBlock(x, y, z, block_type)

            print(f"Layer {i+1}/{tower_height}: {block_type.split(':')[1]}")
            await asyncio.sleep(0.1)  # Small delay for effect

        # Add beacon on top
        print("\n✨ Adding beacon on top...")
        beacon_y = base_y + tower_height
        await block_api.setBlock(base_x, beacon_y, base_z, "minecraft:beacon")

        # Teleport player to top
        print("🚀 Teleporting player to top...")
        await player.teleport(
            float(base_x),
            float(beacon_y + 2),
            float(base_z)
        )

        print(f"\n✅ Tower complete! Height: {tower_height} blocks")
        await player.sendMessage("Welcome to the rainbow tower!")


if __name__ == "__main__":
    asyncio.run(main())
