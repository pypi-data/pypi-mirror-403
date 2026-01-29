"""
Basic Usage Example
Demonstrates fundamental operations with the Minecraft API.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def main():
    """Basic API usage examples."""
    async with MinecraftAPI() as api:
        print("=== Basic Usage Example ===\n")

        # Create player instance
        player = api.Player("Dev")

        # Get player information
        print("📊 Getting player info...")
        info = await player.getPlayerInfo()

        print(f"Player: {info.name}")
        print(f"UUID: {info.uuid}")
        print(f"Health: {info.health}/{info.maxHealth}")
        print(f"Food: {info.food}")
        print(f"Level: {info.level}")
        print(f"Game Mode: {info.gameMode}")
        print(f"World: {info.world}")
        print(f"Position: ({info.x:.1f}, {info.y:.1f}, {info.z:.1f})")
        print(f"Ping: {info.ping}ms")

        # Get player position
        print("\n📍 Position details...")
        position = await player.getPosition()
        print(f"X: {position.x:.2f}")
        print(f"Y: {position.y:.2f}")
        print(f"Z: {position.z:.2f}")

        # Send message to player
        print("\n💬 Sending message to player...")
        await player.sendMessage("Hello from Python API!")

        # Get server info
        print("\n🖥️  Server information...")
        server = api.Server()
        server_info = await server.getInfo()

        print(f"Version: {server_info.version}")
        print(f"Brand: {server_info.brand}")
        print(f"Players: {server_info.onlinePlayerCount}/{server_info.maxPlayers}")
        print(f"TPS: {server_info.averageTPS:.2f}")
        print(f"Difficulty: {server_info.difficulty}")

        print("\n✅ Example completed!")


if __name__ == "__main__":
    asyncio.run(main())
