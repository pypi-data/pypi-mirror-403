from typing import Any, Tuple, Dict, Callable, Awaitable

from ..core.client import MinecraftClient


class SocketInstance:
    """Base class for all async API entities"""

    def __init__(self, name: str, client: MinecraftClient, *args):
        self.module_name = name
        self._client = client
        self.entry_args = list(args)

    def __getattr__(self, name: str) -> Callable[..., Awaitable[Any]]:
        async def server_method(*args: Any, **kwargs: Any) -> Any:
            final_args = self._process_args(args, kwargs)
            return await self._client.send_request(
                module=self.module_name,
                method=name,
                args=final_args
            )

        return server_method

    def _process_args(self, args: Tuple, kwargs: Dict) -> list:
        processed_args = self.entry_args + list(args)

        if kwargs:
            processed_args.extend(kwargs.values())

        return processed_args
