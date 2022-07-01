from dices import roll_dice


async def reroll_and_send_text(context, dices_data=None, adv=True, number_of_dices=2):
    if number_of_dices > 3:
        number_of_dices = 3
    dice_result = await roll_dice(number_of_dices, 20)

    try:
        text = f"{context.message.author.display_name}: 1d20 => "
    except:
        text = f" 1d20 => "

    dice_1 = dice_2 = dice_3 = ""
    if dice_result[0] == 20 or dice_result[0] == 1:
        dice_1 = "!"
    if dice_result[1] == 20 or dice_result[1] == 1:
        dice_2 = "!"
    if number_of_dices == 3:
        if dice_result[2] == 20 or dice_result[2] == 1:
            dice_3 = "!"

    if adv:
        if number_of_dices == 2:
            if dice_result[0] >= dice_result[1]:
                text += f"[ {dice_result[0]}{dice_1},  ~~{dice_result[1]}{dice_2}~~ ]"
                result = dice_result[0]
            else:
                text += f"[ ~~{dice_result[0]}{dice_1}~~, {dice_result[1]}{dice_2} ]"
                result = dice_result[1]
        else:
            if dice_result[0] >= dice_result[1] and dice_result[0] >= dice_result[2]:
                text += f"[ {dice_result[0]}{dice_1},  ~~{dice_result[1]}{dice_2}~~,  ~~{dice_result[2]}{dice_3}~~ ]"
                result = dice_result[0]
            elif dice_result[1] >= dice_result[0] and dice_result[1] >= dice_result[2]:
                text += f"[ ~~{dice_result[0]}{dice_1}~~, {dice_result[1]}{dice_2}, ~~{dice_result[2]}{dice_3}~~, ]"
                result = dice_result[1]
            else:
                text += f"[ ~~{dice_result[0]}{dice_1}~~, ~~{dice_result[1]}{dice_2}~~, {dice_result[2]}{dice_3} ]"
                result = dice_result[2]

    else:
        if number_of_dices == 2:
            if dice_result[0] <= dice_result[1]:
                text += f"[ {dice_result[0]}{dice_1}, ~~{dice_result[1]}{dice_2}~~ ]"
                result = dice_result[0]
            else:
                text += f"[ ~~{dice_result[0]}{dice_1}~~, {dice_result[1]}{dice_2} ]"
                result = dice_result[1]
        else:
            if dice_result[0] <= dice_result[1] and dice_result[0] <= dice_result[2]:
                text += f"[ {dice_result[0]}{dice_1}, ~~{dice_result[1]}{dice_2}~~, ~~{dice_result[2]}{dice_3}~~ ]"
                result = dice_result[0]
            elif dice_result[1] <= dice_result[0] and dice_result[1] <= dice_result[3]:
                text += f"[ ~~{dice_result[0]}{dice_1}~~, {dice_result[1]}{dice_2}, ~~{dice_result[2]}{dice_3}~~ ]"
                result = dice_result[1]
            else:
                text += f"[ ~~{dice_result[0]}{dice_1}~~, ~~{dice_result[1]}{dice_2}~~, {dice_result[2]}{dice_3} ]"
                result = dice_result[2]

    if number_of_dices == 2:
        if dice_result[0] == 1 and dice_result[1] == 1 or dice_result[0] == 20 and dice_result[1] == 20:
            text += f" ¯\_(ツ)_/¯ \n"
    else:
        if dice_result[0] == 1 and dice_result[1] == 1 and dice_result[2] == 1 or dice_result[0] == 20 and dice_result[1] == 20 and dice_result[2] == 20:
            text += f" ¯\_(ツ)_/¯ HOLY FUCKING! Pode subir um nivel, isso é impossivel, sério mesmo, fala com o mestre e sobe um nivel, vc é o Deus dos dados. (eh uma chance em 8.000!!)\n"

    extra_signal = "+" if dices_data and not "+" in dices_data and not "-" in dices_data else ""
    final_text = f"{result}{extra_signal}{dices_data}=" if dices_data else ""
    result_final = result+eval(dices_data) if dices_data else result

    print(f"{text} \n{final_text} **{result_final}**")
    await context.send(f"{text} \n{final_text} **{result_final}**")


async def send_text(context, dice_list, first=True, dm=False):
    text = ""
    user = context.message.author
    if first:
        text = f"{user.display_name}: "

    for die in dice_list['result_minus_dies'] + dice_list['result_sum_dies']:

        text += f"``` {die.verbose}  => ["
        for index, dice in enumerate(die.list_of_result):
            comma = ""
            if index != len(die.list_of_result) -1:
                comma = ","
            bold = ""
            if dice == die.dice_base or dice == 1:
                bold = "!"
            text += f" {dice}{bold}{comma}"
        text += " ]```"

    if len(dice_list['result_minus_dies']) + len(dice_list['result_sum_dies']) == 0:
        dice_list['only_dices'] = ""

    msg = f"{text} \n {dice_list['only_dices']}{dice_list['additional']}= **{dice_list['result_final']}**"
    print(f"{msg} - DM?: {dm}")
    if not dm:
        await context.send(msg)
    else:
        await user.send(msg)
