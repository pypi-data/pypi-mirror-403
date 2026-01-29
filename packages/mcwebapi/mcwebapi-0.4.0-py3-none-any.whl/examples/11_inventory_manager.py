"""
Inventory Manager
Inspect and manage player inventory.
"""

import asyncio
from mcwebapi import MinecraftAPI


async def main():
    """Manage player inventory."""
    async with MinecraftAPI() as api:
        print("=== 🎒 Inventory Manager ===\n")

        player = api.Player("Dev")

        # Get current inventory
        print("📦 Current Inventory:")
        inventory = await player.getInventory()

        if not inventory:
            print("  Inventory is empty!")
        else:
            # Group items by type
            item_counts = {}
            for item in inventory:
                item_name = item.item.split(":")[1]
                if item_name not in item_counts:
                    item_counts[item_name] = 0
                item_counts[item_name] += item.count

            # Display inventory summary
            print(f"\n📊 Inventory Summary ({len(inventory)} slots used):")
            for item_name, count in sorted(item_counts.items()):
                print(f"  - {item_name.replace('_', ' ').title()}: x{count}")

            # Display detailed inventory
            print(f"\n📋 Detailed Inventory:")
            for item in inventory:
                item_name = item.item.split(":")[1].replace("_", " ").title()
                damage_info = f" (Damage: {item.damage})" if item.damage > 0 else ""
                print(f"  Slot {item.slot:2d}: {item_name} x{item.count}{damage_info}")

        # Give some items
        print("\n🎁 Giving items to player...")

        items_to_give = [
            ("minecraft:diamond_sword", 1, "Diamond Sword"),
            ("minecraft:diamond_pickaxe", 1, "Diamond Pickaxe"),
            ("minecraft:cooked_beef", 32, "Cooked Beef"),
            ("minecraft:torch", 64, "Torches"),
            ("minecraft:golden_apple", 5, "Golden Apples"),
        ]

        for item_id, count, name in items_to_give:
            success = await player.giveItem(item_id, count)
            if success:
                print(f"  ✅ Gave {count}x {name}")
            else:
                print(f"  ❌ Failed to give {name}")
            await asyncio.sleep(0.3)

        # Get updated inventory count
        print("\n📈 Checking updated inventory...")
        new_inventory = await player.getInventory()
        print(f"  Total slots used: {len(new_inventory)}")

        # Get armor
        print("\n🛡️  Armor:")
        armor = await player.getArmor()

        if not armor:
            print("  No armor equipped")
        else:
            armor_slots = ["Boots", "Leggings", "Chestplate", "Helmet"]
            for item in armor:
                slot_name = armor_slots[item.slot] if item.slot < len(armor_slots) else f"Slot {item.slot}"
                item_name = item.item.split(":")[1].replace("_", " ").title()
                durability = f" ({item.damage}/{item.damage + 100})" if item.damage > 0 else ""
                print(f"  {slot_name}: {item_name}{durability}")

        print("\n✅ Inventory management complete!")
        await player.sendMessage("Inventory check complete!")


if __name__ == "__main__":
    asyncio.run(main())
