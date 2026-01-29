"""
Block Bridge Builder
Creates a bridge of blocks under the player as they walk.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def main():
    """Build a bridge under player in real-time."""
    async with MinecraftAPI() as api:
        print("=== Block Bridge Builder ===\n")

        player = api.Player("Dev")
        block_api = api.Block("minecraft:overworld")

        print("🌉 Building bridge under player for 10 seconds...")
        print("Walk around and watch blocks appear under you!\n")

        last_pos = None
        start_time = asyncio.get_event_loop().time()
        blocks_placed = 0

        while asyncio.get_event_loop().time() - start_time < 10:
            # Get current position
            position = await player.getPosition()
            current_pos = (int(position.x), int(position.y), int(position.z))

            # Only place block if player moved
            if current_pos != last_pos:
                block_x = int(position.x)
                block_y = int(position.y) - 1
                block_z = int(position.z)

                try:
                    await block_api.setBlock(
                        block_x, block_y, block_z,
                        "minecraft:glass"
                    )
                    blocks_placed += 1
                    print(f"✨ Placed block #{blocks_placed} at ({block_x}, {block_y}, {block_z})")
                except Exception as e:
                    print(f"❌ Error placing block: {e}")

                last_pos = current_pos

            # Small delay to avoid spam
            await asyncio.sleep(0.1)

        print(f"\n✅ Bridge building complete! Placed {blocks_placed} blocks.")


if __name__ == "__main__":
    asyncio.run(main())
