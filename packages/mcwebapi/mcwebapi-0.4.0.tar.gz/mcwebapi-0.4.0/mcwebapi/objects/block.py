from .base import SocketInstance
from ..core.client import MinecraftClient
from ..types import BlockInfo, BlockInventory, FurnaceInfo


class Block(SocketInstance):
    """Block object for interacting with blocks and their inventory if present.

    This class provides methods to manipulate blocks in the Minecraft world,
    including getting/setting blocks, breaking them, and managing block entity inventories.
    """

    def __init__(self, client: MinecraftClient, level_id: str):
        super().__init__("block", client, level_id)

    async def getBlock(self, x: int, y: int, z: int) -> BlockInfo:
        """Get block information at coordinates.

        Args:
            x: X coordinate of the block
            y: Y coordinate of the block
            z: Z coordinate of the block

        Returns:
            BlockInfo object containing block type and properties
        """
        data = await super().__getattr__("getBlock")(x, y, z)
        return BlockInfo(**data)

    async def setBlock(self, x: int, y: int, z: int, block_id: str) -> bool:
        """Set block at coordinates.

        Args:
            x: X coordinate where to place the block
            y: Y coordinate where to place the block
            z: Z coordinate where to place the block
            block_id: Namespaced ID of the block to place

        Examples:
            >>> await block.setBlock(10, 64, 20, "minecraft:diamond_block")
            >>> await block.setBlock(0, 0, 0, "minecraft:stone")
            >>> await block.setBlock(5, 70, 5, "minecraft:oak_log")

        Returns:
            True if block was set successfully
        """
        return await super().__getattr__("setBlock")(x, y, z, block_id)

    async def breakBlock(self, x: int, y: int, z: int, drop_items: bool = True) -> bool:
        """Break block at coordinates.

        Args:
            x: X coordinate of the block to break
            y: Y coordinate of the block to break
            z: Z coordinate of the block to break
            drop_items: Whether to drop items when breaking the block (default: True)

        Examples:
            >>> await block.breakBlock(10, 64, 20)  # Break and drop items
            >>> await block.breakBlock(10, 64, 20, drop_items=False)  # Break without dropping

        Returns:
            True if block was broken successfully
        """
        return await super().__getattr__("breakBlock")(x, y, z, drop_items)

    async def getInventory(self, x: int, y: int, z: int) -> BlockInventory:
        """Get block entity inventory.

        Works with blocks that have inventories such as chests, furnaces, hoppers, etc.

        Args:
            x: X coordinate of the block entity
            y: Y coordinate of the block entity
            z: Z coordinate of the block entity

        Examples:
            >>> inv = await block.getInventory(10, 64, 20)

        Returns:
            BlockInventory object with items and slots
        """
        data = await super().__getattr__("getInventory")(x, y, z)
        return BlockInventory.from_dict(data)

    async def setInventorySlot(self, x: int, y: int, z: int, slot: int, item_id: str, count: int) -> bool:
        """Set block entity inventory slot.

        Args:
            x: X coordinate of the block entity
            y: Y coordinate of the block entity
            z: Z coordinate of the block entity
            slot: Slot index (0-26 for chests, 0-8 for furnaces)
            item_id: Namespaced ID of the item
            count: Number of items (1-64 for most items)

        Examples:
            >>> await block.setInventorySlot(10, 64, 20, 0, "minecraft:diamond", 64)
            >>> await block.setInventorySlot(10, 64, 20, 1, "minecraft:golden_apple", 1)
            >>> await block.setInventorySlot(10, 64, 20, 5, "minecraft:iron_sword", 1)

        Returns:
            True if slot was set successfully
        """
        return await super().__getattr__("setInventorySlot")(x, y, z, slot, item_id, count);

    async def clearInventory(self, x: int, y: int, z: int) -> bool:
        """Clear block entity inventory.

        Removes all items from the block entity's inventory.

        Args:
            x: X coordinate of the block entity
            y: Y coordinate of the block entity
            z: Z coordinate of the block entity

        Examples:
            >>> await block.clearInventory(10, 64, 20)  # Clear chest inventory

        Returns:
            True if inventory was cleared successfully
        """
        return await super().__getattr__("clearInventory")(x, y, z)

    async def getFurnaceInfo(self, x: int, y: int, z: int) -> FurnaceInfo:
        """Get furnace information.

        Retrieves detailed information about a furnace, including burn time,
        cook time, and current smelting progress.

        Args:
            x: X coordinate of the furnace
            y: Y coordinate of the furnace
            z: Z coordinate of the furnace

        Examples:
            >>> info = await block.getFurnaceInfo(10, 64, 20)
            >>> print(f"Burn time: {info.burn_time}, Cook time: {info.cook_time}")

        Returns:
            FurnaceInfo object with furnace state information
        """
        data = await super().__getattr__("getFurnaceInfo")(x, y, z)
        return FurnaceInfo(**data)
