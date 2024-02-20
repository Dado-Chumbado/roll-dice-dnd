#!/usr/bin/env python3

import json
import os
from interactions import Client, Intents, listen, slash_command, slash_option, OptionType
from dice import process, calculate_dice
from initiative import InitTable, clean_dex
from save_dice import DiceTable
from roll_view import multiple_d20_text, get_roll_text
from stats_db import show_general_info, show_session_stats

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# read our environment variables
with open("./config.json", "r") as env:
    ENV = json.load(env)

COMMAND_CHAR = ENV['command_char']

COMMAND_ROLL = ENV['command_roll']
COMMAND_ROLL_DOUBLE_ADVANTAGE = ENV["command_roll_double_advantage"]
COMMAND_ROLL_ADVANTAGE = ENV["command_roll_advantage"]
COMMAND_ROLL_DISADVANTAGE = ENV["command_roll_disadvantage"]
COMMAND_ROLL_LUCK_DICE = ENV["command_roll_luck"]
COMMAND_DM_ROLL = ENV['command_dm_roll']
#  =======================================
COMMAND_RESET = ENV["command_reset"]
COMMAND_ROLL_INITIATIVE = ENV["command_initiative"]
COMMAND_ROLL_INITIATIVE_ADV = ENV["command_initiative_adv"]
COMMAND_FORCE_INITIATIVE = ENV["command_force_initiative"]
COMMAND_REMOVE_INITIATIVE = ENV["command_remove_initiative"]
COMMAND_ADD_CONDITION_INITIATIVE = ENV["command_add_condition"]
COMMAND_REMOVE_CONDITION_INITIATIVE = ENV["command_remove_condition"]
COMMAND_NEXT_INITIATIVE = ENV["command_next_initiative"]
COMMAND_PREV_INITIATIVE = ENV["command_previous_initiative"]

COMMAND_SHOW_STATS_PLAYER = ENV["command_show_stats_player"]
COMMAND_SHOW_STATS_SESSION = ENV["command_show_stats_session"]

COMMAND_SAVE_DICE = ENV["command_save_dice"]
COMMAND_LIST_SAVED_DICE = ENV["command_list_saved_dice"]
COMMAND_REMOVE_SAVED_DICE = ENV["command_remove_saved_dice"]
COMMAND_RESET_SAVED_DICE = ENV["command_reset_saved_dice"]

STATS_ENABLE = True if ENV["stats"] == "1" else False

# read our discord access token
with open("secrets.json", "r") as secrets:
    DISCORD_TOKEN = json.load(secrets)["discord"]
init_items = InitTable()

# intents = discord.Intents.default()
# intents.message_content = True
bot = Client(command_prefix=[COMMAND_CHAR],
             description="Roll dices and control initiative table",
             intents=Intents.DEFAULT)


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
    name=COMMAND_DM_ROLL,
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
        await context.send(f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL} 1d20+2 por exemplo")
        await context.send(f"Exception {e}")


@slash_command(
    name=COMMAND_ROLL,
    description="Roll dice"
)
@slash_option(
    name="args",
    description="Dice expression. E.g: 1d10+1d4-1",
    required=False,
    opt_type=OptionType.STRING
)
async def command_roll_dice(context, args: str = "d20"):
    try:
        rr = None
        data = ''.join(args)
        if data[-2:] in ["r1", "r2", "r3"]:
            rr = data[-2:]
            data = data.split(data[-2:])[0]

        for index, dice_list in enumerate(
                await process(context, data, ignore_d20=False, reroll=rr)):  # Parse and roll dice
            text, result_text, msg_result = await get_roll_text(context, dice_list, True if index == 0 else False)
            await context.send(f"{text}\n\n{result_text}{msg_result}")

    except Exception as e:
        await context.send(f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL} 1d20+2 por exemplo")
        await context.send(f"Exception {e}")


@slash_command(
    name=COMMAND_ROLL_ADVANTAGE,
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
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo")
        await context.send(f"Exception {e}")


@slash_command(
    name=COMMAND_ROLL_DOUBLE_ADVANTAGE,
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
        if data == "d20":
            data = ""
        data = data.replace("d20", "")
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
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo \n"
            f"Voce tbm pode rolar com {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +d6+1")
        await context.send(f"Exception {e}")


@slash_command(
    name=COMMAND_ROLL_DISADVANTAGE,
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
        if data == "d20":
            data = ""
        data = data.replace("d20", "")
        data = await sanitize_input(data)

        dice = await calculate_dice(context, [[2, 20]], [], None, adv=False)
        try:
            # Try to evaluate extra data
            additional_dice = await process(context, data, ignore_d20=True)
            text = await multiple_d20_text(context, dice, additional_dice)
        except:
            raise

        if text:
            await context.send(text)
    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo \n"
            f"Voce tbm pode rolar com {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +d6+1")
        await context.send(f"Exception {e}")


@slash_command(
    name=COMMAND_ROLL_LUCK_DICE,
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

    dice = await calculate_dice(context, [[1, 20]], [], None, luck=True)
    text = None
    try:
        # Try to evaluate extra data
        additional_dice = await process(context, data, ignore_d20=True)
        text = await multiple_d20_text(context, dice, additional_dice)
    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_LUCK_DICE} +2 por exemplo")
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
    name=COMMAND_RESET,
    description="Reset the initiative table"
)
async def roll_reset_initiative(context):
    await init_items.reset(context.channel.name)
    # Delete last msg and send the new one
    if init_items.initiative_last_msg:
        await init_items.initiative_last_msg.delete()

    init_items.initiative_last_msg = await context.send("OK, limpei a tabela. Bons dados :)")


@slash_command(
    name=COMMAND_REMOVE_INITIATIVE,
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
            await init_items.initiative_last_msg.delete()

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=COMMAND_ADD_CONDITION_INITIATIVE,
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
    name=COMMAND_REMOVE_CONDITION_INITIATIVE,
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
    name=COMMAND_ROLL_INITIATIVE,
    description="Roll initiative!"
)
@slash_option(
    name="dex",
    description="Character dexterity modifier. E.g: 2",
    required=False,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="repeat",
    description="Number of times that the roll will be repeated. Default is 1.",
    required=False,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="args",
    description="Character name. Default is the user name.",
    required=False,
    opt_type=OptionType.STRING
)
async def roll_initiative(context, dex: int = -99, repeat: int = 1, args: str = ""):
    try:
        channel = context.channel.name

        if dex == -99:
            print("Show init table")
            await init_items.show(context.channel.name, context)
            return

        for i in range(0, repeat):
            name = f"{args}" if args else context.author.nick
            if repeat > 1:
                name += f" {i + 1}"

            dice = await calculate_dice(context, [[1, 20]], [], str(dex))
            await init_items.add(channel, name, dice['only_dice'], str(dex))

        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            await init_items.initiative_last_msg.delete()

        init_items.initiative_last_msg = await init_items.show(channel, context)

    except Exception as e:
        await context.send(f"Erro: {e}")
        raise

@slash_command(
    name=COMMAND_NEXT_INITIATIVE,
    description="Move the initiative to the next character."
)
async def next_initiative(context):
    await init_items.next(context.channel.name)
    # Delete last msg and send the new one
    if init_items.initiative_last_msg:
        await init_items.initiative_last_msg.delete()

    init_items.initiative_last_msg = await init_items.show(context.channel.name, context)


@slash_command(
    name=COMMAND_PREV_INITIATIVE,
    description="Move the initiative to the previous character."
)
async def prev_initiative(context):
    await init_items.previous(context.channel.name)
    # Delete last msg and send the new one
    if init_items.initiative_last_msg:
        await init_items.initiative_last_msg.delete()

    init_items.initiative_last_msg = await init_items.show(context.channel.name, context)


@slash_command(
    name=COMMAND_ROLL_INITIATIVE_ADV,
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
    name=COMMAND_FORCE_INITIATIVE,
    description="Force initiative. Add a character that already rolled dices into initiative table."
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
    name=COMMAND_SHOW_STATS_PLAYER,
    description="Show stats per player in the channel"
)
async def command_show_stats_player(context):
    try:
        await show_general_info(context)
    except Exception as e:
        await context.send(f"Exception {e}")


@slash_command(
    name=COMMAND_SHOW_STATS_SESSION,
    description="Show stats per channel (session)"
)
async def command_show_stats_session(context, date=None, end_date=None):
    try:
        print(f"date: {date}")
        await show_session_stats(bot, context, context.channel.name, date, end_date)
    except Exception as e:
        await context.send(f"Exception {e}")


#================================================================================================

@slash_command(
    name=COMMAND_SAVE_DICE,
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
    name=COMMAND_LIST_SAVED_DICE,
    description="List saved dice."
)
async def list_saved_dice(context):
    try:
        dice_items = DiceTable(context.author.id)
        await dice_items.show(context)

    except Exception as e:
        await context.send(f"Erro: {e}")


@slash_command(
    name=COMMAND_REMOVE_SAVED_DICE,
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
        raise


@slash_command(
    name=COMMAND_RESET_SAVED_DICE,
    description="Remove all saved dice."
)
async def reset_dice(context):
    try:
        dice_items = DiceTable(context.author.id)
        await dice_items.reset()
        await dice_items.show(context)

    except Exception as e:
        await context.send(f"Erro: {e}")
        raise


@listen()
async def on_ready():
    print(f"I'm logged in as {bot.user.display_name} !\n Statistics enable: {STATS_ENABLE}.")


bot.start(DISCORD_TOKEN)
