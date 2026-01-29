import logging
import time
import asyncio
from typing import Dict, Optional, Any, TYPE_CHECKING

from .connection import ConnectionManager
from ..events.manager import EventManager


class MinecraftClient:
    """
    Async client for communicating with Minecraft WebSocket API.

    Handles request/response cycle, authentication, and high-level API operations
    using asyncio for efficient async/await patterns.
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 8765,
            auth_key: str = "default-secret-key-change-me",
            timeout: float = 10.0,
    ):
        self.auth_key = auth_key
        self.timeout = timeout

        self.connection = ConnectionManager(host, port)
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._authenticated = False
        self._message_id = 0
        self.event_manager: Optional[EventManager] = None

    async def connect(self) -> None:
        """Establish connection and authenticate with server."""
        try:
            # Establish WebSocket connection
            await self.connection.connect()
            self.connection.start_receiver(self._handle_message)

            # Authentication flow
            await self._authenticate()

        except Exception as e:
            await self.connection.disconnect()
            raise ConnectionError(f"Failed to connect: {e}")

    async def disconnect(self) -> None:
        """Close connection and cleanup."""
        self._authenticated = False
        await self.connection.disconnect()

    def is_authenticated(self) -> bool:
        """Check authentication status."""
        return self._authenticated

    def is_connected(self) -> bool:
        """Check connection status."""
        return self.connection.is_connected()

    def has_pending_requests(self) -> bool:
        """Check pending requests status."""
        return len(self._pending_requests) > 0

    def set_event_manager(self, event_manager: EventManager) -> None:
        """
        Set the event manager for handling event messages.

        Args:
            event_manager: EventManager instance to handle events
        """
        self.event_manager = event_manager

    async def send_request(self, module: str, method: str, args: Optional[list] = None) -> Any:
        """
        Send request to server and return the result.

        Args:
            module: API module name (e.g., 'player', 'world')
            method: Method name to call
            args: List of arguments for the method

        Returns:
            The response data from the server

        Raises:
            ConnectionError: If not connected or authenticated
            TimeoutError: If request times out
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to server")

        if not self._authenticated and module != "auth":
            raise ConnectionError("Not authenticated. Call connect() first.")

        request_id = self._generate_request_id()
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        message = {
            "type": "REQUEST",
            "module": module,
            "method": method,
            "args": args or [],
            "requestId": request_id,
            "timestamp": time.time(),
        }

        try:
            logging.info(f"Sending message: {message}")
            await self.connection.send_message(message)
        except Exception as e:
            future.set_exception(e)
            del self._pending_requests[request_id]
            raise

        # Wait for response with timeout
        try:
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result
        except asyncio.TimeoutError:
            del self._pending_requests[request_id]
            raise TimeoutError(f"Request timed out after {self.timeout}s")

    async def _authenticate(self) -> None:
        """Perform authentication flow."""
        check_result = await self.send_request("auth", "check", [])
        logging.info(f"Auth check (no auth): {check_result}")

        auth_info = await self.send_request("auth", "getInfo", [])
        logging.info(f"Auth info: {auth_info}")

        auth_result = await self.send_request("auth", "authenticate", [self.auth_key])
        logging.info(f"Authentication result: {auth_result}")

        if auth_result.get("success"):
            self._authenticated = True
            logging.info("Successfully authenticated!")

            # Verify authentication
            check_result = await self.send_request("auth", "check", [])
            logging.info(f"Auth check: {check_result}")
        else:
            raise ConnectionError(f"Authentication failed: {auth_result.get('message')}")

    def _handle_message(self, raw_message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            if not raw_message or raw_message.strip() == "":
                return

            message = self.connection._decode_message(raw_message)
            message_type = message.get("type")

            # Handle EVENT messages
            if message_type == "EVENT":
                if self.event_manager:
                    asyncio.create_task(self.event_manager._handle_event(message))
                else:
                    logging.debug(f"Received EVENT but no event_manager set: {message.get('method')}")
                return

            # Handle REQUEST/RESPONSE messages
            request_id = message.get("requestId")
            if not request_id or request_id not in self._pending_requests:
                return

            future = self._pending_requests.pop(request_id)

            if message_type == "RESPONSE":
                if message.get("status") == "SUCCESS":
                    future.set_result(message.get("data"))
                else:
                    error_data = message.get("data", {})
                    error_msg = error_data.get("message", "Unknown error")
                    future.set_exception(Exception(f"{error_data.get('code', 'UNKNOWN')}: {error_msg}"))

            elif message_type == "ERROR":
                error_data = message.get("data", {})
                error_msg = error_data.get("message", "Unknown error")
                future.set_exception(Exception(f"{error_data.get('code', 'UNKNOWN')}: {error_msg}"))

        except Exception as e:
            logging.error(f"Error handling message: {e}")

    def _generate_request_id(self) -> str:
        """Generate short unique request ID."""
        self._message_id = (self._message_id + 1) % 4096
        return format(self._message_id, "03x")
