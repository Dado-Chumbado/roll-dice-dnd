from config import roll_commands, initiative_commands, stats_commands, dice_commands
from dice import process, calculate_dice
from initiative import InitTable, clean_dex
from save_dice import DiceTable
from roll_view import multiple_d20_text, get_roll_text
from stats_db import show_general_info, show_session_stats
from interactions import (slash_command, slash_option,
                          OptionType)


# Instance of our dice table
init_items = InitTable()

# COMMANDS ================
@slash_command(
    name='test',
    description="TEST"
)
@slash_option(
    name="dice",
    description="String Option",
    required=False,
    opt_type=OptionType.STRING
)
async def command_test_dice(context, dice: str = "d20"):
    await context.send(f"pong  {context.author.nick} :{dice}")


@slash_command(
    name=roll_commands.get("dm_roll"),
    description="Roll private dice"
)
@slash_option(
    name="args",
    description="Dice expression. E.g: 1d10+1d4-1",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_dm_dice(context, args: str = "d20"):
    try:
        '''
            process("1d10+1d4-1")
            (['1d10 = [3]', '1d4 = [2]'], 4)
        '''
        rr = None
        data = ''.join(args)
        if not data:
            data = "d20"
        if data[-2:] in ["r1", "r2", "r3"]:
            rr = data[-2:]
            data = data.split(data[-2:])[0]

        for index, dice in enumerate(await process(context, data, ignore_d20=False, reroll=rr)):  # Parse and roll dice
            text, result_text, msg_result = await get_roll_text(context, dice, True if index == 0 else False)
            await context.author.send(f"{text}\n\n{result_text}{msg_result}")

        await context.send(f"Rolagem enviada para {context.author.nick}")
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=roll_commands.get("default"),
    description="Roll dice"
)
@slash_option(
    name="args",
    description="Dice expression. E.g: 1d10+1d4-1 OR saved dice name",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_dice(context, args: str = "d20"):
    try:
        rr = None
        data = ''.join(args)

        extra_text = ""
        # Check if is a die saved
        dice_saved = None
        try:
            dice = DiceTable(context.author.id)
            dice_saved = await dice.get(data)
        except Exception as e:
            print(f"Error: {e}")
            pass

        if dice_saved:
            data = dice_saved
            extra_text = f"\n## Rolando {args}: {data} \n\n\n"

        if data[-2:] in ["r1", "r2", "r3"]:
            rr = data[-2:]
            data = data.split(data[-2:])[0]

        for index, dice_list in enumerate(
                await process(context, data, ignore_d20=False, reroll=rr)):  # Parse and roll dice
            text, result_text, msg_result = await get_roll_text(context, dice_list, True if index == 0 else False)
            await context.send(f"{extra_text}{text}\n\n{result_text}{msg_result}")

    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=roll_commands.get("critical_damage"),
    description="Roll critical damage dice"
)
@slash_option(
    name="args",
    description="Max the first dice and double others. Expected dice exp OR saved dice name OR exp + extra damage",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="extra",
    description="Additional damage. Expected dice exp",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_critical_damage_dice(context, args: str, extra: str = ""):
    try:
        rr = None
        data = ''.join(args)

        extra_text = ""
        # Check if is a dice saved
        dice_saved = None
        try:
            dice = DiceTable(context.author.id)
            dice_saved = await dice.get(data)
        except Exception as e:
            print(f"Error: {e}")
            pass

        if extra != "":
            extra = f"+{extra}"

        if dice_saved:
            data = dice_saved + extra
            extra_text = f"\n## Rolando {args}: {data} \n\n\n"
        else:
            data += extra

        if data[-2:] in ["r1", "r2", "r3"]:
            rr = data[-2:]
            data = data.split(data[-2:])[0]

        for index, dice_list in enumerate(
                await process(context, data, ignore_d20=False, reroll=rr, critical=True)):  # Parse and roll dice
            text, result_text, msg_result = await get_roll_text(context, dice_list, True if index == 0 else False)
            await context.send(f"{extra_text}{text}\n\n{result_text}{msg_result}")

    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=roll_commands.get("advantage"),
    description="Roll dice with advantage"
)
@slash_option(
    name="args",
    description="Dice expression. E.g: d20+2d6 | 2d6-1 ",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_advantage_dice(context, args: str = ""):
    try:
        data = ''.join(args)
        # Clean up
        if data == "d20":
            data = ""
        data = data.replace("d20", "")
        data = await sanitize_input(data)

        dice = await calculate_dice(context, [[2, 20]], [], None, adv=True)
        text = ""
        try:
            # Try to evaluate extra data
            additional_dice = await process(context, data, ignore_d20=True)
            text = await multiple_d20_text(context, dice, additional_dice)
        except Exception as e:
            print(e)

        if text:
            await context.send(text)

    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=roll_commands.get("double_advantage"),
    description="Roll dice with double advantage"
)
@slash_option(
    name="args",
    description="Dice expression. E.g: 1d10",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_double_advantage_dice(context, args: str = ""):
    try:
        data = ''.join(args)
        # Clean up
        if data == "d20" or data == "1d20":
            data = ""
        data = data.replace("1d20", "").replace("d20", "")
        data = await sanitize_input(data)

        dice = await calculate_dice(context, [[3, 20]], [], None, adv=True)
        try:
            # Try to evaluate extra data
            additional_dice = await process(context, data, ignore_d20=True)
            text = await multiple_d20_text(context, dice, additional_dice)
        except:
            pass

        if text:
            await context.send(text)
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=roll_commands.get("disadvantage"),
    description="Roll dice with disadvantage"
)
@slash_option(
    name="args",
    description="Dice expression. E.g: d20 | 2d6+1",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_disadvantage_dice(context, args: str = ""):
    try:
        data = ''.join(args)
        # SANITIZE STRING -> MOVE THIS
        if data == "d20" or data == "1d20":
            data = ""
        data = data.replace("1d20", "").replace("d20", "")
        data = await sanitize_input(data)

        dice = await calculate_dice(context, [[2, 20]], [], None, adv=False)
        try:
            # Try to evaluate extra data
            additional_dice = await process(context, data, ignore_d20=True)
            text = await multiple_d20_text(context, dice, additional_dice)
        except Exception as e:
            await context.send(f"Exception {e}")

        if text:
            await context.send(text)
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=roll_commands.get("luck_roll"),
    description="Roll dice with LUCK!"
)
@slash_option(
    name="args",
    description="Dice expression. E.g: 1d10+1d4-1",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_luck_dice(context, args: str = ""):
    data = ''.join(args)
    # SANITIZE STRING -> MOVE THIS
    if data == "d20":
        data = ""
    data = data.replace("d20", "")
    data = await sanitize_input(data)

    dice = await calculate_dice(context, [[1, 20]], [], None, adv=None, luck=True)
    text = None
    try:
        # Try to evaluate extra data
        additional_dice = await process(context, data, ignore_d20=True)
        text = await multiple_d20_text(context, dice, additional_dice)
    except Exception as e:
        await context.send(f"Exception {e}")

    if text:
        await context.send(text)


async def sanitize_input(data):
    if data == "+" or data == "-":
        data = ""
    data = data.replace("++", "+")
    data = data.replace("--", "-")
    return data


# ============================================================================

@slash_command(
    name=initiative_commands.get("reset"),
    description="Reset the initiative table"
)
async def roll_reset_initiative(context):
    await init_items.reset(context.channel.name)
    # Delete last msg and send the new one
    if init_items.initiative_last_msg:
        try:
            await init_items.initiative_last_msg.delete()
        except Exception as e:
            print(f"Error deleting last initiative msg: {e}")

    init_items.initiative_last_msg = await context.send("OK, limpei a tabela. Bons dados :)")


@slash_command(
    name=initiative_commands.get("remove"),
    description="Remove item from table"
)
@slash_option(
    name="index",
    description="Initiative position to remove.",
    required=True,
    opt_type=OptionType.INTEGER
)
async def remove_initiative(context, index=0):
    try:
        await init_items.remove_index(context.channel.name, index)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                print(f"Error deleting last initiative msg: {e}")

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=initiative_commands.get("add_condition"),
    description="Add item from table"
)
@slash_option(
    name="index",
    description="Initiative position to remove.",
    required=True,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="args",
    description="Condition to add.",
    required=True,
    opt_type=OptionType.STRING
)
async def add_condition_initiative(context, index: int, args: str = ""):
    try:
        await init_items.add_condition(context.channel.name, index, args)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            await init_items.initiative_last_msg.delete()

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=initiative_commands.get("remove_condition"),
    description="Remove item from table"
)
@slash_option(
    name="index",
    description="Initiative position to remove.",
    required=True,
    opt_type=OptionType.INTEGER
)
async def remove_condition_initiative(context, index: int):
    try:
        await init_items.remove_condition(context.channel.name, index)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            await init_items.initiative_last_msg.delete()

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    except Exception as e:
        await context.send(f"Exception {e}")

@slash_command(
    name=initiative_commands.get("default"),
    description="Roll initiative!"
)
@slash_option(
    name="initiative",
    description="Character initiative modifier. E.g: 2",
    required=False,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="name",
    description="Character name. Default is the user name.",
    required=False,
    opt_type=OptionType.STRING
)
@slash_option(
    name="repeat",
    description="Number of times that the roll will be repeated. Default is 1.",
    required=False,
    opt_type=OptionType.INTEGER
)
async def roll_initiative(context, initiative: int = -99, name: str = "", repeat: int = 1):
    try:
        channel = context.channel.name

        if initiative == -99:
            print("Show init table")
            await init_items.show(context.channel.name, context)
            return

        for i in range(0, repeat):
            try:
                new_name = f"{name}" if name else context.author.nick
            except:
                new_name = f"{name}" if name else context.author.global_name

            if int(repeat) > 1:
                new_name = f"{new_name} {i+1}"

            dice = await calculate_dice(context, [[1, 20]], [], str(initiative))
            await init_items.add(channel, new_name, dice['only_dice'], str(initiative))

        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            await init_items.initiative_last_msg.delete()

        init_items.initiative_last_msg = await init_items.show(channel, context)

    except Exception as e:
        raise
        print(context.send(f"Erro: {e}"))

@slash_command(
    name=initiative_commands.get("next"),
    description="Move the initiative to the next character."
)
async def next_initiative(context):
    await init_items.next(context.channel.name)
    # Delete last msg and send the new one
    if init_items.initiative_last_msg:
        try:
            await init_items.initiative_last_msg.delete()
        except Exception as e:
            print(f"Error deleting last initiative msg: {e}")

    init_items.initiative_last_msg = await init_items.show(context.channel.name, context)


@slash_command(
    name=initiative_commands.get("previous"),
    description="Move the initiative to the previous character."
)
async def prev_initiative(context):
    await init_items.previous(context.channel.name)
    # Delete last msg and send the new one
    if init_items.initiative_last_msg:
        await init_items.initiative_last_msg.delete()

    init_items.initiative_last_msg = await init_items.show(context.channel.name, context)


@slash_command(
    name=initiative_commands.get("advantage"),
    description="Roll initiative with advantage!"
)
@slash_option(
    name="dex",
    description="Character dexterity modifier. E.g: 2",
    required=True,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="args",
    description="Character name. Default is the user name.",
    required=True,
    opt_type=OptionType.STRING
)
async def roll_initiative_advantage(context, dex: int = 0, args: str = ""):
    try:
        if not dex:
            await init_items.show(context.channel.name, context)
            return

        name = f"{args}" if args else context.author.nick

        dice = await calculate_dice(context, [[2, 20]], [], str(dex))

        text = await multiple_d20_text(context, dice, None)
        await context.send(text)
        await init_items.add(context.channel.name, name, dice['result_die'][0].larger(), str(dex))

        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            await init_items.initiative_last_msg.delete()

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)

    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=initiative_commands.get("force"),
    description="Force initiative. Add a character that already rolled dice into initiative table."
)
@slash_option(
    name="dice",
    description="Dice rolled for initiative.",
    required=True,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="dex",
    description="Character dexterity modifier",
    required=True,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="args",
    description="Character name.",
    required=True,
    opt_type=OptionType.STRING
)
async def force_initiative(context, dice: int = 0, dex: int = 0, args: str = ""):
    try:
        dice, _ = await clean_dex(str(dice))
        dex, neg = await clean_dex(str(dex))
        name = f"{args}" if args else context.author.nick

        await init_items.add(context.channel.name, name, dice, str(dex) if not neg else str(dex * -1))
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            await init_items.initiative_last_msg.delete()

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)

    except Exception as e:
        await context.send(f"Exception {e}")


#  STATS  =========================================================================

@slash_command(
    name=stats_commands.get("player"),
    description="Show stats per player in the channel"
)
async def command_show_stats_player(context):
    try:
        await show_general_info(context)
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=stats_commands.get("session"),
    description="Show stats per channel (session)"
)
async def command_show_stats_session(context, date=None, end_date=None):
    try:
        print(f"date: {date}")
        await show_session_stats(context, context.channel.name, date, end_date)
    except Exception as e:
        await context.send(f"Exception {e}")


#================================================================================================

@slash_command(
    name=dice_commands.get("save"),
    description="Save dice roll. E.g: 1d6+2"
)
@slash_option(
    name="name",
    description="Dice save name. E.g: Machado",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="args",
    description="Dice values to save. E.g: 1d6+2",
    required=True,
    opt_type=OptionType.STRING
)
async def save_dice(context,  name: str, args: str,):
    try:
        dice_items = DiceTable(context.author.id)
        await dice_items.add(name, args)
        await dice_items.show(context)

    except Exception as e:
        await context.send(f"Erro: {e}")


@slash_command(
    name=dice_commands.get("list"),
    description="List saved dice."
)
async def list_saved_dice(context):
    try:
        dice_items = DiceTable(context.author.id)
        await dice_items.show(context)

    except Exception as e:
        await context.send(f"Erro: {e}")


@slash_command(
    name=dice_commands.get("remove"),
    description="Remove saved dice by index."
)
@slash_option(
    name="index",
    description="Dice index to remove. E.g: 1",
    required=True,
    opt_type=OptionType.INTEGER
)
async def remove_dice(context, index: int):
    try:
        dice_items = DiceTable(context.author.id)
        await dice_items.remove_index(index)
        await dice_items.show(context)

    except Exception as e:
        await context.send(f"Erro: {e}")


@slash_command(
    name=dice_commands.get("reset"),
    description="Remove all saved dice."
)
async def reset_dice(context):
    try:
        dice_items = DiceTable(context.author.id)
        await dice_items.reset()
        await dice_items.show(context)

    except Exception as e:
        await context.send(f"Erro: {e}")