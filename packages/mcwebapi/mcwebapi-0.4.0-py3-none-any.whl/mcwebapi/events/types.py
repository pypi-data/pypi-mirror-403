"""Event data types for Minecraft events."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    """3D position in Minecraft world."""
    x: float
    y: float
    z: float


# Base event classes


@dataclass
class BaseEventData:
    """Base event data with timestamp."""
    timestamp: int


@dataclass
class DimensionalEventData(BaseEventData):
    """Event data with dimension information."""
    dimension: str


@dataclass
class PlayerEventData(BaseEventData):
    """Base event data for player-related events."""
    player_name: str
    player_uuid: str


@dataclass
class PlayerDimensionalEventData(PlayerEventData):
    """Player event data with dimension information."""
    dimension: str


# Player events


@dataclass
class PlayerJoinEventData(PlayerDimensionalEventData):
    """Data for player join event."""
    pass


@dataclass
class PlayerQuitEventData(PlayerEventData):
    """Data for player quit event."""
    pass


@dataclass
class PlayerChatEventData(PlayerEventData):
    """Data for player chat event."""
    message: str


@dataclass
class PlayerDeathEventData(PlayerEventData):
    """Data for player death event."""
    death_message: str
    position: Position
    killer: Optional[str]


@dataclass
class PlayerDamageEventData(PlayerDimensionalEventData):
    """Data for player damage event."""
    damage_amount: float
    damage_source: str
    attacker: Optional[str]
    position: Position


@dataclass
class PlayerAttackEntityEventData(PlayerDimensionalEventData):
    """Data for player attacking entity event."""
    entity_type: str
    entity_uuid: str
    damage_amount: float
    weapon: str
    position: Position


@dataclass
class PlayerUseItemEventData(PlayerDimensionalEventData):
    """Data for player using item event."""
    item_type: str
    item_count: int
    position: Position


@dataclass
class PlayerDimensionChangeEventData(PlayerEventData):
    """Data for player dimension change event."""
    from_dimension: str
    to_dimension: str


@dataclass
class PlayerRespawnEventData(PlayerDimensionalEventData):
    """Data for player respawn event."""
    position: Position
    is_bed_spawn: bool


@dataclass
class PlayerItemPickupEventData(PlayerDimensionalEventData):
    """Data for player item pickup event."""
    item_type: str
    item_count: int
    position: Position


@dataclass
class PlayerItemDropEventData(PlayerDimensionalEventData):
    """Data for player item drop event."""
    item_type: str
    item_count: int
    position: Position


@dataclass
class PlayerInteractBlockEventData(PlayerDimensionalEventData):
    """Data for player block interaction event."""
    block_type: str
    position: Position
    hand: str


@dataclass
class PlayerAdvancementEventData(PlayerDimensionalEventData):
    """Data for player advancement event."""
    advancement_id: str
    advancement_title: str


# Block events


@dataclass
class BlockBreakEventData(PlayerDimensionalEventData):
    """Data for block break event."""
    block_type: str
    position: Position


@dataclass
class BlockPlaceEventData(PlayerDimensionalEventData):
    """Data for block place event."""
    block_type: str
    position: Position
    replaced_block: str


# Entity events


@dataclass
class EntitySpawnEventData(DimensionalEventData):
    """Data for entity spawn event."""
    entity_type: str
    entity_uuid: str
    position: Position


@dataclass
class EntityDeathEventData(DimensionalEventData):
    """Data for entity death event."""
    entity_type: str
    entity_uuid: str
    position: Position
    killer: Optional[str]
