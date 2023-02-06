async def get_roll_text(context, dice_result_dict, first=True):
    text = ""
    user = context.message.author
    if first:
        text = f"{user.display_name}: \n"

    try:
        list_of_dices = []
        for dice in dice_result_dict['result_dies']:
            list_of_dices.append(dice)

        if dice_result_dict['result_minus_dies']:
            for dice in dice_result_dict['result_minus_dies']:
                list_of_dices.append(dice)

        for die in list_of_dices:
            text += f"\n> *{die.verbose}* => ["
            for index, dice_rolled in enumerate(die.list_of_result):
                dice, confirmed = dice_rolled
                comma = bold = ""
                if index != len(die.list_of_result) - 1:
                    comma = ","
                if dice == die.dice_base or dice == 1:
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
                          f"{dice_result_dict['only_dices']}{dice_result_dict['additional']}", \
                          f"= **{dice_result_dict['result_final']}**"

        return msg, msg_operation, msg_result
    except Exception as e:
        print(e)
        raise


async def multiple_d20_text(context, dice_result_dict, additional_data=None, adv=True):
    dice_obj = dice_result_dict['result_dies'][0]
    dice_obj.set_validation_adv()

    text, text_result, msg_result = await get_roll_text(context, dice_result_dict, first=True)
    result = dice_result_dict['result_final']

    if len(dice_obj.list_of_result) == 2 and dice_obj.list_of_result.count(1) == len(dice_obj.list_of_result) \
            or dice_obj.list_of_result.count(20) == len(dice_obj.list_of_result):
        text += f"\n ¯\_(ツ)_/¯ uma chance em 400!\n"
    elif dice_obj.list_of_result.count(1) == len(dice_obj.list_of_result) \
            or dice_obj.list_of_result.count(20) == len(dice_obj.list_of_result):
        text += f"\n ¯\_(ツ)_/¯ HOLY FUCKING! uma chance em 8.000!!\n"

    if not additional_data:
        return text

    additional_data = additional_data[0]

    if not additional_data['result_dies'] and not additional_data['result_minus_dies']:
        # msg, msg_operation, msg_result
        additional_text = "", f"{additional_data['result_final']}", ""
        result_final = result + additional_data['result_final']
        return f"{text} \n{additional_text[0]}\n {result}+{additional_text[1]}= **{result_final}**"

    # Continue with a adv + dices + additional
    additional_text = await get_roll_text(context, additional_data, False)
    result_final = result + additional_data['result_final']
    return f"{text} \n{additional_text[0]}\n\n {result}+{additional_text[1]}= **{result_final}**"