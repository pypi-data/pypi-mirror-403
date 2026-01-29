"""
Server Monitor
Displays real-time server statistics and performance metrics.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def clear_screen():
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


async def main():
    """Monitor server performance in real-time."""
    async with MinecraftAPI() as api:
        server = api.Server()

        print("=== Server Monitor ===")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Get server info and memory
                info = await server.getInfo()
                memory = await server.getMemoryUsage()
                players = await server.getOnlinePlayers()

                await clear_screen()
                print("=== 🖥️  SERVER MONITOR (Updates every 2s) ===\n")

                # Server info
                print(f"📦 Version: {info.version}")
                print(f"🏷️  Brand: {info.brand}")
                print(f"💬 MOTD: {info.motd}")

                # Performance
                print(f"\n⚡ Performance:")
                tps_color = "🟢" if info.averageTPS >= 19.5 else "🟡" if info.averageTPS >= 15 else "🔴"
                print(f"   TPS: {tps_color} {info.averageTPS:.2f}/20.00")
                print(f"   Ticks: {info.ticksRunning:,}")

                # Memory usage
                memory_percent = (memory.used / memory.max) * 100
                memory_bar_length = 20
                filled_length = int(memory_bar_length * memory.used / memory.max)
                memory_bar = "█" * filled_length + "░" * (memory_bar_length - filled_length)

                print(f"\n💾 Memory:")
                print(f"   [{memory_bar}] {memory_percent:.1f}%")
                print(f"   Used:  {format_bytes(memory.used)}")
                print(f"   Total: {format_bytes(memory.total)}")
                print(f"   Max:   {format_bytes(memory.max)}")
                print(f"   Free:  {format_bytes(memory.free)}")

                # Players
                print(f"\n👥 Players: {info.onlinePlayerCount}/{info.maxPlayers}")
                if players:
                    print(f"   Online: {', '.join(players)}")

                # Game settings
                print(f"\n🎮 Settings:")
                print(f"   Difficulty: {info.difficulty}")
                print(f"   Hardcore: {'Yes' if info.isHardcore else 'No'}")
                print(f"   Default Game Mode: {info.defaultGameMode}")

                # Wait before next update
                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped.")


if __name__ == "__main__":
    asyncio.run(main())
