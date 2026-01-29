import logging
import asyncio
import websockets
from websockets.asyncio.client import ClientConnection, connect
from websockets.protocol import State
import json
import base64
from typing import Optional, Callable


class ConnectionManager:
    """
    Manages async WebSocket connection and message handling.

    Handles low-level WebSocket communication, message encoding/decoding,
    and connection state management using asyncio.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.ws: Optional[ClientConnection] = None
        self._connected = False
        self._receiver_task: Optional[asyncio.Task] = None
        self._message_handler: Optional[Callable] = None

    async def connect(self) -> None:
        """Establish async WebSocket connection."""
        ws_url = f"ws://{self.host}:{self.port}/"
        logging.info(f"Connecting to {ws_url}")

        self.ws = await connect(ws_url)
        self._connected = True

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._connected = False
        if self._receiver_task and not self._receiver_task.done():
            self._receiver_task.cancel()
            try:
                await self._receiver_task
            except asyncio.CancelledError:
                pass
        if self.ws:
            await self.ws.close()

    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._connected and self.ws is not None and self.ws.state == State.OPEN

    async def send_message(self, message: dict) -> None:
        """Send encoded message through WebSocket."""
        if not self.is_connected() or self.ws is None:
            raise ConnectionError("Not connected to server")

        encoded_message = self._encode_message(message)
        await self.ws.send(encoded_message)

    def start_receiver(self, message_handler: Callable) -> None:
        """Start message receiver task."""
        self._message_handler = message_handler
        self._receiver_task = asyncio.create_task(self._receiver_loop())

    async def _receiver_loop(self) -> None:
        """Main async receiver loop for incoming messages."""
        while self._connected and self.ws:
            try:
                message = await self.ws.recv()
                if self._message_handler:
                    # Handle message in background if it's async
                    if asyncio.iscoroutinefunction(self._message_handler):
                        asyncio.create_task(self._message_handler(message))
                    else:
                        self._message_handler(message)
            except websockets.exceptions.ConnectionClosed:
                logging.info("WebSocket connection closed")
                self._connected = False
                break
            except Exception as e:
                if self._connected:
                    logging.error(f"Receiver error: {e}")
                break

    def _encode_message(self, message: dict) -> str:
        """Encode message to base64 string."""
        json_str = json.dumps(message, default=str)
        return base64.b64encode(json_str.encode()).decode()

    def _decode_message(self, message: str) -> dict:
        """Decode base64 string to message dict."""
        decoded = base64.b64decode(message).decode()
        return json.loads(decoded)
