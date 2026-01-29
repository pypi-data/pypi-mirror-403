"""Event decorators for subscribing to Minecraft events."""

from typing import Callable, Dict, List, Tuple, Type, Optional
from .types import (
    PlayerJoinEventData,
    PlayerQuitEventData,
    PlayerChatEventData,
    PlayerDeathEventData,
    PlayerDamageEventData,
    PlayerAttackEntityEventData,
    PlayerUseItemEventData,
    PlayerDimensionChangeEventData,
    PlayerRespawnEventData,
    PlayerItemPickupEventData,
    PlayerItemDropEventData,
    PlayerInteractBlockEventData,
    PlayerAdvancementEventData,
    BlockBreakEventData,
    BlockPlaceEventData,
    EntitySpawnEventData,
    EntityDeathEventData,
)

# Global registry of event handlers
# Format: {event_name: [(handler_function, data_class)]}
_global_handlers: Dict[str, List[Tuple[Callable, Optional[Type]]]] = {}


def event(event_name: str):
    """
    Low-level decorator for subscribing to custom events.

    Usage:
        @event("custom.my_event")
        async def on_custom(event_data):
            print(event_data)
    """
    def decorator(func: Callable):
        if event_name not in _global_handlers:
            _global_handlers[event_name] = []
        _global_handlers[event_name].append((func, None))
        return func
    return decorator


class EventDecorator:
    """Base class for event decorators with typed data."""

    _event_name: str = ""
    _data_class: Optional[Type] = None

    def __init__(self, func: Callable):
        """Initialize the decorator with a handler function."""
        if self._event_name not in _global_handlers:
            _global_handlers[self._event_name] = []
        _global_handlers[self._event_name].append((func, self._data_class))
        self.func = func

    def __call__(self, *args, **kwargs):
        """Make the decorator callable."""
        return self.func(*args, **kwargs)


class PlayerJoinEvent(EventDecorator):
    """
    Decorator for player join events.

    Usage:
        @PlayerJoinEvent
        async def on_join(event: PlayerJoinEventData):
            print(f"{event.player_name} joined!")
    """
    _event_name = "player.join"
    _data_class = PlayerJoinEventData


class PlayerQuitEvent(EventDecorator):
    """
    Decorator for player quit events.

    Usage:
        @PlayerQuitEvent
        async def on_quit(event: PlayerQuitEventData):
            print(f"{event.player_name} left!")
    """
    _event_name = "player.quit"
    _data_class = PlayerQuitEventData


class PlayerChatEvent(EventDecorator):
    """
    Decorator for player chat events.

    Usage:
        @PlayerChatEvent
        async def on_chat(event: PlayerChatEventData):
            print(f"{event.player_name}: {event.message}")
    """
    _event_name = "player.chat"
    _data_class = PlayerChatEventData


class PlayerDeathEvent(EventDecorator):
    """
    Decorator for player death events.

    Usage:
        @PlayerDeathEvent
        async def on_death(event: PlayerDeathEventData):
            print(f"{event.player_name} died: {event.death_message}")
    """
    _event_name = "player.death"
    _data_class = PlayerDeathEventData


class BlockBreakEvent(EventDecorator):
    """
    Decorator for block break events.

    Usage:
        @BlockBreakEvent
        async def on_break(event: BlockBreakEventData):
            print(f"{event.player_name} broke {event.block_type}")
    """
    _event_name = "player.block_break"
    _data_class = BlockBreakEventData


class BlockPlaceEvent(EventDecorator):
    """
    Decorator for block place events.

    Usage:
        @BlockPlaceEvent
        async def on_place(event: BlockPlaceEventData):
            print(f"{event.player_name} placed {event.block_type}")
    """
    _event_name = "player.block_place"
    _data_class = BlockPlaceEventData


class EntitySpawnEvent(EventDecorator):
    """
    Decorator for entity spawn events.

    Usage:
        @EntitySpawnEvent
        async def on_spawn(event: EntitySpawnEventData):
            print(f"{event.entity_type} spawned!")
    """
    _event_name = "entity.spawn"
    _data_class = EntitySpawnEventData


class EntityDeathEvent(EventDecorator):
    """
    Decorator for entity death events.

    Usage:
        @EntityDeathEvent
        async def on_entity_death(event: EntityDeathEventData):
            print(f"{event.entity_type} died!")
    """
    _event_name = "entity.death"
    _data_class = EntityDeathEventData


class PlayerDamageEvent(EventDecorator):
    """
    Decorator for player damage events.

    Usage:
        @PlayerDamageEvent
        async def on_damage(event: PlayerDamageEventData):
            print(f"{event.player_name} took {event.damage_amount} damage from {event.damage_source}")
    """
    _event_name = "player.damage"
    _data_class = PlayerDamageEventData


class PlayerAttackEntityEvent(EventDecorator):
    """
    Decorator for player attacking entity events.

    Usage:
        @PlayerAttackEntityEvent
        async def on_attack(event: PlayerAttackEntityEventData):
            print(f"{event.player_name} attacked {event.entity_type} with {event.weapon}")
    """
    _event_name = "player.attack_entity"
    _data_class = PlayerAttackEntityEventData


class PlayerUseItemEvent(EventDecorator):
    """
    Decorator for player using item events.

    Usage:
        @PlayerUseItemEvent
        async def on_use(event: PlayerUseItemEventData):
            print(f"{event.player_name} used {event.item_type}")
    """
    _event_name = "player.use_item"
    _data_class = PlayerUseItemEventData


class PlayerDimensionChangeEvent(EventDecorator):
    """
    Decorator for player dimension change events.

    Usage:
        @PlayerDimensionChangeEvent
        async def on_dimension_change(event: PlayerDimensionChangeEventData):
            print(f"{event.player_name} moved from {event.from_dimension} to {event.to_dimension}")
    """
    _event_name = "player.dimension_change"
    _data_class = PlayerDimensionChangeEventData


class PlayerRespawnEvent(EventDecorator):
    """
    Decorator for player respawn events.

    Usage:
        @PlayerRespawnEvent
        async def on_respawn(event: PlayerRespawnEventData):
            print(f"{event.player_name} respawned in {event.dimension}")
    """
    _event_name = "player.respawn"
    _data_class = PlayerRespawnEventData


class PlayerItemPickupEvent(EventDecorator):
    """
    Decorator for player item pickup events.

    Usage:
        @PlayerItemPickupEvent
        async def on_pickup(event: PlayerItemPickupEventData):
            print(f"{event.player_name} picked up {event.item_count}x {event.item_type}")
    """
    _event_name = "player.item_pickup"
    _data_class = PlayerItemPickupEventData


class PlayerItemDropEvent(EventDecorator):
    """
    Decorator for player item drop events.

    Usage:
        @PlayerItemDropEvent
        async def on_drop(event: PlayerItemDropEventData):
            print(f"{event.player_name} dropped {event.item_count}x {event.item_type}")
    """
    _event_name = "player.item_drop"
    _data_class = PlayerItemDropEventData


class PlayerInteractBlockEvent(EventDecorator):
    """
    Decorator for player block interaction events.

    Usage:
        @PlayerInteractBlockEvent
        async def on_interact(event: PlayerInteractBlockEventData):
            print(f"{event.player_name} interacted with {event.block_type}")
    """
    _event_name = "player.interact_block"
    _data_class = PlayerInteractBlockEventData


class PlayerAdvancementEvent(EventDecorator):
    """
    Decorator for player advancement events.

    Usage:
        @PlayerAdvancementEvent
        async def on_advancement(event: PlayerAdvancementEventData):
            print(f"{event.player_name} earned: {event.advancement_title}")
    """
    _event_name = "player.advancement"
    _data_class = PlayerAdvancementEventData
