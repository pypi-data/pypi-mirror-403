"""Event manager for handling Minecraft events."""

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional, Type, Callable, Any

if TYPE_CHECKING:
    from ..core.client import MinecraftClient

from .types import Position


class EventManager:
    """
    Manages event subscriptions and handlers for Minecraft events.

    Handles subscribing to events on the server, routing incoming events
    to registered handlers, and converting event data to typed dataclasses.
    """

    def __init__(self, client: "MinecraftClient"):
        """
        Initialize the event manager.

        Args:
            client: The MinecraftClient instance to use for communication
        """
        self.client = client
        self._handlers: Dict[str, List[Tuple[Callable, Optional[Type]]]] = {}
        self._subscribed_events: set = set()
        self._logger = logging.getLogger(__name__)

    async def subscribe(self, event_name: str) -> bool:
        """
        Subscribe to an event on the server.

        Args:
            event_name: Name of the event to subscribe to (e.g., "player.chat")

        Returns:
            True if subscription was successful

        Raises:
            Exception: If subscription fails
        """
        try:
            result = await self.client.send_request("events", "subscribe", [event_name])
            if result.get("subscribed"):
                self._subscribed_events.add(event_name)
                self._logger.info(f"Subscribed to event: {event_name}")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Failed to subscribe to {event_name}: {e}")
            raise

    async def unsubscribe(self, event_name: str) -> bool:
        """
        Unsubscribe from an event on the server.

        Args:
            event_name: Name of the event to unsubscribe from

        Returns:
            True if unsubscription was successful

        Raises:
            Exception: If unsubscription fails
        """
        try:
            result = await self.client.send_request("events", "unsubscribe", [event_name])
            if result.get("unsubscribed"):
                self._subscribed_events.discard(event_name)
                self._logger.info(f"Unsubscribed from event: {event_name}")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Failed to unsubscribe from {event_name}: {e}")
            raise

    def register_handler(
        self,
        event_name: str,
        handler: Callable,
        data_class: Optional[Type] = None
    ) -> None:
        """
        Register a handler function for an event.

        Args:
            event_name: Name of the event
            handler: Async function to call when event occurs
            data_class: Optional dataclass to convert event data to
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append((handler, data_class))
        self._logger.debug(f"Registered handler for {event_name}")

    async def start(self) -> None:
        """
        Start the event manager by loading all decorated handlers and subscribing to events.

        This method:
        1. Imports the decorators module to load all @event decorated functions
        2. Registers all handlers from the global registry
        3. Subscribes to all events that have handlers
        """
        # Import decorators to trigger decorator execution
        from . import decorators

        # Load handlers from global registry
        for event_name, handlers in decorators._global_handlers.items():
            for handler, data_class in handlers:
                self.register_handler(event_name, handler, data_class)

        # Subscribe to all events that have handlers
        for event_name in self._handlers.keys():
            try:
                await self.subscribe(event_name)
            except Exception as e:
                self._logger.error(f"Failed to subscribe to {event_name}: {e}")

        self._logger.info(f"Event manager started with {len(self._handlers)} event types")

    async def _handle_event(self, event_message: dict) -> None:
        """
        Handle an incoming event message from the server.

        Args:
            event_message: The raw event message from the server
        """
        try:
            event_name = event_message.get("method")
            event_data = event_message.get("data", {})

            if not event_name:
                self._logger.warning("Received event without method name")
                return

            handlers = self._handlers.get(event_name, [])
            if not handlers:
                self._logger.debug(f"No handlers registered for event: {event_name}")
                return

            # Call all handlers for this event
            for handler, data_class in handlers:
                try:
                    # Convert data to dataclass if specified
                    if data_class:
                        event_obj = self._convert_to_dataclass(event_data, data_class)
                        asyncio.create_task(handler(event_obj))
                    else:
                        asyncio.create_task(handler(event_data))
                except Exception as e:
                    self._logger.error(
                        f"Error in handler {handler.__name__} for event {event_name}: {e}",
                        exc_info=True
                    )

        except Exception as e:
            self._logger.error(f"Error handling event: {e}", exc_info=True)

    def _convert_to_dataclass(self, data: dict, data_class: Type) -> Any:
        """
        Convert a dictionary to a dataclass instance.

        Handles nested Position objects and converts camelCase to snake_case.

        Args:
            data: Dictionary with event data
            data_class: Dataclass type to convert to

        Returns:
            Instance of data_class
        """
        # Convert camelCase keys to snake_case
        converted_data = {}
        for key, value in data.items():
            snake_key = self._camel_to_snake(key)

            # Handle Position objects
            if isinstance(value, dict) and 'x' in value and 'y' in value and 'z' in value:
                converted_data[snake_key] = Position(
                    x=value['x'],
                    y=value['y'],
                    z=value['z']
                )
            else:
                converted_data[snake_key] = value

        return data_class(**converted_data)

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert camelCase to snake_case."""
        # Разделяем перед заглавными буквами, но не разбиваем последовательности заглавных
        s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Разделяем между строчной и заглавной
        result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
        return result.lower()
