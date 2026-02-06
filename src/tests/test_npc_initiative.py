import pytest
from core.initiative import InitTable
from core.roll import RolledDice, Roll
import os


@pytest.mark.asyncio
async def test_npc_initiative_basic():
    """Test basic NPC initiative roll simulation."""
    # Create an initiative table
    test_folder = os.path.join(os.getcwd(), 'data/')
    init_table = InitTable(test_folder, "test-npc-init")

    # Reset to ensure clean state
    await init_table.reset("test-npc-init")

    # Simulate rolling initiative for 3 goblins with +2 dex
    for i in range(3):
        # Simulate a d20 roll
        rolled_dice = RolledDice(20, [10 + i])  # Mock rolls: 10, 11, 12
        roll = Roll("1d20+2", "+2")
        roll.add_rolled_dice_sum(rolled_dice)
        roll.additional_eval = 2

        # Add to initiative table
        npc_name = f"Goblin {i + 1}"
        await init_table.add("test-npc-init", npc_name, roll.total_dice_result, str(roll.additional_eval))

    # Verify all were added
    assert len(init_table.initiative_table) == 3

    # Check names are correct
    names = [entry.name for entry in init_table.initiative_table]
    assert "Goblin 1" in names
    assert "Goblin 2" in names
    assert "Goblin 3" in names

    # Check they're sorted by total (descending)
    totals = [entry.total for entry in init_table.initiative_table]
    assert totals == sorted(totals, reverse=True)

    # Clean up
    await init_table.reset("test-npc-init")


@pytest.mark.asyncio
async def test_npc_initiative_with_advantage():
    """Test NPC initiative with advantage."""
    test_folder = os.path.join(os.getcwd(), 'data/')
    init_table = InitTable(test_folder, "test-npc-adv")

    await init_table.reset("test-npc-adv")

    # Simulate rolling with advantage (2d20, keep higher)
    rolled_dice = RolledDice(20, [15, 8])
    rolled_dice.set_advantage(True)  # Should keep 15

    roll = Roll("2d20+3", "+3")
    roll.add_rolled_dice_sum(rolled_dice)
    roll.additional_eval = 3

    # Verify advantage worked
    assert rolled_dice.total == 15

    # Add to initiative
    await init_table.add("test-npc-adv", "Guard 1", roll.total_dice_result, str(roll.additional_eval))

    # Verify
    assert len(init_table.initiative_table) == 1
    assert init_table.initiative_table[0].name == "Guard 1"
    assert init_table.initiative_table[0].total == 18  # 15 + 3

    await init_table.reset("test-npc-adv")


@pytest.mark.asyncio
async def test_npc_initiative_with_disadvantage():
    """Test NPC initiative with disadvantage."""
    test_folder = os.path.join(os.getcwd(), 'data/')
    init_table = InitTable(test_folder, "test-npc-disadv")

    await init_table.reset("test-npc-disadv")

    # Simulate rolling with disadvantage (2d20, keep lower)
    rolled_dice = RolledDice(20, [15, 8])
    rolled_dice.set_advantage(False)  # Should keep 8

    roll = Roll("2d20+1", "+1")
    roll.add_rolled_dice_sum(rolled_dice)
    roll.additional_eval = 1

    # Verify disadvantage worked
    assert rolled_dice.total == 8

    # Add to initiative
    await init_table.add("test-npc-disadv", "Zombie 1", roll.total_dice_result, str(roll.additional_eval))

    # Verify
    assert len(init_table.initiative_table) == 1
    assert init_table.initiative_table[0].name == "Zombie 1"
    assert init_table.initiative_table[0].total == 9  # 8 + 1

    await init_table.reset("test-npc-disadv")


@pytest.mark.asyncio
async def test_multiple_npc_groups():
    """Test rolling for multiple different NPC groups."""
    test_folder = os.path.join(os.getcwd(), 'data/')
    init_table = InitTable(test_folder, "test-multi-npc")

    await init_table.reset("test-multi-npc")

    # Add 2 goblins
    for i in range(2):
        rolled_dice = RolledDice(20, [10 + i])
        roll = Roll("1d20+2", "+2")
        roll.add_rolled_dice_sum(rolled_dice)
        roll.additional_eval = 2
        await init_table.add("test-multi-npc", f"Goblin {i + 1}", roll.total_dice_result, str(roll.additional_eval))

    # Add 1 dragon
    rolled_dice = RolledDice(20, [18])
    roll = Roll("1d20+3", "+3")
    roll.add_rolled_dice_sum(rolled_dice)
    roll.additional_eval = 3
    await init_table.add("test-multi-npc", "Dragon", roll.total_dice_result, str(roll.additional_eval))

    # Verify all were added
    assert len(init_table.initiative_table) == 3

    # Dragon should be first (highest total)
    assert init_table.initiative_table[0].name == "Dragon"
    assert init_table.initiative_table[0].total == 21  # 18 + 3

    await init_table.reset("test-multi-npc")


@pytest.mark.asyncio
async def test_npc_with_negative_dex():
    """Test NPC with negative dexterity modifier."""
    test_folder = os.path.join(os.getcwd(), 'data/')
    init_table = InitTable(test_folder, "test-npc-neg")

    await init_table.reset("test-npc-neg")

    # Simulate rolling with negative modifier
    rolled_dice = RolledDice(20, [10])
    roll = Roll("1d20-1", "-1")
    roll.add_rolled_dice_sum(rolled_dice)
    roll.additional_eval = -1

    await init_table.add("test-npc-neg", "Zombie", roll.total_dice_result, str(roll.additional_eval))

    # Verify
    assert len(init_table.initiative_table) == 1
    assert init_table.initiative_table[0].total == 9  # 10 - 1
    assert init_table.initiative_table[0].dex == -1

    await init_table.reset("test-npc-neg")
