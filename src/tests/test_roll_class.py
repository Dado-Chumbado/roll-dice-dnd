import pytest

from ..core.roll import RolledDice, Dice, _roll_dice, generate_dice_roll


@pytest.mark.asyncio
async def test_roll_result_manual():

    rolled_dice = [18]
    rolled_dice =  RolledDice(20, rolled_dice)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 1
    assert rolled_dice.results == [Dice(value=18, is_active=True,
                                      is_critical=False, is_fail=False)]
    assert rolled_dice.total == 18
    assert rolled_dice.quantity == 1
    assert rolled_dice.dice_base == 20

    rolled_dice = [18, 6]
    rolled_dice =  RolledDice(20, rolled_dice)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 2
    assert rolled_dice.results == [Dice(value=18, is_active=True,
                                      is_critical=False, is_fail=False),
                                   Dice(value=6, is_active=True,
                                        is_critical=False, is_fail=False)
                                   ]
    assert rolled_dice.total == 24
    assert rolled_dice.quantity == 2
    assert rolled_dice.dice_base == 20

    rolled_dice = [10, 1]
    rolled_dice =  RolledDice(20, rolled_dice)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 2
    assert rolled_dice.results == [Dice(value=10, is_active=True,
                                      is_critical=False, is_fail=False),
                                   Dice(value=1, is_active=True,
                                        is_critical=False, is_fail=True)
                                   ]
    assert rolled_dice.total == 11
    assert rolled_dice.quantity == 2
    assert rolled_dice.dice_base == 20


@pytest.mark.asyncio
async def test_roll_result(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b)

    rolled_dice =  await generate_dice_roll(1, 20)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 1
    assert rolled_dice.results == [Dice(value=20, is_active=True,
                                      is_critical=True, is_fail=False)]
    assert rolled_dice.total == 20
    assert rolled_dice.quantity == 1
    assert rolled_dice.dice_base == 20

    rolled_dice = await generate_dice_roll(4, 8)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 4
    assert rolled_dice.results == [Dice(value=8, is_active=True,
                                      is_critical=True, is_fail=False),
                                   Dice(value=8, is_active=True,
                                        is_critical=True, is_fail=False),
                                   Dice(value=8, is_active=True,
                                        is_critical=True, is_fail=False),
                                   Dice(value=8, is_active=True,
                                        is_critical=True, is_fail=False),
                                   ]
    assert rolled_dice.total == 32
    assert rolled_dice.quantity == 4
    assert rolled_dice.dice_base == 8



@pytest.mark.asyncio
async def test_roll_class(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b)

    results = await _roll_dice(1, 20)
    rolled_dice =  RolledDice(20, results)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 1
    assert rolled_dice.results == [Dice(value=20, is_active=True,
                                      is_critical=True, is_fail=False)]
    assert rolled_dice.total == 20
    assert rolled_dice.quantity == 1
    assert rolled_dice.dice_base == 20

@pytest.mark.asyncio
async def test_roll_class_result(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b/2)

    results = await _roll_dice(2, 20)
    rolled_dice =  RolledDice(20, results)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 2
    assert rolled_dice.results == [Dice(value=10, is_active=True,
                                      is_critical=False, is_fail=False),
                                   Dice(value=10, is_active=True,
                                      is_critical=False, is_fail=False)]
    assert rolled_dice.total == 20
    assert rolled_dice.quantity == 2
    assert rolled_dice.dice_base == 20

    assert rolled_dice.get_list_valid_values() == [10, 10]


@pytest.mark.asyncio
async def test_roll_class_multiple_dice(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b)

    results = await _roll_dice(2, 6)
    rolled_dice = RolledDice(6, results)

    assert type(rolled_dice) == RolledDice
    assert len(rolled_dice.results) == 2
    assert rolled_dice.results == [Dice(value=6, is_active=True,
                                        is_critical=True, is_fail=False),
                                   Dice(value=6, is_active=True,
                                        is_critical=True, is_fail=False)]

    results = await _roll_dice(4, 12)
    rolled_dice = RolledDice(12, results)

    assert type(rolled_dice) == RolledDice
    assert len(rolled_dice.results) == 4
    assert rolled_dice.results == [Dice(value=12, is_active=True,
                                        is_critical=True, is_fail=False),
                                   Dice(value=12, is_active=True,
                                        is_critical=True, is_fail=False),
                                   Dice(value=12, is_active=True,
                                        is_critical=True, is_fail=False),
                                   Dice(value=12, is_active=True,
                                        is_critical=True, is_fail=False),
                                   ]

@pytest.mark.asyncio
async def test_roll_and_reroll(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b - b/2)

    results = await _roll_dice(2, 20)
    rolled_dice =  RolledDice(20, results)

    assert type(rolled_dice)  == RolledDice
    assert len(rolled_dice.results) == 2
    assert rolled_dice.results == [Dice(value=10, is_active=True,
                                      is_critical=False, is_fail=False),
                                   Dice(value=10, is_active=True,
                                      is_critical=False, is_fail=False)]
    assert rolled_dice.total == 20
    assert rolled_dice.quantity == 2
    assert rolled_dice.dice_base == 20

    assert len(rolled_dice.results) == 2
    assert rolled_dice.get_list_valid_values() == [10, 10]

    monkeypatch.setattr('random.randint', lambda a, b: b)

    rolled_dice = await rolled_dice.apply_reroll(12)

    assert rolled_dice.quantity == 4
    assert rolled_dice.dice_base == 20

    assert len(rolled_dice.results) == 4
    assert rolled_dice.get_list_valid_values() == [20, 20]
    assert rolled_dice.results == [Dice(value=10, is_active=False,
                                      is_critical=False, is_fail=False),
                                   Dice(value=10, is_active=False,
                                      is_critical=False, is_fail=False),
                                   Dice(value=20, is_active=True,
                                        is_critical=True, is_fail=False),
                                   Dice(value=20, is_active=True,
                                        is_critical=True, is_fail=False),
                                   ]

@pytest.mark.asyncio
async def test_roll_class_advantage(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b)

    results = await _roll_dice(2, 20)
    rolled_dice =  RolledDice(20, results)

    rolled_dice.set_advantage(True)

    assert type(rolled_dice) == RolledDice
    assert len(rolled_dice.results) == 2
    assert rolled_dice.quantity_active == 1
    assert rolled_dice.total == rolled_dice.larger()

@pytest.mark.asyncio
async def test_roll_class_double_advantage(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b)

    results = await _roll_dice(3, 20)
    rolled_dice =  RolledDice(20, results)
    value_target = max(rolled_dice.get_list_valid_values())
    rolled_dice.set_advantage(True, True)

    assert type(rolled_dice) == RolledDice
    assert len(rolled_dice.results) == 3
    assert rolled_dice.quantity_active == 1
    assert value_target == rolled_dice.total

@pytest.mark.asyncio
async def test_roll_class_real_random_double_advantage():

    results = await _roll_dice(3, 20)
    rolled_dice =  RolledDice(20, results)

    value_target = max(rolled_dice.get_list_valid_values())
    rolled_dice.set_advantage(True, True)

    assert type(rolled_dice) == RolledDice
    assert len(rolled_dice.results) == 3
    assert rolled_dice.quantity_active == 1
    assert value_target == rolled_dice.total
