"""
Combat statistics tracker using advanced events.
Tracks player damage dealt/received and provides real-time combat stats.
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict
from mcwebapi import MinecraftAPI
from mcwebapi.events import (
    PlayerDamageEvent,
    PlayerAttackEntityEvent,
    PlayerDeathEvent,
    PlayerJoinEvent,
    PlayerQuitEvent,
    PlayerDamageEventData,
    PlayerAttackEntityEventData,
    PlayerDeathEventData,
    PlayerJoinEventData,
    PlayerQuitEventData,
)


@dataclass
class PlayerStats:
    """Combat statistics for a player."""
    damage_dealt: float = 0.0
    damage_taken: float = 0.0
    kills: int = 0
    deaths: int = 0
    entities_killed: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    death_causes: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def get_kd_ratio(self) -> float:
        """Calculate kill/death ratio."""
        return self.kills / max(self.deaths, 1)

    def print_stats(self, player_name: str):
        """Print formatted statistics."""
        print(f"\n📊 Stats for {player_name}:")
        print(f"  Damage Dealt: {self.damage_dealt:.1f}")
        print(f"  Damage Taken: {self.damage_taken:.1f}")
        print(f"  Kills: {self.kills}")
        print(f"  Deaths: {self.deaths}")
        print(f"  K/D Ratio: {self.get_kd_ratio():.2f}")

        if self.entities_killed:
            print(f"  Top kills:")
            for entity, count in sorted(self.entities_killed.items(), key=lambda x: x[1], reverse=True)[:3]:
                entity_name = entity.split(":")[-1]
                print(f"    - {entity_name}: {count}")

        if self.death_causes:
            print(f"  Death causes:")
            for cause, count in sorted(self.death_causes.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"    - {cause}: {count}")


# Global stats storage
player_stats: Dict[str, PlayerStats] = defaultdict(PlayerStats)


@PlayerJoinEvent
async def on_player_join(event: PlayerJoinEventData):
    """Initialize stats for new players."""
    if event.player_name not in player_stats:
        player_stats[event.player_name] = PlayerStats()
    print(f"✅ {event.player_name} joined the server")


@PlayerQuitEvent
async def on_player_quit(event: PlayerQuitEventData):
    """Show stats when player leaves."""
    print(f"❌ {event.player_name} left the server")
    if event.player_name in player_stats:
        player_stats[event.player_name].print_stats(event.player_name)


@PlayerDamageEvent
async def on_player_damage(event: PlayerDamageEventData):
    """Track damage taken by players."""
    stats = player_stats[event.player_name]
    stats.damage_taken += event.damage_amount

    attacker_info = f" by {event.attacker}" if event.attacker else ""
    print(f"💔 {event.player_name} took {event.damage_amount:.1f} damage from {event.damage_source}{attacker_info}")


@PlayerAttackEntityEvent
async def on_player_attack(event: PlayerAttackEntityEventData):
    """Track damage dealt by players."""
    stats = player_stats[event.player_name]
    stats.damage_dealt += event.damage_amount

    entity_name = event.entity_type.split(":")[-1]
    weapon_name = event.weapon.split(":")[-1]
    print(f"⚔️  {event.player_name} hit {entity_name} with {weapon_name} for {event.damage_amount:.1f} damage")


@PlayerDeathEvent
async def on_player_death(event: PlayerDeathEventData):
    """Track player deaths and entity kills."""
    # Track death for victim
    victim_stats = player_stats[event.player_name]
    victim_stats.deaths += 1

    # Determine death cause
    death_message = event.death_message
    if "by" in death_message.lower():
        cause = death_message.split("by")[-1].strip()
    else:
        cause = "environment"

    victim_stats.death_causes[cause] += 1

    # Track kill for killer
    if event.killer:
        killer_stats = player_stats[event.killer]
        killer_stats.kills += 1
        # Assume killer was player, track as player kill
        killer_stats.entities_killed["player"] += 1
        print(f"💀 {event.player_name} was killed by {event.killer}")
    else:
        print(f"💀 {event.player_name} died: {event.death_message}")


async def show_leaderboard():
    """Periodically show leaderboard."""
    while True:
        await asyncio.sleep(60)  # Show every minute

        if not player_stats:
            continue

        print("\n" + "=" * 60)
        print("🏆 COMBAT LEADERBOARD")
        print("=" * 60)

        # Most damage dealt
        print("\n🗡️  Most Damage Dealt:")
        for i, (player, stats) in enumerate(sorted(player_stats.items(), key=lambda x: x[1].damage_dealt, reverse=True)[:3], 1):
            print(f"  {i}. {player}: {stats.damage_dealt:.1f}")

        # Best K/D ratio
        print("\n⚔️  Best K/D Ratio:")
        for i, (player, stats) in enumerate(sorted(player_stats.items(), key=lambda x: x[1].get_kd_ratio(), reverse=True)[:3], 1):
            print(f"  {i}. {player}: {stats.get_kd_ratio():.2f} ({stats.kills}K/{stats.deaths}D)")

        # Most kills
        print("\n💀 Most Kills:")
        for i, (player, stats) in enumerate(sorted(player_stats.items(), key=lambda x: x[1].kills, reverse=True)[:3], 1):
            print(f"  {i}. {player}: {stats.kills}")

        print("=" * 60 + "\n")


async def main():
    """Main function to connect and start tracking."""
    api = MinecraftAPI()

    try:
        print("Connecting to Minecraft server...")
        await api.connect()
        print("Connected! Starting combat statistics tracking...")
        print("=" * 60)
        print("Tracking combat stats...")
        print("Stats will be shown when players leave")
        print("Leaderboard updates every minute")
        print("=" * 60)
        print()

        # Start the event manager
        events = api.events()
        await events.start()

        # Start leaderboard task
        leaderboard_task = asyncio.create_task(show_leaderboard())

        try:
            # Keep the script running
            while True:
                await asyncio.sleep(1)
        finally:
            leaderboard_task.cancel()

    except KeyboardInterrupt:
        print("\nStopping combat tracker...")

        # Show final stats for all players
        if player_stats:
            print("\n" + "=" * 60)
            print("FINAL STATISTICS")
            print("=" * 60)
            for player_name, stats in player_stats.items():
                stats.print_stats(player_name)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await api.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
