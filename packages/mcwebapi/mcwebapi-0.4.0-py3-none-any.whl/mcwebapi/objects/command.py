from .base import SocketInstance
from ..core.client import MinecraftClient
from ..types import CommandResult


class Command(SocketInstance):
    """Command object for executing server commands.

    This class provides methods to execute Minecraft server commands and
    retrieve command results.
    """

    def __init__(self, client: MinecraftClient):
        super().__init__("command", client)

    async def executeCommand(self, command: str) -> CommandResult:
        """Execute a server command.

        Executes any valid Minecraft server command without the leading slash.

        Args:
            command: Command to execute

        Common commands:
            - "give <player> <item> [count]" - Give items to player
            - "tp <player> <x> <y> <z>" - Teleport player
            - "gamemode <mode> [player]" - Change game mode
            - "time set <value>" - Set time (day/night/0-24000)
            - "weather <clear|rain|thunder>" - Set weather
            - "difficulty <peaceful|easy|normal|hard>" - Set difficulty
            - "effect give <player> <effect> [duration] [amplifier]" - Give effect
            - "summon <entity> [x] [y] [z]" - Spawn entity
            - "setblock <x> <y> <z> <block>" - Place block
            - "say <message>" - Broadcast message
            - "kill <target>" - Kill entities
            - "clear [player]" - Clear inventory

        Returns:
            CommandResult object with success status and result message
        """
        data = await super().__getattr__("executeCommand")(command)
        return CommandResult(**data)