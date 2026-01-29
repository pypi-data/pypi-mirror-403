"""
Basic example of using the event system with decorators.

This example shows how to subscribe to various Minecraft events
using both high-level decorators and low-level event API.
"""

import asyncio
import logging

from mcwebapi import MinecraftAPI
from mcwebapi.events import (
    PlayerJoinEvent,
    PlayerQuitEvent,
    PlayerChatEvent,
    PlayerDeathEvent,
    BlockBreakEvent,
    BlockPlaceEvent,
    event,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

api: MinecraftAPI = None


@PlayerJoinEvent
async def on_player_join(event_data):
    """Handle player join events."""
    print(f"[JOIN] {event_data.player_name} joined the server!")
    print(f"  UUID: {event_data.player_uuid}")
    print(f"  Dimension: {event_data.dimension}")


@PlayerQuitEvent
async def on_player_quit(event_data):
    """Handle player quit events."""
    print(f"[QUIT] {event_data.player_name} left the server")


@PlayerChatEvent
async def on_player_chat(event_data):
    """Handle player chat events."""
    print(f"[CHAT] {event_data.player_name}: {event_data.message}")


@PlayerDeathEvent
async def on_player_death(event_data):
    """Handle player death events."""
    print(f"[DEATH] {event_data.player_name} died: {event_data.death_message}")
    if event_data.killer:
        print(f"  Killed by: {event_data.killer}")
    print(f"  Position: ({event_data.position.x}, {event_data.position.y}, {event_data.position.z})")


@BlockBreakEvent
async def on_block_break(event_data):
    """Handle block break events."""
    x, y, z = event_data.position.x, event_data.position.y, event_data.position.z
    await api.Block('minecraft:overworld').setBlock(x, y, z, event_data.block_type)
    print(f"[BLOCK BREAK] {event_data.player_name} broke {event_data.block_type}")
    print(f"  Position: ({event_data.position.x}, {event_data.position.y}, {event_data.position.z})")


@BlockPlaceEvent
async def on_block_place(event_data):
    """Handle block place events."""
    print(f"[BLOCK PLACE] {event_data.player_name} placed {event_data.block_type}")
    print(f"  Replaced: {event_data.replaced_block}")


# Low-level API: Subscribe to custom events (if you code them)
@event("custom.my_event")
async def on_custom_event(event_data):
    """Handle custom events."""
    print(f"[CUSTOM] Received custom event: {event_data}")


async def main():
    """Main function."""
    global api

    # Create API instance
    async with MinecraftAPI(
        host="localhost",
        port=8765,
        auth_key="default-secret-key-change-me"
    ) as api:
        print("Connected to Minecraft server!")

        # Get event manager and start listening
        await api.events().start()

        print("Event system started! Listening for events...")
        print("Press Ctrl+C to stop")

        # Keep the connection alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")


if __name__ == "__main__":
    asyncio.run(main())
