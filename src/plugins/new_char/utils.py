import logging

logger = logging.getLogger(__name__)


async def get_new_char_roll_text(context, roll, mode: str = "new"):
    try:
        username = f"{context.author.nick}"
    except:
        username = f"No name"

    text = f"{username} rolled a new char stats: \n"

    try:
        text_sum, operation_description = await _generate_dice_text(roll)

        text += text_sum
        operation_description = f"{operation_description[2:]}"

        # Add spaces around characters that are not digits
        # text_additional = "".join(f" {c} " if not c.isdigit() else c for c in roll.additional)
        text += f"\n# {operation_description}"
        text += f"\nTotal roll: **{roll.total_roll}**"

        if roll.total_dice_result == 69:
            text += " nice"

        # thresholds depend on mode: "classic" uses older values, "new" uses higher thresholds
        if mode == "classic":
            t_low, t_mid, t_high = 60, 70, 90
        else:
            t_low, t_mid, t_high = 65, 75, 95

        if roll.total_dice_result <= t_low:
            text += " \n\n# Holy cow, this is pure :shit:"
        elif roll.total_dice_result < t_mid:
            text += " \n\n-# Recommended to reroll, you're a little unlucky"
        elif roll.total_dice_result >= t_high:
            text += " \n\n# :crown: JESUS FUCKING CHRIST BRO! :crown: "

        return text
    except Exception as e:
        logging.error(f"An error occurred while generating the roll text: {e}")
        await context.send(f"Exception {e}")


async def _generate_dice_text(dice_data):
    text = "\n"
    target_total_column = 55  # Total column will always start at character 55
    operation_description = ""

    header = f"{'Dice':<10} {'Rolls'}{' ' * (target_total_column - 15)}Total"
    separator = "-" * (len(header))
    text += f"{header}\n{separator}\n"

    for rolled_die in dice_data.rolled_sum_dice:
        # Dice notation
        dice_label = f"{rolled_die.quantity}d{rolled_die.dice_base}"

        # Build roll display
        rolled_results = rolled_die.get_list_valid_dice()
        roll_display = ""
        for i, die in enumerate(rolled_results):
            comma = "," if i != rolled_die.quantity - 1 else ""
            alert = "!" if die.is_critical or die.is_fail else ""
            strike = "~~" if not die.is_active else ""
            roll_display += f"{strike}{die.value}{alert}{strike}{comma} "
        roll_display = f"[{roll_display.strip()}]"

        # Calculate how many spaces are needed to align Total
        base_string = f"{dice_label:<10} {roll_display}"
        spaces_needed = max(1, target_total_column - len(base_string))
        padding = " " * spaces_needed

        text += f"{base_string}{padding}{rolled_die.total}\n"
        operation_description += f", {rolled_die.total}"

    return text, operation_description


