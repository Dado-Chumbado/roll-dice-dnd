import pytest
from core.roll import RolledDice


@pytest.mark.asyncio
async def test_initiative_advantage_vs_disadvantage():
    """Test that advantage and disadvantage produce opposite results."""
    from core.roll import RolledDice

    # Test with known values
    rolled_dice_adv = RolledDice(20, [15, 8])
    rolled_dice_adv.set_advantage(True)  # Should keep 15

    rolled_dice_disadv = RolledDice(20, [15, 8])
    rolled_dice_disadv.set_advantage(False)  # Should keep 8

    assert rolled_dice_adv.total == 15
    assert rolled_dice_disadv.total == 8


@pytest.mark.asyncio
async def test_initiative_disadvantage_with_modifier():
    """Test initiative roll with disadvantage and a dexterity modifier."""
    from core.roll import RolledDice, Roll

    # Create a roll with disadvantage
    rolled_dice = RolledDice(20, [15, 8])
    rolled_dice.set_advantage(False)  # Disadvantage

    roll = Roll("2d20+4", "+4")
    roll.add_rolled_dice_sum(rolled_dice)
    roll.additional_eval = 4

    # Should keep the lower die (8)
    assert rolled_dice.total == 8

    # Total should be 8 + 4 = 12
    assert roll.total_roll == 12


@pytest.mark.asyncio
async def test_initiative_disadvantage_same_values():
    """Test initiative disadvantage when both dice show the same value."""
    from core.roll import RolledDice

    # When both dice are the same, disadvantage should still work
    rolled_dice = RolledDice(20, [12, 12])
    rolled_dice.set_advantage(False)

    # Should have one inactive die
    active_dice = [d for d in rolled_dice.results if d.is_active]
    assert len(active_dice) == 1
    assert rolled_dice.total == 12


@pytest.mark.asyncio
async def test_initiative_disadvantage_with_negative_modifier():
    """Test initiative disadvantage with a negative dexterity modifier."""
    from core.roll import RolledDice, Roll

    # Create a roll with disadvantage
    rolled_dice = RolledDice(20, [12, 6])
    rolled_dice.set_advantage(False)  # Disadvantage

    roll = Roll("2d20-1", "-1")
    roll.add_rolled_dice_sum(rolled_dice)
    roll.additional_eval = -1

    # Should keep the lower die (6)
    assert rolled_dice.total == 6

    # Total should be 6 - 1 = 5
    assert roll.total_roll == 5


@pytest.mark.asyncio
async def test_initiative_disadvantage_complete_flow():
    """Test complete flow of initiative with disadvantage."""
    from core.initiative import InitTable
    from core.roll import RolledDice, Roll
    import os

    # Create an initiative table
    test_folder = os.path.join(os.getcwd(), 'data/')
    init_table = InitTable(test_folder, "test-initiative-disadv")

    # Reset to ensure clean state
    await init_table.reset("test-initiative-disadv")

    # Simulate rolling initiative with disadvantage
    rolled_dice = RolledDice(20, [14, 9])
    rolled_dice.set_advantage(False)  # Disadvantage - should keep 9

    roll = Roll("2d20+2", "+2")
    roll.add_rolled_dice_sum(rolled_dice)
    roll.additional_eval = 2

    # Get the results
    dice_result = roll.total_dice_result  # Should be 9
    modifier = roll.additional_eval  # Should be 2

    # Verify the disadvantage worked (should keep lower value)
    assert dice_result == 9

    # Add to initiative table
    await init_table.add("test-initiative-disadv", "TestPlayer", dice_result, str(modifier))

    # Verify it was added
    assert len(init_table.initiative_table) == 1
    assert init_table.initiative_table[0].name == "Testplayer"  # capitalized by the code
    assert init_table.initiative_table[0].dex == modifier
    assert init_table.initiative_table[0].total == 11  # 9 + 2

    # Clean up
    await init_table.reset("test-initiative-disadv")
