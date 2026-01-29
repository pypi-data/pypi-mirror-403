<div align="center">

<img width="220" height="220" alt="mcwebapi" src="https://github.com/user-attachments/assets/bcda77d5-f67b-417d-b958-cc65e3627324" />

<h1>Minecraft Websocket API</h1>
<p>
    <strong>
        Async Python client library for the
        <a href="https://github.com/addavriance/MinecraftWebsocketAPI">Minecraft WebSocket API</a>
        mod
    </strong>
</p>

[![PyPI](https://img.shields.io/pypi/v/mcwebapi?style=for-the-badge&logo=pypi&labelColor=black&color=blue)](https://pypi.org/project/mcwebapi/)
[![Python](https://img.shields.io/pypi/pyversions/mcwebapi?style=for-the-badge&logo=python&labelColor=black)](https://pypi.org/project/mcwebapi/)
[![Downloads](https://img.shields.io/pypi/dm/mcwebapi?style=for-the-badge&labelColor=black&color=green)](https://pypi.org/project/mcwebapi/)

</div>

## Features

- **Clean Async API** - Modern async/await syntax with asyncio
- **Event System** - Subscribe to game events with decorators (`@PlayerChatEvent`, `@PlayerJoinEvent`, etc.)
- **Type-safe** - Full typing support with .pyi stubs for better IDE autocomplete
- **Comprehensive** - Player, Level, Block, Server, Entity, and Scoreboard management
- **Lightweight** - Minimal dependencies (just `websockets`)
- **Easy to Use** - Intuitive object-oriented interface

## Installation

```bash
pip install mcwebapi
```

## Quick Start

```python
import asyncio
from mcwebapi import MinecraftAPI

async def main():
    async with MinecraftAPI() as api:
        # Get server info
        server = api.Server()
        info = await server.getInfo()
        print(f"Connected to {info['version']}")

        # Give items to player
        player = api.Player("Steve")
        await player.giveItem("minecraft:diamond", 64)
        await player.sendMessage("You received 64 diamonds!")

        # Set time to day
        level = api.Level("minecraft:overworld")
        await level.setDayTime(6000)

if __name__ == "__main__":
    asyncio.run(main())
```

## Event System

Subscribe to Minecraft events using decorators:

```python
from mcwebapi import MinecraftAPI
from mcwebapi.events import PlayerChatEvent, PlayerJoinEvent

@PlayerChatEvent
async def on_chat(event):
    print(f"{event.player_name}: {event.message}")

@PlayerJoinEvent
async def on_join(event):
    print(f"{event.player_name} joined!")

async def main():
    async with MinecraftAPI() as api:
        events = api.events()
        await events.start()
        try:
            while True:
                await asyncio.sleep(1) # Keep alive
        except KeyboardInterrupt:
            print("\nStopping...")

asyncio.run(main())
```

**Available Events:**
- `@PlayerJoinEvent` - Player joins server
- `@PlayerQuitEvent` - Player leaves server
- `@PlayerChatEvent` - Player sends chat message
- `@PlayerDeathEvent` - Player dies
- `@BlockBreakEvent` - Block broken
- `@BlockPlaceEvent` - Block placed
- `@EntitySpawnEvent` - Entity spawns
- `@EntityDeathEvent` - Entity dies

## Documentation

**[📖 Full Documentation on Wiki](https://github.com/addavriance/mcwebapi/wiki)**

- **[Quick Start Guide](https://github.com/addavriance/mcwebapi/wiki/Home)** - Get started quickly
- **[Player Operations](https://github.com/addavriance/mcwebapi/wiki/Player-Operations)** - Health, inventory, effects, teleportation
- **[Block Operations](https://github.com/addavriance/mcwebapi/wiki/Block-Operations)** - Place blocks, manage inventories
- **[Entity Management](https://github.com/addavriance/mcwebapi/wiki/Entity-Management)** - Spawn and control entities
- **[Level Management](https://github.com/addavriance/mcwebapi/wiki/Level-Management)** - Time, weather, world settings
- **[Scoreboard](https://github.com/addavriance/mcwebapi/wiki/Scoreboard)** - Objectives, teams, scores
- **[Server Management](https://github.com/addavriance/mcwebapi/wiki/Server-Management)** - Server info and administration
- **[Code Examples](https://github.com/addavriance/mcwebapi/wiki/Examples)** - Practical examples for common tasks

## Server Setup

Requires the [MinecraftWebsocketAPI](https://github.com/addavriance/MinecraftWebsocketAPI) mod on your Minecraft 1.21.1 server.

**Basic Setup:**
1. Install the NeoForge mod
2. Configure `config/mcwebapi-server.toml` with your settings (port, auth key)
3. Restart the server

**Python Client:**
```python
api = MinecraftAPI(
    host="localhost",
    port=8765,
    auth_key="your-secret-key"
)
```

## Requirements

- Python 3.8+
- `websockets>=12.0`
- Minecraft 1.21.1 server with [MinecraftWebsocketAPI](https://github.com/addavriance/MinecraftWebsocketAPI) mod

## Contributing

Contributions welcome! Please open an issue or PR on [GitHub](https://github.com/addavriance/mcwebapi).

## Links

- **Documentation:** [Wiki](https://github.com/addavriance/mcwebapi/wiki)
- **PyPI:** [pypi.org/project/mcwebapi](https://pypi.org/project/mcwebapi/)
- **Server Mod:** [MinecraftWebsocketAPI](https://github.com/addavriance/MinecraftWebsocketAPI)
- **Issues:** [GitHub Issues](https://github.com/addavriance/mcwebapi/issues)
