"""
Teleport Circle
Teleports the player in a circular path around a center point.
"""

import asyncio
import math
from mcwebapi import MinecraftAPI


async def main():
    """Teleport player in a circle."""
    async with MinecraftAPI() as api:
        print("=== 🌀 Teleport Circle ===\n")

        player = api.Player("Dev")

        # Get starting position as center
        center = await player.getPosition()
        center_x = center.x
        center_y = center.y
        center_z = center.z

        print(f"Center point: ({center_x:.1f}, {center_y:.1f}, {center_z:.1f})")
        print("Starting circular teleportation...\n")

        radius = 10.0  # Circle radius in blocks
        steps = 100  # Number of points on circle
        angle_step = (2 * math.pi) / steps

        for i in range(steps):
            angle = i * angle_step

            x = center_x + radius * math.cos(angle)
            z = center_z + radius * math.sin(angle)
            y = center_y

            # Teleport player
            await player.teleport(x, y, z)

            # Show progress
            progress = (i + 1) / steps * 100
            print(f"🌀 Progress: {progress:>5.1f}% | Position: ({x:>6.1f}, {y:>6.1f}, {z:>6.1f})")

            # Small delay for smooth movement
            await asyncio.sleep(0.01)

        # Return to center
        print("\n🎯 Returning to center...")
        await player.teleport(center_x, center_y, center_z)

        print("\n✅ Circular teleportation complete!")
        await player.sendMessage("Teleport circle complete!")


if __name__ == "__main__":
    asyncio.run(main())
