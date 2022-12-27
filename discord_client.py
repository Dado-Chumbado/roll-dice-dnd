#!/usr/bin/env python3

import json

from discord.ext import commands
import os
from dices import process, calculate_dices, process_luck_dice
from initiative import InitTable, clean_dex
from roll import send_roll_text, multiple_d20_text
from stats_db import show_general_info, show_session_stats

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# read our environment variables
with open("./config.json", "r") as env:
    ENV = json.load(env)

COMMAND_CHAR = ENV['command_char']
ALTERNATIVE_COMMAND_CHAR = ENV['alternative_char']
COMMAND_HELPER = ENV['command_helper']

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
COMMAND_FORCE_INITIATIVE= ENV["command_force_initiative"]
COMMAND_REMOVE_INITIATIVE = ENV["command_remove_initiative"]
COMMAND_ADD_CONDITION_INITIATIVE = ENV["command_add_condition"]
COMMAND_REMOVE_CONDITION_INITIATIVE = ENV["command_remove_condition"]

COMMAND_SHOW_STATS_PLAYER = ENV["command_show_stats_player"]
COMMAND_SHOW_STATS_SESSION = ENV["command_show_stats_session"]

STATS_ENABLE = True if ENV["stats"] == "1" else False

# read our discord access token
with open("secrets.json", "r") as secrets:
    DISCORD_TOKEN = json.load(secrets)["discord"]
init_items = InitTable()

bot = commands.Bot(
    command_prefix=[COMMAND_CHAR, ALTERNATIVE_COMMAND_CHAR],
    description="Roll a random dices, normal or with advantages/disadvantages and control initiative table"
)


# COMMANDS ================
@bot.command(
    name=COMMAND_DM_ROLL,
    description="Roll private dices?"
)
async def command_roll_dm_dices(context, *args):
    try:
        '''
            process("1d10+1d4-1")
            (['1d10 = [3]', '1d4 = [2]'], 4)
        '''
        data = ''.join(args)
        if not data:
            data = "d20"

        for index, dice in enumerate(await process(context, data)):   # Parse and roll dices
            await send_roll_text(context, dice, True if index == 0 else False, True)

    except Exception as e:
        await context.send(f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL} 1d20+2 por exemplo")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL,
    description="Roll dices?"
)
async def command_roll_dices(context, *args):
    try:
        data = ''.join(args)
        if not data:
            data = "d20"

        for index, dice_list in enumerate(await process(context, data)):   # Parse and roll dices
            await send_roll_text(context, dice_list, True if index == 0 else False)

    except Exception as e:
        await context.send(f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL} 1d20+2 por exemplo")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_ADVANTAGE,
    description="Roll dices with advantage?"
)
async def command_roll_advantage_dices(context, *args):
    try:
        data = ''.join(args)

        # Clean up
        if data == "d20":
            data = None
        else:
            data = data.replace("d20", "")

        dices = await calculate_dices(context, [[2, 20]], [], None)
        try:
            # Try to evaluate extra data
            additional_dices = await process(context, data, ignore_d20=True)
            await multiple_d20_text(context, dices['result_dies'][0].list_of_result, additional_dices, True)
        except:
            await multiple_d20_text(context, dices['result_dies'][0].list_of_result, data, True)

    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_DOUBLE_ADVANTAGE,
    description="Roll dices with double advantage?"
)
async def command_roll_double_advantage_dices(context, *args):
    try:
        data = ''.join(args)
        # Clean up
        if data == "d20":
            data = None
        else:
            data = data.replace("d20", "")

        dices = await calculate_dices(context, [[3, 20]], [], None)
        try:
            # Try to evaluate extra data
            additional_dices = await process(context, data, ignore_d20=True)
            await multiple_d20_text(context, dices['result_dies'][0].list_of_result, additional_dices, True)
        except:
            await multiple_d20_text(context, dices['result_dies'][0].list_of_result, data, True)
    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo \n"
            f"Voce tbm pode rolar com {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +d6+1")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_DISADVANTAGE,
    description="Roll dices with disadvantage?"
)
async def command_roll_disadvantage_dices(context, *args):
    try:
        data = ''.join(args)
        # Clean up
        if data == "d20":
            data = None
        else:
            data = data.replace("d20", "")

        dices = await calculate_dices(context, [[2, 20]], [], None)
        try:
            # Try to evaluate extra data
            additional_dices = await process(context, data, ignore_d20=True)
            await multiple_d20_text(context, dices['result_dies'][0].list_of_result, additional_dices, False)
        except:
            await multiple_d20_text(context, dices['result_dies'][0].list_of_result, data, False)
    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo \n"
            f"Voce tbm pode rolar com {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +d6+1")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_LUCK_DICE,
    description="Roll dices with LUCK?"
)
async def command_roll_luck_dices(context, data=None):
    try:
        for index, dice in enumerate(await process_luck_dice(context, data)):  # Parse and roll dices
            await send_roll_text(context, dice, True if index == 0 else False, False)

    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_LUCK_DICE} +2 por exemplo")
        await context.send(f"Exception {e}")


#============================================================================

@bot.command(
    name=COMMAND_RESET,
    description="Reset the initiative table"
)
async def roll_reset_initiative(context):
    await init_items.reset(context.channel.name)
    await context.send("OK, limpei a tabela. Bons dados :)")


@bot.command(
    name=COMMAND_REMOVE_INITIATIVE,
    description="Remove item from table"
)
async def remove_initiative(context, index=0):
    await init_items.remove_index(context.channel.name, index)
    await init_items.show(context.channel.name, context)


@bot.command(
    name=COMMAND_ADD_CONDITION_INITIATIVE,
    description="Add item from table"
)
async def add_condition_initiative(context, index, condition):
    await init_items.add_condition(context.channel.name, index, condition)
    await init_items.show(context.channel.name, context)


@bot.command(
    name=COMMAND_REMOVE_CONDITION_INITIATIVE,
    description="Remove item from table"
)
async def remove_initiative(context, index):
    await init_items.remove_condition(context.channel.name, index)
    await init_items.show(context.channel.name, context)


@bot.command(
    name=COMMAND_ROLL_INITIATIVE,
    description=""
)
async def roll_initiative(context, dex="", name_arg="", repeat=1):
    try:
        channel = context.channel.name
        if not dex:
            await init_items.show(context.channel.name, context)
            return

        for i in range(0, repeat):
            name = f"{name_arg}" if name_arg else context.message.author.display_name
            if repeat > 1:
                name += f"_{i+1}"

            dices = await calculate_dices(context, [[1, 20]], [], dex)
            await init_items.add(channel, name, dices['only_dices'], dex)
        await init_items.show(channel, context)

    except Exception as e:
        await context.send(f"Digite um numero (normalmente sua destreza). {dex} não é válido... ")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_INITIATIVE_ADV,
    description=""
)
async def roll_initiative_advantage(context, dex="", name_arg=""):
    try:
        if not dex:
            await init_items.show(context.channel.name, context)
            return

        name = f"{name_arg}" if name_arg else context.message.author.display_name

        dices = await calculate_dices(context, [[2, 20]], [], dex)

        await multiple_d20_text(context, dices['result_dies'][0].list_of_result, dex, True)
        await init_items.add(context.channel.name, name, dices['result_dies'][0].larger(), dex)
        await init_items.show(context.channel.name, context)

    except Exception as e:
        await context.send(f"Digite um numero (normalmente sua destreza). {dex} não é válido... ")
        await context.send(f"Exception {e}")
        raise


@bot.command(
    name=COMMAND_FORCE_INITIATIVE,
    description=""
)
async def force_initiative(context, number, dex="", name_arg=""):
    try:

        number, _ = await clean_dex(number)
        dex, neg = await clean_dex(dex)
        name = f"{name_arg}" if name_arg else context.message.author.display_name

        await init_items.add(context.channel.name, name, number, dex if not neg else dex*-1)
        await init_items.show(context.channel.name, context)

    except Exception as e:
        await context.send(f"Manda o comando direito mestre... ")
        await context.send(f"Exception {e}")


#  STATS  =========================================================================

@bot.command(
    name=COMMAND_SHOW_STATS_PLAYER,
    description="Show stats per player in the channel"
)
async def command_show_stats_player(context):
    try:
        await show_general_info(context)
    except Exception as e:
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_SHOW_STATS_SESSION,
    description="Show stats per channel (session)"
)
async def command_show_stats_session(context, date=None):
    try:
        print(f"date: {date}")
        await show_session_stats(bot, context, context.channel.name, date)
    except Exception as e:
        await context.send(f"Exception {e}")
        raise


@bot.command(
    name=COMMAND_HELPER,
    description="Show helpers menu"
)
async def command_helper(context):
    text = "``` COMO USAR \n"
    text += f" use {COMMAND_CHAR} ou {ALTERNATIVE_COMMAND_CHAR} para acionar + a tecla de comando por exemplo: \n"
    text += f" {COMMAND_ROLL}) {COMMAND_CHAR}{COMMAND_ROLL} 2d6+3 para rolar 2d6 e somar +3 ao resultado\n"
    text += f" {COMMAND_ROLL_ADVANTAGE}) {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +1 para rolar 2d20, pegar o maior numero e somar +1 ao resultado\n"
    text += f" {COMMAND_ROLL_DISADVANTAGE}) {COMMAND_CHAR}{COMMAND_ROLL_DISADVANTAGE} +1 para rolar 2d20, pegar o menor resultado somar +1 ao resultado\n"
    text += f" {COMMAND_HELPER}) {COMMAND_CHAR}{COMMAND_HELPER} mostra essa ajuda ```"

    await context.send(f"{text}")


@bot.event
async def on_ready():
    print(f"I'm logged in as {bot.user.name} !\n Statistics enable: {STATS_ENABLE}")


bot.run(DISCORD_TOKEN)
