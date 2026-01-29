"""
Player Monitor
Real-time monitoring of player stats with live updates.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def clear_screen():
    """Clear terminal screen (works on Unix/Linux/Mac)."""
    print("\033[2J\033[H", end="")


async def main():
    """Monitor player stats in real-time."""
    async with MinecraftAPI() as api:
        player = api.Player("Dev")

        print("=== Real-Time Player Monitor ===")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Get player info
                info = await player.getPlayerInfo()
                position = await player.getPosition()
                rotation = await player.getRotation()

                # Clear screen and display stats
                await clear_screen()
                print("=== 📊 PLAYER STATS (Updates every 1s) ===\n")

                print(f"👤 Player: {info.name}")
                print(f"🆔 UUID: {info.uuid}")
                print(f"🌍 World: {info.world}")
                print(f"🎮 Game Mode: {info.gameMode}")

                print(f"\n💚 Health: {'❤️ ' * int(info.health)} ({info.health:.1f}/{info.maxHealth})")
                print(f"🍖 Food: {'🍗' * (info.food // 2)} ({info.food}/20)")
                print(f"⭐ Level: {info.level}")

                print(f"\n📍 Position:")
                print(f"   X: {position.x:>10.2f}")
                print(f"   Y: {position.y:>10.2f}")
                print(f"   Z: {position.z:>10.2f}")

                print(f"\n🧭 Rotation:")
                print(f"   Yaw:   {rotation.yaw:>6.1f}°")
                print(f"   Pitch: {rotation.pitch:>6.1f}°")

                print(f"\n🏃 Status:")
                print(f"   Sneaking: {'✅' if info.isSneaking else '❌'}")
                print(f"   Sprinting: {'✅' if info.isSprinting else '❌'}")
                print(f"   Flying: {'✅' if info.isFlying else '❌'}")

                print(f"\n📶 Ping: {info.ping}ms")


                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped.")


if __name__ == "__main__":
    asyncio.run(main())
