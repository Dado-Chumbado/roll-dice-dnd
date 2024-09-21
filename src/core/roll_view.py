

async def get_roll_text(context, roll, dice_data, reroll):
    try:
        username = f"{context.author.nick}"
    except:
        username = f"No name"
    text = f"{username} rolled **{dice_data}{reroll}**: \n"

    try:
        text_sum, op_desc_sum = await generate_dice_text(roll.rolled_sum_dice,
                                                         True)
        text_sub, op_desc_sub = await generate_dice_text(roll.rolled_subtract_die,
                                                         False)

        text += text_sum
        text += text_sub
        operation_description = f"{op_desc_sum[2:]}{op_desc_sub}"

        # Add spaces around characters that are not digits
        text_additional = "".join(f" {c} " if not c.isdigit() else c for c in roll.additional)
        text += f"\n\n {operation_description}{text_additional} = **{roll.total_roll}**"

        return text
    except Exception as e:
        raise


async def generate_dice_text(dice_data, is_sum=True):
    text = ""
    operation_description = ""
    for rolled_die in dice_data:
        text += f"\n> {rolled_die.quantity_active}d{rolled_die.dice_base} => ["

        # Filter all dice (active and not active)
        for i, die in enumerate(rolled_die.get_list_valid_dices()):
            comma = "," if i != rolled_die.quantity - 1 else ''
            alert = "!" if die.is_critical or die.is_fail else ''
            if rolled_die.dice_base == 20 and die.is_critical:
                alert = ":sparkles:"

            strike = "~~" if not die.is_active else ''

            text += f" {strike}{die.value}{alert}{strike}{comma}"

        text += f" ]"
        operation_description += f"{' + ' if is_sum else ' - '}{rolled_die.total}"
    return text, operation_description



# async def multiple_d20_text(context, dice_result_dict, additional_data=None):
#     dice_obj = dice_result_dict['result_die'][0]
#     dice_obj.set_validation_adv()
#
#     text, text_result, msg_result = await get_roll_text(context, dice_result_dict)
#     result = dice_result_dict['result_final']
#
#     only_d20 = [sublist[0] for sublist in dice_obj.list_of_result]
#     total_die_roll = len(dice_obj.list_of_result)
#
#     if len(dice_obj.list_of_result) == 2 and only_d20.count(1) == total_die_roll \
#             or only_d20.count(20) == total_die_roll:
#         text += f"\n ¯\_(ツ)_/¯ DADO CHUMBADO!!  uma chance em 400!\n"
#
#     elif only_d20.count(1) == total_die_roll \
#             or only_d20.count(20) == total_die_roll:
#         text += f"\n ¯\_(ツ)_/¯ DADO CHUMBADO!! uma chance em 8.000!!\n"
#
#     if not additional_data:
#         return text
#
#     additional_data = additional_data[0]
#
#     # If there is no additional dice to calculate, return the result with the value evaluated
#     if not additional_data['result_die'] and not additional_data['result_minus_die']:
#         # msg, msg_operation, msg_result
#         result_final = result + additional_data['result_final']
#         signal = ""
#         if additional_data['additional_eval'] > 0:
#             signal = "+"
#         elif additional_data['additional_eval'] == 0:
#             signal = ""
#             additional_data['result_final'] = ""
#
#         return f"{text} \n\n {result}{signal}{additional_data['result_final']}= **{result_final}**"
#
#     # Continue with a adv + dice + additional
#     additional_text = await get_roll_text(context, additional_data, False)
#     result_final = result + additional_data['result_final']
#
#     return f"{text} \n{additional_text[0]}\n\n {result}+{additional_text[1]}= **{result_final}**"