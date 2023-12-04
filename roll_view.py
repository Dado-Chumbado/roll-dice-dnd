async def get_roll_text(context, dice_result_dict, first=True):
    text = ""
    try:
        user = context.message.author
        if first:
            text = f"{user.display_name}: \n"
    except:
        text = f"Test: \n"

    try:
        list_of_dice = []
        for dice in dice_result_dict['result_die']:
            list_of_dice.append(dice)

        if dice_result_dict['result_minus_die']:
            for dice in dice_result_dict['result_minus_die']:
                list_of_dice.append(dice)

        for die in list_of_dice:
            text += f"\n> *{die.verbose}* => ["
            for index, dice_rolled in enumerate(die.list_of_result):
                dice, confirmed = dice_rolled
                comma = bold = ""
                if index != len(die.list_of_result) - 1:
                    comma = ","
                if dice == int(die.dice_base) or dice == 1:
                    bold = "!"
                if not confirmed:
                    text += f" ~~{dice}{bold}~~{comma}"
                else:
                    text += f" {dice}{bold}{comma}"
            text += " ]"

        if not dice_result_dict['additional']:
            dice_result_dict['additional'] = ""

        if len(dice_result_dict['additional']) > 0:
            if not "+" in dice_result_dict['additional'][0] and not "-" in dice_result_dict['additional'][0]:
                dice_result_dict['additional'] = f"+{dice_result_dict['additional']}"

        print(dice_result_dict)
        msg, msg_operation, msg_result = f"{text}", \
                          f"{dice_result_dict['only_dice']}{dice_result_dict['additional']}", \
                          f"= **{dice_result_dict['result_final']}**"

        return msg, msg_operation, msg_result
    except Exception as e:
        print(e)
        raise


async def multiple_d20_text(context, dice_result_dict, additional_data=None):
    dice_obj = dice_result_dict['result_die'][0]
    dice_obj.set_validation_adv()

    text, text_result, msg_result = await get_roll_text(context, dice_result_dict, first=True)
    result = dice_result_dict['result_final']

    only_d20 = [sublist[0] for sublist in dice_obj.list_of_result]
    total_die_roll = len(dice_obj.list_of_result)

    if len(dice_obj.list_of_result) == 2 and only_d20.count(1) == total_die_roll \
            or only_d20.count(20) == total_die_roll:
        text += f"\n ¯\_(ツ)_/¯ uma chance em 400!\n"

    elif only_d20.count(1) == total_die_roll \
            or only_d20.count(20) == total_die_roll:
        text += f"\n ¯\_(ツ)_/¯ DADO CHUMBADO!! uma chance em 8.000!!\n"

    if not additional_data:
        return text

    additional_data = additional_data[0]

    if not additional_data['result_die'] and not additional_data['result_minus_die']:
        # msg, msg_operation, msg_result
        additional_text = "", f"{additional_data['result_final']}", ""
        result_final = result + additional_data['result_final']

        signal = "+" if additional_data['result_final'] > 0 else ""

        return f"{text} \n{additional_text[0]}\n {result}{signal}{additional_text[1]}= **{result_final}**"

    # Continue with a adv + dice + additional
    additional_text = await get_roll_text(context, additional_data, False)
    result_final = result + additional_data['result_final']
    return f"{text} \n{additional_text[0]}\n\n {result}+{additional_text[1]}= **{result_final}**"