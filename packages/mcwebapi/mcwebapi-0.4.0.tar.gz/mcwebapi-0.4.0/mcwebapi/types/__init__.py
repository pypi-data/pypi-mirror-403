"""Type definitions for mcwebapi."""

from .responses import (
    # Common types
    Position,
    Rotation,
    Velocity,
    # Player types
    Experience,
    ItemStack,
    ItemStackExtended,
    MobEffect,
    AdvancementInfo,
    Advancements,
    PlayerInfo,
    # Block types
    BlockInfo,
    BlockInventory,
    FurnaceInfo,
    # Entity types
    EntitySpawnResult,
    EntityInfo,
    EntitySummary,
    # Level types
    BlockState,
    Weather,
    WorldBorder,
    SpawnPoint,
    LevelData,
    ChunkInfo,
    LevelInfo,
    # Server types
    ServerInfo,
    MemoryUsage,
    CommandResult,
    # Scoreboard types
    ObjectiveInfo,
    TeamInfo,
)

__all__ = [
    # Common types
    "Position",
    "Rotation",
    "Velocity",
    # Player types
    "Experience",
    "ItemStack",
    "ItemStackExtended",
    "MobEffect",
    "AdvancementInfo",
    "Advancements",
    "PlayerInfo",
    # Block types
    "BlockInfo",
    "BlockInventory",
    "FurnaceInfo",
    # Entity types
    "EntitySpawnResult",
    "EntityInfo",
    "EntitySummary",
    # Level types
    "BlockState",
    "Weather",
    "WorldBorder",
    "SpawnPoint",
    "LevelData",
    "ChunkInfo",
    "LevelInfo",
    # Server types
    "ServerInfo",
    "MemoryUsage",
    "CommandResult",
    # Scoreboard types
    "ObjectiveInfo",
    "TeamInfo",
]
