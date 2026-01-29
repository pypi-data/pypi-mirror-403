"""
World Controller
Control world settings like time, weather, and difficulty.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def main():
    """Demonstrate world control capabilities."""
    async with MinecraftAPI() as api:
        print("=== 🌍 World Controller ===\n")

        level = api.Level("minecraft:overworld")
        player = api.Player("Dev")

        # Get current world info
        print("📊 Current World Status:")
        level_info = await level.getLevelInfo()

        print(f"  Dimension: {level_info.dimension}")
        print(f"  Seed: {level_info.seed}")
        print(f"  Day Time: {level_info.dayTime}")
        print(f"  Total Time: {level_info.totalTime}")
        print(f"  Difficulty: {level_info.difficulty}")
        print(f"  Players: {level_info.playerCount}")

        # Check time of day
        is_day = await level.isDay()
        is_night = await level.isNight()
        print(f"\n🌞 Time: {'Day' if is_day else 'Night'}")

        # Weather info
        weather = await level.getWeather()
        print(f"\n☁️  Weather:")
        print(f"  Raining: {weather.isRaining}")
        print(f"  Thundering: {weather.isThundering}")
        if weather.isRaining:
            print(f"  Rain Level: {weather.rainLevel:.2f}")

        # Cycle through times
        print("\n⏰ Cycling through different times...")
        times = [
            (1000, "Morning"),
            (6000, "Noon"),
            (12000, "Sunset"),
            (18000, "Midnight"),
        ]

        for time_ticks, time_name in times:
            await level.setDayTime(time_ticks)
            print(f"  Set time to {time_name} ({time_ticks} ticks)")
            await player.sendMessage(f"Time: {time_name}")
            await asyncio.sleep(2)

        # Weather demo
        print("\n🌧️  Weather demonstration...")

        # Make it rain
        print("  Starting rain...")
        await level.setWeather(True, False)
        await player.sendMessage("Rain started!")
        await asyncio.sleep(3)

        # Add thunder
        print("  Adding thunder...")
        await level.setWeather(True, True)
        await player.sendMessage("Thunder storm!")
        await asyncio.sleep(3)

        # Clear weather
        print("  Clearing weather...")
        await level.setWeather(False, False)
        await player.sendMessage("Clear skies!")

        # World border info
        print("\n🗺️  World Border:")
        border = await level.getWorldBorder()
        print(f"  Center: ({border.centerX}, {border.centerZ})")
        print(f"  Size: {border.size} blocks")
        print(f"  Damage: {border.damagePerBlock}/block")

        # Spawn point
        spawn = await level.getSpawnPoint()
        print(f"\n🎯 Spawn Point: ({spawn.x}, {spawn.y}, {spawn.z})")

        print("\n✅ World control demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
