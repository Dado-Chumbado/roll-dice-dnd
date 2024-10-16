# test_dice_engine.py
import pytest
from core.dice_engine import parse_dice, parse_additional, \
    validate_dice_expression, handle_repeat, fix_dice_expression, \
    process_input_dice, calculate_dice
from core.roll import Roll, generate_dice_roll


@pytest.mark.asyncio
async def test_simple_parse_dice():
    # Test simple cases
    data = "1d20"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20)]
    assert negative_dice == []

    data = "1d20+1d4"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20), (1, 4)]
    assert negative_dice == []

    data = "1d20-1d4"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20)]
    assert negative_dice == [(1, 4)]

    data = "1d20+1d4"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20), (1, 4)]
    assert negative_dice == []

    data = "1d20-2d4"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20)]
    assert negative_dice == [(2, 4)]

    data = "1d20-2"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20)]
    assert negative_dice == []

    data = "1d20+2"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20)]
    assert negative_dice == []


@pytest.mark.asyncio
async def test_parse_dice():

    # Test case with positive and negative dice
    data = "2d6+3d8-1d4"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(2, 6), (3, 8)]
    assert negative_dice == [(1, 4)]

    # Test case with no negative dice
    data = "4d10+5d12"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(4, 10), (5, 12)]
    assert negative_dice == []

    # Test case with no positive dice
    data = "-2d6-1d20"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == []
    assert negative_dice == [(2, 6), (1, 20)]

    data = "-2d6-1d20+2"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == []
    assert negative_dice == [(2, 6), (1, 20)]

    data = "1d20-1d4+2"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(1, 20)]
    assert negative_dice == [(1, 4)]

    data = "1000d1000"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(100, 100)]
    assert negative_dice == []


@pytest.mark.asyncio
async def test_advanced_parse_dice():

    data = "2d20+2d6+3d8-1d4+2+1-4+123-34d4+23d8-25d10-5d100+1"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(2, 20), (2, 6), (3, 8), (23, 8)]
    assert negative_dice == [(1, 4), (34, 4), (25, 10), (5, 100)]

    data = "2d20+2d6+22d6+100d6+2d6+2d6-2d6-22d6-2d20"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(2, 20), (2, 6), (22, 6), (100, 6), (2, 6), (2, 6)]
    assert negative_dice == [(2, 6), (22, 6), (2, 20)]


@pytest.mark.asyncio
async def test_parse_additional():
    # Example where dice values are stripped out
    data = "2d6+1d8+4-1d4"
    positive_die = [('2', '6'), ('1', '8')]
    negative_die = [('1', '4')]

    result = await parse_additional(data, positive_die, negative_die)
    assert result == "+4"

    # Example with only additional modifiers
    data = "+5"
    positive_die = []
    negative_die = []

    result = await parse_additional(data, positive_die, negative_die)
    assert result == "+5"

    data = "+5-2+1"
    positive_die = []
    negative_die = []

    result = await parse_additional(data, positive_die, negative_die)
    assert result == "+5-2+1"

    data = "2d6-5"
    positive_die = [('2', '6')]
    negative_die = []

    result = await parse_additional(data, positive_die, negative_die)
    assert result == "-5"

    data = "1d20+5-1"
    positive_die = [('1', '20')]
    negative_die = []

    result = await parse_additional(data, positive_die, negative_die)
    assert result == "+5-1"


@pytest.mark.asyncio
async def test_advanced_parse_additional():

    data = "+1"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == []
    assert negative_dice == []

    result = await parse_additional(data, positive_dice, negative_dice)
    assert result == "+1"

    data = "2d20+2d6+3d8-1d4+2+1-4+123-34d4+23d8-25d10-5d100+1"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(2, 20), (2, 6), (3, 8), (23, 8)]
    assert negative_dice == [(1, 4), (34, 4), (25, 10), (5, 100)]

    result = await parse_additional(data, positive_dice, negative_dice)
    assert result == "+2+1-4+123+1"

    data = "2d20+2d6+22d6+99d6+2d6+2d6-2d6-22d6-2d20+1"
    positive_dice, negative_dice = await parse_dice(data)

    assert positive_dice == [(2, 20), (2, 6), (22, 6), (99, 6), (2, 6), (2, 6)]
    assert negative_dice == [(2, 6), (22, 6), (2, 20)]

    result = await parse_additional(data, positive_dice, negative_dice)

    assert result == "+1"


@pytest.mark.asyncio
async def test_valid_dice_expression():

    valid_expressions = [
        "2d20",
        "d6+3",
        "d20-5",
        "10d8+4",
        "d12",
        "d20+1",
        "2d6r2", # Reroll command
        "4d4 r2",  # Reroll command
        "1d20-d4",
        "1d20-d4+1",
        "1d20-d4+2-1",
        "2d20+d6-d4+1-2",
        "2d20+2d6+3d8-1d4+2+1-4+123-34d4+23d8-25d10-5d100+1",
        "101d12", # Exceeds limit of dice per roll
        "10d100",  # Exceeds limit of dice per roll
        "101d101",  # Exceeds limit of dice per roll
        "2d6 + 3d10 + 1",
        "d20 - 2",
        "3d6 +1+d6 r2",
        "3D20-1 r2",
        "20d4 R2"
    ]
    for expr in valid_expressions:
        try:
            dice_data, reroll = await validate_dice_expression(expr)
            assert type(dice_data) == str
            if expr[-2:] in ["r1", "r2", "r3", "r4", "r5"]:
                print(expr, dice_data)
                assert reroll != ''

        except ValueError:
            pytest.fail(f"Unexpected ValueError for valid expression: {expr}")

@pytest.mark.asyncio
async def test_valid_dice_reroll_r2():

    valid_expressions = [
        "2d6r2", # Reroll command
        "4d4 r2",  # Reroll command
        "2d6 + 3d10 + 1r2",
        "d20 - 2r2",
        "3d6 +1+d6 r2",
        "3D20-1 r2",
        "20d4 R2"
    ]
    for expr in valid_expressions:
        try:
            dice_data, reroll = await validate_dice_expression(expr)
            assert type(dice_data) == str
            if expr[-2:] in ["r1", "r2", "r3", "r4", "r5"]:
                print(expr, dice_data)
                assert reroll == 'r2'

        except ValueError:
            pytest.fail(f"Unexpected ValueError for valid expression: {expr}")

@pytest.mark.asyncio
async def test_invalid_dice_expression():

    invalid_expressions = [
        "2d",
        "d",
        "3d",
        "d20d10",
        "2d6r",
        "2d8+r2",
        "3d10 r",
        "r23d10",
        "4d12r2+1d4",
        "2d-4",
        "d"
        "99999d99999+d"
    ]
    for expr in invalid_expressions:
        with pytest.raises(ValueError):
            dice_data, _ = await validate_dice_expression(expr)
            assert type(dice_data) == str


@pytest.mark.asyncio
async def test_only_modifier_dice_expression():

    valid_expressions = [
        "5",
        "2",
        "7",
        "10",
        "69",
        "420",
        "-5",
        "-2",
        "-7",
        "-10",
        "-69",
        "-420",
    ]
    for expr in valid_expressions:
        await validate_dice_expression(expr)

@pytest.mark.asyncio
async def test_fix_dice_expression_only_numbers_valid():
    # Test valid dice expressions and their corrections
    test_cases = [
        ("5", "1d20+5"),
        ("2", "1d20+2"),
        ("7", "1d20+7"),
        ("10", "1d20+10"),
        ("69", "1d20+69"),
        ("420", "1d20+420"),
        ("-5", "1d20-5"),
        ("-2", "1d20-2"),
        ("-7", "1d20-7"),
        ("-10", "1d20-10"),
        ("-69", "1d20-69"),
        ("-420", "1d20-420"),
    ]

    for dice_data, expected in test_cases:
        result = await fix_dice_expression(dice_data)
        result = result[0]
        assert result == expected, f"Expected '{expected}' but got '{result}'"

@pytest.mark.asyncio
async def test_handle_repeat_valid():
    # Test valid repeat multipliers
    test_cases = [
        ("3*d6", 3, "d6"),
        ("5x4d8", 5, "4d8"),
        ("5x4d8+2d6+1", 5, "4d8+2d6+1"),
        ("2xd12-d4", 2, "d12-d4"),
        ("d12", 1, "d12"),  # No repeat multiplier
        ("2x3d4", 2, "3d4"),  # Ensure it only takes the first multiplier
        ("2x2d6r2", 2, "2d6r2"),
    ]

    for dice_data, expected_repeat, expected_dice in test_cases:
        dice_data_result, repeat = await handle_repeat(dice_data)
        assert repeat == expected_repeat, f"Expected repeat {expected_repeat} but got {repeat}"
        assert dice_data_result == expected_dice, f"Expected dice data '{expected_dice}' but got '{dice_data_result}'"

@pytest.mark.asyncio
async def test_handle_repeat_out_of_bounds():
    # Test repeat multiplier out of bounds
    test_cases = [
        ("30*d6", 20, "d6"),  # Limit should apply
        ("100x2d8", 20, "2d8"),  # Limit should apply
    ]

    for dice_data, expected_repeat, expected_dice in test_cases:
        dice_data_result, repeat = await handle_repeat(dice_data)
        assert repeat == expected_repeat, f"Expected repeat {expected_repeat} but got {repeat}"
        assert dice_data_result == expected_dice, f"Expected dice data '{expected_dice}' but got '{dice_data_result}'"

@pytest.mark.asyncio
async def test_handle_repeat_invalid():
    # Test invalid repeat multipliers
    test_cases = [
        ("1d20", 1, "1d20"),  # Invalid multiplier, should default to 1
        ("1d6+2d4", 1, "1d6+2d4"),    # Invalid multiplier, should default to 1
        ("1d6", 1, "1d6"),
        ("2d6+1d4+1", 1, "2d6+1d4+1"),
    ]

    for dice_data, expected_repeat, expected_dice in test_cases:
        dice_data_result, repeat = await handle_repeat(dice_data)
        assert repeat == expected_repeat, f"Expected repeat {expected_repeat} but got {repeat}"
        assert dice_data_result == expected_dice, f"Expected dice data '{expected_dice}' but got '{dice_data_result}'"

@pytest.mark.asyncio
async def test_fix_dice_expression_valid():
    # Test valid dice expressions and their corrections
    test_cases = [
        ("20+5", "1d20+5"),  # Missing 'd' should be added
        ("d20-5", "1d20-5"),  # No change needed
        ("d6", "1d6"),  # Missing number before 'd' should be added
        ("5d10+2d4+1", "5d10+2d4+1"),  # No change needed
        ("d4+3d6", "1d4+3d6"),  # Missing number before 'd' should be added
        ("3+d4", "1d3+1d4"),  # Add missing '+' at start
        ("d4+3", "1d4+3"),
        ("1d4+d6", "1d4+1d6"),
        ("2d8-d8", "2d8-1d8"),
        ("--5+10", "-5+10"),  # Clean up double signs
        ("1000d10", "100d10")
    ]

    for dice_data, expected in test_cases:
        result = await fix_dice_expression(dice_data)
        result = result[0]
        assert result == expected, f"Expected '{expected}' but got '{result}'"

@pytest.mark.asyncio
async def test_fix_dice_expression_exceed_limit(monkeypatch):

    # set limit to test env limit_of_dice_per_roll and limit_of_dice_size
    monkeypatch.setenv("limit_of_dice_per_roll", '10')
    monkeypatch.setenv("limit_of_die_size", '10')

    # Test ignoring the 'd20' fix when ignore_d20 is True
    test_cases = [
        ("20d6", "10d6"),
        ("1000d100", "10d10"),
        ("2d10+30d6+2+1-d4", "2d10+10d6+2+1-1d4"),
        ("39d60-345d999-10000", "10d10-10d10-10000"),
        ("2d6+9999", "2d6+9999"),
        ("10d10+9d9+8d8-99999", "10d10+9d9+8d8-99999"),
    ]

    for dice_data, expected in test_cases:
        result = await fix_dice_expression(dice_data)
        result = result[0]
        assert result == expected, f"Expected '{expected}' but got '{result}'"

@pytest.mark.asyncio
async def test_fix_dice_expression_d0():

    # Test ignoring the 'd20' fix when ignore_d20 is True
    test_cases = [
        ("20d0", "20d20"),
        ("d0+d6-4", "1d20+1d6-4"),
        ("2d10+4d0+2+1-d4", "2d10+4d20+2+1-1d4"),
    ]

    for dice_data, expected in test_cases:
        result = await fix_dice_expression(dice_data)
        assert result[0] == expected, f"Expected '{expected}' but got '{result}'"

@pytest.mark.asyncio
async def test_process_input_dice_valid(monkeypatch):
    # Mock random.randint to return fixed results for reproducibility
    monkeypatch.setattr('random.randint', lambda a, b: b)

    # Test valid dice expressions and their results
    test_cases = [
        (None, "d20", None, False,
         [await generate_dice_roll(1, 20)]),

        (None, "1d20-5", None, False,
         [await generate_dice_roll(1, 20)]),

        (None, "2d8+8", None, False,
         [await generate_dice_roll(2, 8)]),

        (None, "2d6+2", None, False,
         [await generate_dice_roll(2, 6)]),

        (None, "1d2-d4", None, False,
         [await generate_dice_roll(1, 2),
          await generate_dice_roll(1, 4)]),

        (None, "101d101-d4+2-1", None, False,
         [await generate_dice_roll(100, 100),
          await generate_dice_roll(1, 4)]),
    ]

    for context, dice_data, adv, critical, expected in test_cases:
        result = await process_input_dice(context, dice_data, adv=adv, critical=critical)

        result, dice_data, reroll = result # Since we receive a list of Rolls
        result = result[0]
        assert type(result) == Roll
        assert type(result.rolled_sum_dice) == list
        assert type(result.rolled_subtract_die) == list
        assert type(result.rolled_sum_dice[0].results) == list

        assert result.rolled_sum_dice[0].results == expected[0].results
        assert result.rolled_sum_dice[0].dice_base == expected[0].dice_base
        assert result.rolled_sum_dice[0].total == expected[0].total
        assert result.rolled_sum_dice[0].quantity == expected[0].quantity

        assert result.rolled_sum_dice[0].results[0].value == expected[0].results[0].value
        assert result.rolled_sum_dice[0].results[0].is_critical == expected[0].results[0].is_critical

        assert type(dice_data) == str
        assert reroll == ''

        if result.additional_eval:
            assert result.total_roll != expected[0].total

@pytest.mark.asyncio
async def test_process_input_dice_invalid():
    # Test invalid dice expressions
    test_cases = [
        (None, "", None, False), # Nothing
        (None, "abc", None, False),  # Non-dice string
        (None, "d", None, False),  # Missing number
        (None, "d20+", None, False), # Incomplete expression
    ]

    for context, dice_data, adv, critical in test_cases:
        with pytest.raises(ValueError):
            await process_input_dice(context, dice_data,
                                     adv=adv, critical=critical)


@pytest.mark.asyncio
async def test_process_input_dice_edge_cases(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    # set limit to test env limit_of_dice_per_roll and limit_of_dice_size
    monkeypatch.setenv("limit_of_dice_per_roll", '5')
    monkeypatch.setenv("limit_of_die_size", '10')

    # Test edge cases and boundary values
    test_cases = [
        (None, "1000d10", None, False,
         [await generate_dice_roll(5, 10)]),  # Minimal dice
        (None, "2d100", None, False,
         [await generate_dice_roll(2, 10)]),  # Maximal dice
        (None, "6d12+4d4", None, False,
         [await generate_dice_roll(5, 10),
          await generate_dice_roll(4, 4)]),    # Repeat test
        (None, "2d20+d4+d6-2d4+10-2", None, False,
         [await generate_dice_roll(2, 10),
          await generate_dice_roll(1, 4),
          await generate_dice_roll(1, 6),
          await generate_dice_roll(2, 4)]),   # Mixed operators
        (None, "2d20-d4+d6-2d8+10-2+1", None, False,
         [await generate_dice_roll(2, 10),
          await generate_dice_roll(1, 4),
          await generate_dice_roll(1, 6),
          await generate_dice_roll(2, 8)]),  # Mixed operators
    ]

    for context, dice_data, adv, critical, expected in test_cases:
        result = await process_input_dice(context, dice_data,
                                          adv=adv, critical=critical)
        result, dice_data, reroll = result  # Since we receive a list of Rolls
        result = result[0]
        assert type(result) == Roll
        assert type(result.rolled_sum_dice) == list
        assert type(result.rolled_subtract_die) == list
        assert type(result.rolled_sum_dice[0].results) == list

        assert result.rolled_sum_dice[0].results == expected[0].results
        assert result.rolled_sum_dice[0].dice_base == expected[0].dice_base
        assert result.rolled_sum_dice[0].total == expected[0].total
        assert result.rolled_sum_dice[0].quantity == expected[0].quantity

        assert result.rolled_sum_dice[0].results[0].value == \
               expected[0].results[0].value
        assert result.rolled_sum_dice[0].results[0].is_critical == \
               expected[0].results[0].is_critical

        if result.additional_eval:
            assert result.total_roll != expected[0].total


@pytest.mark.asyncio
async def test_process_input_dice_reroll():

    # Test edge cases and boundary values
    test_cases = [
        (None, "10d6r4", None, False),  # Minimal dice
        (None, "10d6r2", None, False),  # Maximal dice
          # Mixed operators
    ]

    for context, dice_data, adv, critical in test_cases:
        result, dice_data, reroll = await process_input_dice(context, dice_data,
                                          adv=adv, critical=critical)
        result = result[0]
        assert 'r' in reroll
        assert result.rolled_sum_dice[0].quantity >= 10

@pytest.mark.asyncio
async def test_calculate_dice_no_additional(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    dice_data = "2d6+1d4"
    dice_positive = [(2, 6)]
    dice_negative = [(1, 4)]
    additional = ''

    result = await calculate_dice(None, dice_data, dice_positive,
                                  dice_negative, additional)

    assert type(result) == Roll
    assert type(result.rolled_sum_dice) == list
    assert type(result.rolled_subtract_die) == list
    assert type(result.rolled_sum_dice[0].results) == list

    assert result.rolled_sum_dice[0].total == 12
    assert result.rolled_subtract_die[0].total == 4
    assert result.rolled_sum_dice[0].dice_base == 6
    assert result.rolled_subtract_die[0].dice_base == 4
    assert result.additional_eval == 0
    assert result.total_dice_result == 8
    assert result.total_roll == 8


@pytest.mark.asyncio
async def test_calculate_dice_with_additional(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    dice_data = "2d6+1d4+6-1"
    dice_positive = [(2, 6)]
    dice_negative = [(1, 4)]
    additional = "+6-1"

    result = await calculate_dice(None, dice_data, dice_positive,
                                  dice_negative, additional)

    assert type(result) == Roll
    assert type(result.rolled_sum_dice) == list
    assert type(result.rolled_subtract_die) == list
    assert type(result.rolled_sum_dice[0].results) == list

    assert result.rolled_sum_dice[0].total == 12
    assert result.rolled_subtract_die[0].total == 4
    assert result.rolled_sum_dice[0].dice_base == 6
    assert result.rolled_subtract_die[0].dice_base == 4
    assert result.additional_eval == 5
    assert result.total_dice_result == 8
    assert result.total_roll == 13


@pytest.mark.asyncio
async def test_calculate_dice_with_additional_complex(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    dice_data = "2d6+1d8+6-1+3"
    dice_positive = [(2, 6), (1, 8)]
    dice_negative = [(2, 4)]
    additional = "+6-1+3"

    result = await calculate_dice(None, dice_data, dice_positive,
                                  dice_negative, additional)

    assert type(result) == Roll
    assert type(result.rolled_sum_dice) == list
    assert type(result.rolled_subtract_die) == list
    assert type(result.rolled_sum_dice[0].results) == list

    assert result.rolled_sum_dice[0].total == 12
    assert result.rolled_subtract_die[0].total == 8
    assert result.rolled_sum_dice[1].total == 8
    assert result.rolled_subtract_die[0].total == 8
    assert result.rolled_sum_dice[0].dice_base == 6
    assert result.rolled_sum_dice[1].dice_base == 8
    assert result.rolled_subtract_die[0].dice_base == 4
    assert result.additional_eval == 8
    assert result.total_dice_result == 12
    assert result.total_roll == 20


@pytest.mark.asyncio
async def test_calculate_dice_with_reroll(monkeypatch):
    # set limit to test env limit_of_dice_per_roll and limit_of_dice_size
    monkeypatch.setenv("limit_of_dice_per_roll", '10')
    monkeypatch.setenv("limit_of_die_size", '20')

    dice_data = "10d6+4r8r8"
    dice_positive = [(10, 6)]
    dice_negative = []
    additional = "+4"
    reroll = 'r8'

    result = await calculate_dice(None, dice_data, dice_positive,
                                  dice_negative, additional, reroll=reroll)

    assert type(result) == Roll
    assert type(result.rolled_sum_dice) == list
    assert type(result.rolled_subtract_die) == list
    assert type(result.rolled_sum_dice[0].results) == list

    assert result.rolled_sum_dice[0].total >= 8
    assert result.rolled_sum_dice[0].dice_base == 6
    assert result.additional_eval == 4

    assert result.rolled_sum_dice[0].quantity_active == 10
    assert result.rolled_sum_dice[0].quantity > 10

@pytest.mark.asyncio
async def test_calculate_dice_with_critical(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: 2)

    # Test edge cases and boundary values
    test_cases = [
        (None, "1d6+5", [6, 2]),
        (None, "1d6+1d4+5", [6, 2]),
        (None, "2d6+1d4+5", [6, 6, 2, 2]),
        (None, "3d4+2d4+5", [4, 4, 4, 2, 2, 2]),
        (None, "1d8+2d4+5-1", [8, 2]),
        (None, "2d8-2d4+5-1", [8, 8, 2, 2]),
        (None, "1d8-1d12+5-1", [8, 2]),

    ]

    for context, dice_data, expected in test_cases:
        result, _, _ = await process_input_dice(context, dice_data,
                                          critical=True)
        result = result[0]
        assert result.rolled_sum_dice[0].get_list_valid_values() == expected

@pytest.mark.asyncio
async def test_number_dice_rolled(monkeypatch):
    # Mock random.randint to return predictable results
    monkeypatch.setattr('random.randint', lambda a, b: b)

    # Test edge cases and boundary values
    test_cases = [
        (None, "1d20+1d4+5", [[20], [4]]),
        (None, "1d20+2d4+5", [[20], [4, 4]]),
        (None, "1d20+1d4+2d6+5", [[20], [4], [6, 6]]),
    ]

    for context, dice_data, expected in test_cases:
        result, _, _ = await process_input_dice(context, dice_data)
        result = result[0]
        for i in range(len(expected)):
            assert result.rolled_sum_dice[i].get_list_valid_values() == expected[i]
