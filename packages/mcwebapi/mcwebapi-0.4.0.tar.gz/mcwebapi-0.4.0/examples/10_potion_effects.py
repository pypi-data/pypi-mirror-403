"""
Potion Effects Manager
Apply and manage potion effects on the player.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def main():
    """Apply various potion effects to player."""
    async with MinecraftAPI() as api:
        print("=== ⚗️  Potion Effects Manager ===\n")

        player = api.Player("Dev")

        # Check current effects
        print("🔍 Checking current effects...")
        effects = await player.getEffects()

        if effects:
            print("Active effects:")
            for effect in effects:
                print(f"  - {effect.effect} (Level {effect.amplifier + 1}, {effect.duration} ticks)")
        else:
            print("  No active effects")

        # Apply beneficial effects
        print("\n✨ Applying beneficial effects...")

        beneficial_effects = [
            ("minecraft:speed", 600, 1, "Speed II"),
            ("minecraft:jump_boost", 600, 1, "Jump Boost II"),
            ("minecraft:regeneration", 400, 0, "Regeneration"),
            ("minecraft:resistance", 600, 0, "Resistance"),
            ("minecraft:fire_resistance", 600, 0, "Fire Resistance"),
            ("minecraft:night_vision", 600, 0, "Night Vision"),
        ]

        for effect_id, duration, amplifier, name in beneficial_effects:
            await player.addEffect(effect_id, duration, amplifier)
            print(f"  ✅ Applied {name} ({duration} ticks)")
            await player.sendMessage(f"Applied: {name}")
            await asyncio.sleep(0.5)

        # Check effects again
        print("\n📋 Current active effects:")
        effects = await player.getEffects()

        for effect in effects:
            effect_name = effect.effect.split(":")[1].replace("_", " ").title()
            level = effect.amplifier + 1
            seconds = effect.duration // 20
            print(f"  🧪 {effect_name} (Level {level}) - {seconds}s remaining")

        # Wait a bit
        print("\n⏰ Effects active for 10 seconds...")
        await asyncio.sleep(10)

        # Clear all effects
        print("\n🧹 Clearing all effects...")
        await player.clearEffects()
        print("✅ All effects cleared")

        await player.sendMessage("All potion effects removed!")

        print("\n✅ Potion effects demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
