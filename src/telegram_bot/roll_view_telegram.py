"""Telegram-specific roll formatting using HTML parse mode."""

import logging

logger = logging.getLogger(__name__)


async def get_roll_text_telegram(context, roll, dice_data, reroll, extra_info="", skip_resume=False, skip_user_and_dice=False):
    """Generate roll text formatted for Telegram HTML mode."""
    try:
        username = f"{context.author.nick}"
    except Exception:
        username = "No name"

    text = ""
    if not skip_user_and_dice:
        text = f"{username} rolled <b>{dice_data}{reroll}</b> {extra_info}: \n"

    try:
        text_sum, op_desc_sum = await generate_dice_text_telegram(roll.rolled_sum_dice, True)
        text_sub, op_desc_sub = await generate_dice_text_telegram(roll.rolled_subtract_die, False)

        text += text_sum
        text += text_sub
        operation_description = f"{op_desc_sum[2:]}{op_desc_sub}"

        if not skip_resume:
            text_additional = "".join(f" {c} " if not c.isdigit() else c for c in roll.additional)
            text += f"\n\n {operation_description}{text_additional} = <b>{roll.total_roll}</b>"

        return text
    except Exception as e:
        logger.error(f"An error occurred while generating the roll text: {e}", exc_info=True)
        await context.send("Sorry, I couldn't format the roll results properly.")


async def generate_dice_text_telegram(dice_data, is_sum=True):
    """Generate dice text formatted for Telegram HTML mode."""
    text = ""
    operation_description = ""
    for rolled_die in dice_data:
        text += f"\n  {rolled_die.quantity_active}d{rolled_die.dice_base} =&gt; ["

        for i, die in enumerate(rolled_die.get_list_valid_dice()):
            comma = "," if i != rolled_die.quantity - 1 else ""
            alert = "!" if die.is_critical or die.is_fail else ""
            if rolled_die.dice_base == 20 and die.is_critical:
                alert = "✨"

            if not die.is_active:
                text += f" <s>{die.value}{alert}</s>{comma}"
            else:
                text += f" {die.value}{alert}{comma}"

        text += " ]"
        operation_description += f"{' + ' if is_sum else ' - '}{rolled_die.total}"
    return text, operation_description
