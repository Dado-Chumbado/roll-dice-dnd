import pytest

from ..core.roll import Roll, RolledDice, Dice, _roll_dice, generate_dice_roll


@pytest.mark.asyncio
async def test_roll_dice(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    times = 3
    dice = 6
    result = await _roll_dice(times, dice)

    # Check if the number of rolls and the result are correct
    assert len(result) == 3
    assert result == [6, 6, 6]

    times = 1
    dice = 20
    result = await _roll_dice(times, dice)

    # Check if the number of rolls and the result are correct
    assert len(result) == 1
    assert result == [20]

@pytest.mark.asyncio
async def test_generate_roll(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    times = 3
    dice = 6
    rolled_dice = await generate_dice_roll(times, dice)

    assert type(rolled_dice) == RolledDice
    assert len(rolled_dice.results) == 3
    assert rolled_dice.results == [Dice(value=6, is_active=True,
                                      is_critical=True, is_fail=False),
                            Dice(value=6, is_active=True,
                                        is_critical=True, is_fail=False),
                            Dice(value=6, is_active=True,
                                        is_critical=True, is_fail=False),
                            ]
    assert rolled_dice.total == 18
    assert rolled_dice.quantity == 3
    assert rolled_dice.dice_base == 6

    # Custom test
    rolled_dice = RolledDice(6, [2, 4, 6, 3, 1])

    assert type(rolled_dice) == RolledDice
    assert len(rolled_dice.results) == 5
    assert rolled_dice.results == [Dice(value=2, is_active=True,
                                      is_critical=False, is_fail=False),
                            Dice(value=4, is_active=True,
                                        is_critical=False, is_fail=False),
                            Dice(value=6, is_active=True,
                                        is_critical=True, is_fail=False),
                            Dice(value=3, is_active=True,
                                        is_critical=False, is_fail=False),
                            Dice(value=1, is_active=True,
                                        is_critical=False, is_fail=True),
                            ]
    assert rolled_dice.total == 16
    assert rolled_dice.quantity == 5
    assert rolled_dice.dice_base == 6


@pytest.mark.asyncio
async def test_apply_critical():

    rolled_dice = RolledDice(6, [1, 4, 6])
    assert rolled_dice.total == 11
    assert rolled_dice.quantity == 3
    assert rolled_dice.get_list_valid_values() == [1, 4, 6]
    rolled_dice.apply_critical()
    assert rolled_dice.get_list_valid_values() == [6, 4, 6]
    assert rolled_dice.total == 16
    assert rolled_dice.quantity == 3

    rolled_dice = RolledDice(12, [6, 11])
    rolled_dice.apply_critical()
    assert rolled_dice.get_list_valid_values() == [12, 11]
    assert rolled_dice.total == 23

    rolled_dice = RolledDice(12, [12, 11])
    rolled_dice.apply_critical()
    assert rolled_dice.get_list_valid_values() == [12, 11]
    assert rolled_dice.total == 23

    rolled_dice = RolledDice(12, [1, 1])
    assert rolled_dice.results[0].is_critical == False
    assert rolled_dice.results[0].is_fail == True
    assert rolled_dice.results[1].is_critical == False
    assert rolled_dice.results[1].is_fail == True
    rolled_dice.apply_critical()
    assert rolled_dice.get_list_valid_values() == [12, 1]
    assert rolled_dice.results[0].is_critical == True
    assert rolled_dice.results[0].is_fail == False
    assert rolled_dice.results[1].is_critical == False
    assert rolled_dice.results[1].is_fail == True
    assert rolled_dice.total == 13


@pytest.mark.asyncio
async def test_apply_reroll(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    rolled_dice = RolledDice(6, [2, 5])
    assert len(rolled_dice.results) == 2
    rolled_dice = await rolled_dice.apply_reroll(3)

    assert len(rolled_dice.results) == 3
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[0].value == 2
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.results[1].value == 5
    assert rolled_dice.results[2].is_active == True
    assert rolled_dice.results[2].value == 6

@pytest.mark.asyncio
async def test_apply_reroll_advanced(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    rolled_dice = RolledDice(6, [2, 5, 3, 3, 1, 2])
    assert len(rolled_dice.results) == 6
    rolled_dice = await rolled_dice.apply_reroll(3)

    assert len(rolled_dice.results) == 11
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[0].value == 2
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.results[1].value == 5
    assert rolled_dice.results[2].is_active == False
    assert rolled_dice.results[2].value == 3
    assert rolled_dice.results[3].is_active == False
    assert rolled_dice.results[3].value == 3
    assert rolled_dice.results[4].is_active == False
    assert rolled_dice.results[4].value == 1
    assert rolled_dice.results[5].is_active == False
    assert rolled_dice.results[5].value == 2

    assert rolled_dice.results[6].is_active == True
    assert rolled_dice.results[7].is_active == True
    assert rolled_dice.results[8].is_active == True
    assert rolled_dice.results[9].is_active == True

    assert rolled_dice.total == 35


@pytest.mark.asyncio
async def test_set_adv():
    rolled_dice = RolledDice(20, [8, 15])
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == True
    rolled_dice.set_advantage(True)
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.get_list_valid_values() == [15]
    assert rolled_dice.total == 15

@pytest.mark.asyncio
async def test_set_adv_same_value():
    rolled_dice = RolledDice(20, [15, 15])
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == True
    rolled_dice.set_advantage(True)
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.get_list_valid_values() == [15]
    assert rolled_dice.total == 15

@pytest.mark.asyncio
async def test_set_adv_same_value_double_advantage():
    rolled_dice = RolledDice(20, [15, 15, 15])
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.results[2].is_active == True
    rolled_dice.set_advantage(True, True)
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[1].is_active == False
    assert rolled_dice.results[2].is_active == True
    assert rolled_dice.get_list_valid_values() == [15]
    assert rolled_dice.total == 15

@pytest.mark.asyncio
async def test_set_adv_same_value_double_advantage():
    rolled_dice = RolledDice(20, [18, 2, 3])
    rolled_dice.set_advantage(True, True)
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == False
    assert rolled_dice.results[2].is_active == False
    assert rolled_dice.get_list_valid_values() == [18]
    assert rolled_dice.total == 18

    rolled_dice = RolledDice(20, [18, 2, 2])
    rolled_dice.set_advantage(True, True)
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == False
    assert rolled_dice.results[2].is_active == False
    assert rolled_dice.get_list_valid_values() == [18]
    assert rolled_dice.total == 18

    rolled_dice = RolledDice(20, [18, 2, 18])
    rolled_dice.set_advantage(True, True)
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == False
    assert rolled_dice.results[2].is_active == False
    assert rolled_dice.get_list_valid_values() == [18]
    assert rolled_dice.total == 18

@pytest.mark.asyncio
async def test_set_disadv():
    rolled_dice = RolledDice(20, [8, 15])
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == True
    rolled_dice.set_advantage(False)
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == False
    assert rolled_dice.get_list_valid_values() == [8]
    assert rolled_dice.total == 8

@pytest.mark.asyncio
async def test_set_disadv_same_value():
    rolled_dice = RolledDice(20, [8, 8])
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == True
    rolled_dice.set_advantage(False)
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.get_list_valid_values() == [8]
    assert rolled_dice.total == 8

@pytest.mark.asyncio
async def test_set_adv_and_desadv():
    rolled_dice = RolledDice(20, [5, 5])
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == True
    rolled_dice.set_advantage(True)
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.get_list_valid_values() == [5]
    assert rolled_dice.total == 5

    rolled_dice = RolledDice(20, [5, 5])
    assert rolled_dice.results[0].is_active == True
    assert rolled_dice.results[1].is_active == True
    rolled_dice.set_advantage(False)
    assert rolled_dice.results[0].is_active == False
    assert rolled_dice.results[1].is_active == True
    assert rolled_dice.get_list_valid_values() == [5]
    assert rolled_dice.total == 5
