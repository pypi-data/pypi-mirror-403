"""
Chat bot example using the event system.

This bot responds to various chat commands and welcomes new players.
Demonstrates how to interact with the API from within event handlers.
"""

import asyncio
import logging
import random

from mcwebapi import MinecraftAPI
from mcwebapi.events import PlayerJoinEvent, PlayerChatEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

api: MinecraftAPI = None


@PlayerJoinEvent
async def welcome_player(event_data):
    """Welcome new players to the server."""
    player = api.Player(event_data.player_name)

    # Send welcome message
    await player.sendMessage(f"Welcome to the server, {event_data.player_name}!")
    await asyncio.sleep(0.5)
    await player.sendMessage("Type !help to see available commands")


@PlayerChatEvent
async def handle_commands(event_data):
    """Handle chat commands from players."""
    message = event_data.message.strip()
    player = api.Player(event_data.player_name)

    # Help command
    if message == "!help":
        await player.sendMessage("Available commands:")
        await player.sendMessage("  !help - Show this help message")
        await player.sendMessage("  !heal - Restore your health")
        await player.sendMessage("  !day - Set time to day")
        await player.sendMessage("  !weather clear - Clear the weather")
        await player.sendMessage("  !tp <x> <y> <z> - Teleport to coordinates")
        await player.sendMessage("  !joke - Tell a random joke")

    # Heal command
    elif message == "!heal":
        try:
            await player.setHealth(20.0)
            await player.sendMessage("You have been healed!")
        except Exception as e:
            await player.sendMessage(f"Error: {e}")

    # Day command
    elif message == "!day":
        try:
            command = api.Command()
            await command.execute("time set day")
            await player.sendMessage("Time set to day!")
        except Exception as e:
            await player.sendMessage(f"Error: {e}")

    # Weather command
    elif message == "!weather clear":
        try:
            command = api.Command()
            await command.execute("weather clear")
            await player.sendMessage("Weather cleared!")
        except Exception as e:
            await player.sendMessage(f"Error: {e}")

    # Teleport command
    elif message.startswith("!tp "):
        try:
            parts = message.split()
            if len(parts) != 4:
                await player.sendMessage("Usage: !tp <x> <y> <z>")
                return

            x, y, z = map(float, parts[1:4])
            await player.teleport(x, y, z)
            await player.sendMessage(f"Teleported to {x}, {y}, {z}")
        except ValueError:
            await player.sendMessage("Invalid coordinates! Use numbers.")
        except Exception as e:
            await player.sendMessage(f"Error: {e}")

    # Joke command
    elif message == "!joke":
        jokes = [
            "Why did the creeper cross the road? To get to the other SSSSSS-side!",
            "What's a Minecraft player's favorite type of music? Bedrock!",
            "Why don't Endermen ever win at poker? They always teleport when they get a good hand!",
            "What do you call a zombie who cooks? A dead chef!",
            "Why did Steve go to therapy? He had too many issues with his blocks!",
        ]
        joke = random.choice(jokes)
        await player.sendMessage(joke)

    elif message.startswith("!echo "):
        echo_text = message[6:]  # Remove "!echo "
        await player.sendMessage(f"Echo: {echo_text}")


async def main():
    global api

    print("Starting Minecraft Chat Bot...")

    async with MinecraftAPI(
        host="localhost",
        port=8765,
        auth_key="default-secret-key-change-me"
    ) as api:
        print("Connected to Minecraft server!")

        # Start event system
        events = api.events()
        await events.start()

        print("Chat bot is now active!")
        print("Players can use commands like !help, !heal, !day, etc.")
        print("Press Ctrl+C to stop")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down chat bot...")


if __name__ == "__main__":
    asyncio.run(main())
