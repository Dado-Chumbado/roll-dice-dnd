import logging

logger = logging.getLogger(__name__)


async def get_roll_text(context, roll, dice_data, reroll, extra_info="", skip_resume=False, skip_user_and_dice=False):
    try:
        username = f"{context.author.nick}"
    except:
        username = f"No name"

    text = ""
    if not skip_user_and_dice:
        text = f"{username} rolled **{dice_data}{reroll}** {extra_info}: \n"

    try:
        text_sum, op_desc_sum = await generate_dice_text(roll.rolled_sum_dice,
                                                         True)
        text_sub, op_desc_sub = await generate_dice_text(roll.rolled_subtract_die,
                                                         False)

        text += text_sum
        text += text_sub
        operation_description = f"{op_desc_sum[2:]}{op_desc_sub}"

        if not skip_resume:
            # Add spaces around characters that are not digits
            text_additional = "".join(f" {c} " if not c.isdigit() else c for c in roll.additional)
            text += f"\n\n {operation_description}{text_additional} = **{roll.total_roll}**"

        return text
    except Exception as e:
        logging.error(f"An error occurred while generating the roll text: {e}")
        await context.send(f"Exception {e}")


async def generate_dice_text(dice_data, is_sum=True):
    text = ""
    operation_description = ""
    for rolled_die in dice_data:
        text += f"\n> {rolled_die.quantity_active}d{rolled_die.dice_base} => ["

        # Filter all dice (active and not active)
        for i, die in enumerate(rolled_die.get_list_valid_dice()):
            comma = "," if i != rolled_die.quantity - 1 else ''
            alert = "!" if die.is_critical or die.is_fail else ''
            if rolled_die.dice_base == 20 and die.is_critical:
                alert = ":sparkles:"

            strike = "~~" if not die.is_active else ''

            text += f" {strike}{die.value}{alert}{strike}{comma}"

        text += f" ]"
        operation_description += f"{' + ' if is_sum else ' - '}{rolled_die.total}"
    return text, operation_description

# TODO: Implement this:
#     if len(dice_obj.list_of_result) == 2 and only_d20.count(1) == total_die_roll \
#             or only_d20.count(20) == total_die_roll:
#         text += f"\n ¯\_(ツ)_/¯ DADO CHUMBADO!!  uma chance em 400!\n"
#     elif only_d20.count(1) == total_die_roll \
#             or only_d20.count(20) == total_die_roll:
#         text += f"\n ¯\_(ツ)_/¯ DADO CHUMBADO!! uma chance em 8.000!!\n"
