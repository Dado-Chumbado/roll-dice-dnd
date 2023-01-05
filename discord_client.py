#!/usr/bin/env python3

import json
import os
import discord
from discord.ext import commands
from dices import process, calculate_dices
from initiative import InitTable, clean_dex
from roll_view import multiple_d20_text, get_roll_text
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

intents = discord.Intents.default()
intents.message_content = True
intents.message_content = True
bot = commands.Bot(command_prefix=[COMMAND_CHAR, ALTERNATIVE_COMMAND_CHAR],
                   description="Roll a random dices, normal or with advantages/disadvantages and control initiative table",
                   intents=intents)

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
        rr = None
        data = ''.join(args)
        if not data:
            data = "d20"
        if data[-2:] in ["r1", "r2", "r3"]:
            rr = data[-2:]
            data = data.split(data[-2:])[0]

        for index, dice in enumerate(await process(context, data, ignore_d20=False, reroll=rr)): # Parse and roll dices
            text, result_text, msg_result = await get_roll_text(context, dice, True if index == 0 else False)
            await context.message.author.send(f"{text}\n\n{result_text}{msg_result}")

    except Exception as e:
        await context.send(f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL} 1d20+2 por exemplo")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL,
    description="Roll dices?"
)
async def command_roll_dices(context, *args):
    try:
        rr = None
        data = ''.join(args)
        if not data:
            data = "d20"
        if data[-2:] in ["r1", "r2", "r3"]:
            rr = data[-2:]
            data = data.split(data[-2:])[0]

        for index, dice_list in enumerate(await process(context, data, ignore_d20=False, reroll=rr)): # Parse and roll dices
            text, result_text, msg_result = await get_roll_text(context, dice_list, True if index == 0 else False)
            await context.send(f"{text}\n\n{result_text}{msg_result}")

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
            data = ""
        data = data.replace("d20", "")
        data = await sanitize_input(data)

        dices = await calculate_dices(context, [[2, 20]], [], None, adv=True)
        text = ""
        try:
            # Try to evaluate extra data
            additional_dices = await process(context, data, ignore_d20=True)
            text = await multiple_d20_text(context, dices, additional_dices, True)
        except Exception as e:
            print(e)
            raise

        if text:
            await context.send(text)

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
            data = ""
        data = data.replace("d20", "")
        data = await sanitize_input(data)

        dices = await calculate_dices(context, [[3, 20]], [], None, adv=True)
        try:
            # Try to evaluate extra data
            additional_dices = await process(context, data, ignore_d20=True)
            text = await multiple_d20_text(context, dices, additional_dices, True)
        except:
            raise

        if text:
            await context.send(text)
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
        # SANITIZE STRING -> MOVE THIS
        if data == "d20":
            data = ""
        data = data.replace("d20", "")
        data = await sanitize_input(data)

        dices = await calculate_dices(context, [[2, 20]], [], None, adv=False)
        try:
            # Try to evaluate extra data
            additional_dices = await process(context, data, ignore_d20=True)
            text = await multiple_d20_text(context, dices, additional_dices, False)
        except:
            raise

        if text:
            await context.send(text)
    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo \n"
            f"Voce tbm pode rolar com {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +d6+1")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_LUCK_DICE,
    description="Roll dices with LUCK?"
)
async def command_roll_luck_dices(context, *args):
    data = ''.join(args)
    # SANITIZE STRING -> MOVE THIS
    if data == "d20":
        data = ""
    data = data.replace("d20", "")
    data = await sanitize_input(data)

    dices = await calculate_dices(context, [[1, 20]], [], None, luck=True)
    try:
        # Try to evaluate extra data
        additional_dices = await process(context, data, ignore_d20=True)
        text = await multiple_d20_text(context, dices, additional_dices, True)
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
async def add_condition_initiative(context, index, *args):
    data = ' '.join(args)
    await init_items.add_condition(context.channel.name, index, data)
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
async def roll_initiative(context, dex="", repeat=1, *args):
    try:
        data = ' '.join(args)
        channel = context.channel.name
        if not dex:
            await init_items.show(context.channel.name, context)
            return

        for i in range(0, repeat):
            name = f"{data}" if data else context.message.author.display_name
            if repeat > 1:
                name += f" {i+1}"

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
async def roll_initiative_advantage(context, dex="", *args):
    try:
        data = ' '.join(args)
        if not dex:
            await init_items.show(context.channel.name, context)
            return

        name = f"{data}" if data else context.message.author.display_name

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
async def force_initiative(context, dice, dex="", *args):
    try:
        data = ' '.join(args)
        dice, _ = await clean_dex(dice)
        dex, neg = await clean_dex(dex)
        name = f"{data}" if data else context.message.author.display_name

        await init_items.add(context.channel.name, name, dice, dex if not neg else dex*-1)
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
