"""
Advanced event handling example demonstrating new events.
Showcases damage tracking, item usage, dimension changes, and more.
"""
import asyncio
from mcwebapi import MinecraftAPI
from mcwebapi.events import (
    PlayerDamageEvent,
    PlayerAttackEntityEvent,
    PlayerUseItemEvent,
    PlayerDimensionChangeEvent,
    PlayerRespawnEvent,
    PlayerItemPickupEvent,
    PlayerItemDropEvent,
    PlayerInteractBlockEvent,
    PlayerAdvancementEvent,
    PlayerDamageEventData,
    PlayerAttackEntityEventData,
    PlayerUseItemEventData,
    PlayerDimensionChangeEventData,
    PlayerRespawnEventData,
    PlayerItemPickupEventData,
    PlayerItemDropEventData,
    PlayerInteractBlockEventData,
    PlayerAdvancementEventData,
)


# Player damage tracker
@PlayerDamageEvent
async def on_player_damage(event: PlayerDamageEventData):
    attacker_info = f" by {event.attacker}" if event.attacker else ""
    print(f"💔 {event.player_name} took {event.damage_amount:.1f} damage from {event.damage_source}{attacker_info}")


# Player attack tracker
@PlayerAttackEntityEvent
async def on_player_attack(event: PlayerAttackEntityEventData):
    weapon_name = event.weapon.split(":")[-1]
    entity_name = event.entity_type.split(":")[-1]
    print(f"⚔️  {event.player_name} attacked {entity_name} with {weapon_name} for {event.damage_amount:.1f} damage")


# Item usage tracker (food, potions, etc.)
@PlayerUseItemEvent
async def on_player_use_item(event: PlayerUseItemEventData):
    item_name = event.item_type.split(":")[-1]
    print(f"🍖 {event.player_name} used {item_name}")


# Dimension change tracker
@PlayerDimensionChangeEvent
async def on_dimension_change(event: PlayerDimensionChangeEventData):
    from_dim = event.from_dimension.split(":")[-1]
    to_dim = event.to_dimension.split(":")[-1]
    print(f"🌍 {event.player_name} traveled from {from_dim} to {to_dim}")


# Respawn tracker
@PlayerRespawnEvent
async def on_respawn(event: PlayerRespawnEventData):
    spawn_type = "bed" if event.is_bed_spawn else "world spawn"
    dim = event.dimension.split(":")[-1]
    print(f"💫 {event.player_name} respawned at {spawn_type} in {dim}")


# Item pickup tracker
@PlayerItemPickupEvent
async def on_item_pickup(event: PlayerItemPickupEventData):
    item_name = event.item_type.split(":")[-1]
    print(f"📥 {event.player_name} picked up {event.item_count}x {item_name}")


# Item drop tracker
@PlayerItemDropEvent
async def on_item_drop(event: PlayerItemDropEventData):
    item_name = event.item_type.split(":")[-1]
    print(f"📤 {event.player_name} dropped {event.item_count}x {item_name}")


# Block interaction tracker
@PlayerInteractBlockEvent
async def on_interact_block(event: PlayerInteractBlockEventData):
    block_name = event.block_type.split(":")[-1]
    hand = event.hand.lower().replace("_", " ")
    print(f"👆 {event.player_name} interacted with {block_name} using {hand}")


# Achievement tracker
@PlayerAdvancementEvent
async def on_advancement(event: PlayerAdvancementEventData):
    print(f"🏆 {event.player_name} earned advancement: {event.advancement_title}")


async def main():
    """Main function to connect and start event monitoring."""
    api = MinecraftAPI()

    try:
        print("Connecting to Minecraft server...")
        await api.connect()
        print("Connected! Starting advanced event monitoring...")
        print("=" * 60)
        print("Monitoring:")
        print("  💔 Player damage")
        print("  ⚔️  Player attacks")
        print("  🍖 Item usage")
        print("  🌍 Dimension changes")
        print("  💫 Player respawns")
        print("  📥 Item pickups")
        print("  📤 Item drops")
        print("  👆 Block interactions")
        print("  🏆 Advancements")
        print("=" * 60)
        print()

        # Start the event manager
        events = api.events()
        await events.start()

        # Keep the script running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping event monitoring...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await api.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
