import asyncio
import re
import os
import logging
from core.stats_db import insert_roll
from core.roll import generate_dice_roll, Roll

logger = logging.getLogger(__name__)


async def parse_dice(data: str):
    """
    Parses the dice expression from the input string and returns a tuple of positive and negative dice.

    Args:
        data (str): The dice expression (e.g., "2d6 + 1d20 - 3d8").

    Returns:
        tuple: (parsed_positive, parsed_negative) where each is a list of (number, dice) tuples.
    """
    # This regex will match both positive and negative dice rolls.
    dice_pattern = r'([+-]?)(\d+)?d(\d+)'

    # Find all dice rolls in the data string
    parsed_dice = re.findall(dice_pattern, data)

    parsed_positive = []
    parsed_negative = []

    for sign, number, dice in parsed_dice:
        # Default number of dice to 1 if not specified
        number = min(int(number), int(os.getenv("limit_of_dice_per_roll", 100)))
        dice = min(int(dice), int(os.getenv("limit_of_die_size", 100)))
        # Ensure that the dice is not overflow the limit

        # Separate positive and negative dice
        if sign == '-':
            parsed_negative.append((number, dice))
        else:
            parsed_positive.append((number, dice))

    return parsed_positive, parsed_negative


async def parse_additional(data, positive_die, negative_die):

    # If the string does not start with a "+" or "-", prepend a "+"
    if data and not data[0] in "+-":
        data = "+" + data

    def remove_dice_expressions(data, dice_expressions):
        for count, size in sorted(dice_expressions,
                                  key=lambda x: -len(f"{x[0]}d{x[1]}")):
            dice_expr = f"{count}d{size}"
            # Use regex to match whole dice expressions
            data = re.sub(rf"[\+\-]?{re.escape(dice_expr)}", "", data)
        return data

    # Remove positive dice expressions
    data = remove_dice_expressions(data, positive_die)

    # Remove negative dice expressions
    data = remove_dice_expressions(data, negative_die)

    # Clean up any multiple "+" or "-" signs
    data = re.sub(r'\+\+', '+', data)
    data = re.sub(r'--', '-', data)
    data = re.sub(r'\+-', '-', data)
    data = re.sub(r'-\+', '-', data)

    return data.strip()


async def handle_repeat(dice_data):
    repeat = re.findall('(\d+)(?=\*)', dice_data) + re.findall('(\d+)(?=x)', dice_data)
    if repeat:
        repeat = int(repeat[0])
        repeat = min(repeat, 20)  # Limit repeat to 20
        dice_data = dice_data.split("x")[1] if "x" in dice_data else dice_data.split("*")[1]
    else:
        repeat = 1
    return dice_data, repeat


async def validate_dice_expression(dice_data, adv=None, double_adv=False):
    # Fix any missing elements in the dice expression
    dice_data, rr = await fix_dice_expression(dice_data, adv, double_adv)

    # Use parse_dice to extract dice rolls
    parsed_positive, parsed_negative = await parse_dice(dice_data)

    # Combine positive and negative dice expressions
    all_dice = parsed_positive + parsed_negative

    # Check if there are any valid dice expressions
    if not all_dice:
        logger.error(f"Invalid dice expression: {dice_data}")
        raise ValueError(f"Invalid dice expression: {dice_data}")

    # Use parse_additional to remove all valid dice expressions and see what's left
    remaining_data = await parse_additional(dice_data, parsed_positive,
                                            parsed_negative)

    # Allow valid arithmetic expressions to remain, like "+2", "-1", or "+2-1"
    if remaining_data:
        # Check if the remaining data is a valid arithmetic expression
        if not re.match(r'^[+\-]?\d+([+\-]\d+)*(\s*r\d+)?$', remaining_data):
            raise ValueError(
                f"Invalid remaining data in expression: {remaining_data}")

    return dice_data, rr


async def fix_dice_expression(dice_data, adv=None, double_adv=False):
    """
    Fix and normalize dice expression strings.

    Parameters:
    - dice_data (str): The raw dice expression.
    - adv (bool): Indicates advantage.
    - double_adv (bool): Indicates double advantage.

    Returns:
    - tuple: The fixed dice expression and any reroll indicator (e.g., "r1").
    """
    # Remove any whitespace and lowercase all letters
    dice_data = re.sub(r'\s+', '', dice_data).lower()

    # Remove leading "+" if present (it's redundant)
    if dice_data.startswith('+'):
        dice_data = dice_data[1:]

    # Check if data is just "0"
    if dice_data == "0":
        dice_data = "d20"

    # Handle cases where the expression starts with a number or "-"
    if re.match(r'^\d+([\+\-]|$)', dice_data):
        dice_data = f'1d20+{dice_data}'
    elif re.match(r'^-\d+([\+\-]|$)', dice_data):
        dice_data = f'1d20{dice_data}'

    # Replace d0 with d20
    dice_data = re.sub(r'd0', 'd20', dice_data)

    # Add a "d" before numbers followed by a + or -
    if re.match(r'^\d+(?=[\+\-])', dice_data):
        dice_data = 'd' + dice_data

    # Append a "1" if the string starts with a die expression without a quantity (e.g., "d20" to "1d20")
    dice_data = re.sub(r'(?<!\d)d(\d+)', r'1d\1', dice_data)

    # Handle advantage and double advantage
    if adv is not None:
        # Set the number of d20s based on double_adv
        num_d20 = '3d20' if double_adv else '2d20'

        # If '1d20' or 'd20' exists, replace it with the appropriate roll for advantage
        if re.search(r'\b(2d20|1d20|d20)\b', dice_data):
            dice_data = re.sub(r'\b(1d20|d20)\b', num_d20, dice_data)
        else:
            # If no d20 present, add the d20 expression at the beginning
            dice_data = f'{num_d20}+{dice_data}'

    # Apply limits for dice count and size
    dice_pattern = r'(\d*)d(\d+)'

    def apply_dice_limits(match):
        # Get the number of dice and the size of the dice
        number = match.group(1) or '1'
        dice_size = match.group(2)

        # Apply limits from environment variables (or defaults)
        number = min(int(number),
                     int(os.getenv("limit_of_dice_per_roll", 100)))
        dice_size = min(int(dice_size),
                        int(os.getenv("limit_of_die_size", 100)))

        return f'{number}d{dice_size}'

    dice_data = re.sub(dice_pattern, apply_dice_limits, dice_data)

    # Clean up any extra "+" or "-" signs
    dice_data = dice_data.replace("++", "+").replace("--", "-")

    # Handle reroll indicators (e.g., "r1", "r2")
    rr = ''
    if dice_data[-2:] in ["r1", "r2", "r3", "r4", "r5"]:
        dice_data, rr = dice_data[:-2], dice_data[-2:]

    return dice_data, rr


async def process_input_dice(context, dice_data: str, adv: bool = None,
                             critical: bool = None, double_adv: bool = False) -> (list, list, list):
    # Handle repeat logic
    dice_data, repeat = await handle_repeat(dice_data)

    # Validate dice expression
    dice_data, reroll = await validate_dice_expression(dice_data, adv, double_adv)

    # Parse dice
    dice_positive, dice_negative = await parse_dice(dice_data)
    additional = await parse_additional(dice_data, dice_positive, dice_negative)

    if critical:
        dice_positive = [(int(item[0])*2, item[1]) for item in dice_positive]

    # Roll dice multiple times, return a list of Roll
    dice_roll_list = [
        await calculate_dice(context, dice_data, dice_positive, dice_negative,
                             additional, reroll, adv=adv, critical=critical, double_adv=double_adv)
        for _ in range(repeat)
    ]
    # Return the list of Roll + the data used to generate it
    return dice_roll_list, dice_data, reroll


async def calculate_dice(context, dice_data: str, dice_positive: [],
                         dice_negative: [], additional: str,
                         reroll=None, adv=None, critical=False, double_adv=False) -> Roll:
    roll = Roll(dice_data, additional)

    try:
        # Handle positive dice rolls (subtractions)
        for index, (number_of_dice, dice_size) in enumerate(dice_positive):
            is_critical = critical
            rolled_dice = await generate_dice_roll(number_of_dice, dice_size,
                                                   reroll=reroll,
                                                   critical=is_critical if is_critical and index == 0 else False)

            if adv is not None and index == 0:
                rolled_dice.set_advantage(adv, double_adv)

            roll.add_rolled_dice_sum(rolled_dice)

        # Handle negative dice rolls (subtractions)
        for number_of_dice, dice_size in dice_negative:
            rolled_dice = await generate_dice_roll(number_of_dice, dice_size)
            roll.add_rolled_dice_subtract(rolled_dice)

        # Evaluate additional modifiers
        additional_eval = 0
        if additional:
            additional_eval = eval(additional)  # Evaluate the additional modifiers string
        roll.additional_eval = additional_eval

        # Register dice rolls for stats, if enabled
        if os.getenv("save_stats_db") in ["True", "1"]:
            asyncio.create_task(register_dice_stats(context, roll))

        return roll

    except Exception as e:
        logger.error(f"Error processing dice: {e}")


async def register_dice_stats(context, roll: Roll):
    """
    Register the dice roll results in the stats tracking system.

    Parameters:
    - context: The context of the roll (contains author, channel, etc.)
    - rolled_dice: The list of dice results to be registered.
    """
    for rolled_dice in roll.rolled_sum_dice + roll.rolled_subtract_die:
        for die in rolled_dice.results:

            insert_roll(
                context.author.id,
                context.channel.name,
                f"d{rolled_dice.dice_base}",
                die.value,
                die.is_critical,
                die.is_fail,
            )
