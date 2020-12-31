#!/usr/bin/env python3

import json
from discord.ext import commands
import os
import random

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# read our environment variables
with open("./env.json", "r") as env:
    ENV = json.load(env)

COMMAND_CHAR = ENV['command_char']
ALTERNATIVE_COMMAND_CHAR = ENV['alternative_char']

COMMAND_ROLL = ENV['command_roll']

COMMAND_ROLL_ADVANTAGE = ENV["command_roll_advantage"]
COMMAND_ROLL_DISADVANTAGE = ENV["command_roll_disadvantage"]


COLORS = {
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "PURPLE": "\033[35m",
    "CYAN": "\033[36m",
    "GREY": "\033[37m",
    "WHITE": "\033[38m",
    "NEUTRAL": "\033[00m"
}

SIGN = (
    COLORS["RED"] + "/" +
    COLORS["YELLOW"] + "!" +
    COLORS["RED"] + "\\" +
    COLORS["NEUTRAL"] +
    " "
)


# read our discord access token
with open("secrets.json", "r") as secrets:
    DISCORD_TOKEN = json.load(secrets)["discord"]

bot = commands.Bot(
    command_prefix=[COMMAND_CHAR, ALTERNATIVE_COMMAND_CHAR],
    description="Roll a random dices, normal or with advantages/disadvantages"
)


async def parse_dices(data):
    import re
    return re.findall('(\d+)?d(\d+)?', data)


async def parse_additional(data):
    parsed_minus = data.split('-')
    minus = []
    for i in parsed_minus:
        try:
            if int(i) and i.find("+") == -1:
                minus.append(int(i))
        except:
            pass

    parsed_plus = data.split('+')
    plus = []
    for i in parsed_plus:
        try:
            if int(i) and i.find("-") == -1:
                plus.append(int(i))
        except:
            pass
    return {"minus": minus, "plus": plus}


async def roll_dice(times, dice):
    if int(times) > 10:
        times = 10

    return [random.randint(1, int(dice)) for _ in range(int(times))]


async def process(dices_data):
    dices = await parse_dices(dices_data)
    additional = await parse_additional(dices_data)

    result_dices_verbose = []
    only_dices = 0
    for number, dice in dices:
        number = number if number else 1
        results = await roll_dice(number, dice)
        only_dices += sum(results)
        result_dices_verbose.append({"verbose": f"{number}d{dice}",
                                     "list_of_result": results,
                                     "dice_base": dice,
                                     "result": sum(results),
                                     })

    result_final = only_dices
    for i in additional['plus']:
        result_final += i
    for i in additional['minus']:
        result_final -= i
    return result_dices_verbose, result_final, only_dices, additional


async def reroll_and_send_text(context, dices_data=None, adv=True):
    result = await roll_dice(2, 20)
    additional = {'plus': [], 'minus': []}
    if dices_data:
        additional = await parse_additional(dices_data)
    text = "1d20 => "
    dice_1 = dice_2 = ""
    if result[0] == 20 or result[0] == 1:
        dice_1 = "!"
    if result[1] == 20 or result[1] == 1:
        dice_2 = "!"

    if adv:
        if result[0] >= result[1]:
            text += f"[ {result[0]}{dice_1},  ~~{result[1]}{dice_2}~~ ]"
            result_final = result[0]
        else:
            text += f"[ ~~{result[0]}{dice_1}~~, {result[1]}{dice_2} ]"
            result_final = result[1]
    else:
        if result[0] <= result[1]:
            text += f"[ {result[0]}{dice_1}, ~~{result[1]}{dice_2}~~ ]"
            result_final = result[0]
        else:
            text += f"[ ~~{result[0]}{dice_1}~~, {result[1]}{dice_2} ]"
            result_final = result[1]

    final_text = f"{result_final} "
    for i in additional['plus']:
        result_final += i
        final_text += f"+ {i}"
    for i in additional['minus']:
        result_final -= i
        final_text += f"- {i}"

    if not additional['minus'] and not additional['plus']:
        final_text = ""
    else:
        final_text += " = "

    await context.send(f"{text} \n{final_text} **{result_final}**")


async def send_text(context, result):
    text = ""
    for dices in result[0]:

        text += f"``` {dices['verbose']}  => ["
        for index, dice in enumerate(dices['list_of_result']):
            comma = ""
            if index != len(dices['list_of_result']) -1:
                comma = ","
            bold = ""
            if dice == dices['dice_base'] or dice == 1:
                bold = "!"
            text += f" {dice}{bold}{comma}"
        text += " ]```"
        # {bold_conditional}{dices['result']}{bold_conditional}```"

    extra_text = ""
    if result[3]['plus']:
        for i in result[3]['plus']:
            extra_text = f" + {i} "

    if result[3]['minus']:
        for i in result[3]['minus']:
            extra_text += f" - {i} "
    only_dices = result[2]
    if not extra_text:
        await context.send(f"{text} \n **{result[1]}**")
    else:
        await context.send(f"{text} \n {only_dices}{extra_text}= **{result[1]}**")

# COMMANDS ================
@bot.command(
    name=COMMAND_ROLL,
    description="Roll dices?"
)
async def command_roll_dices(context, data):
    try:
        '''
            process("1d10+1d4-1")
            (['1d10 = [3]', '1d4 = [2]'], 4)
        '''
        result = await process(data) #  Parse and roll dices
        await send_text(context, result)

    except Exception as e:
        await context.send(f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL} 1d20+2 por exemplo")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_ADVANTAGE,
    description="Roll dices with advantage?"
)
async def command_roll_advantage_dices(context, data=None):
    try:
        await reroll_and_send_text(context, data, True)
    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_ADVANTAGE} +2 por exemplo")
        await context.send(f"Exception {e}")


@bot.command(
    name=COMMAND_ROLL_DISADVANTAGE,
    description="Roll dices with disadvantage?"
)
async def command_roll_disadvantage_dices(context, data=None):
    try:
        await reroll_and_send_text(context, data, False)
    except Exception as e:
        await context.send(
            f"Comando nao reconhecido, use: {COMMAND_CHAR}{COMMAND_ROLL_DISADVANTAGE} +2 por exemplo")
        await context.send(f"Exception {e}")

@bot.event
async def on_ready():
    print(
        COLORS["YELLOW"] +
        "I'm logged in as {name} !\n".format(name=bot.user.name) +
        COLORS["NEUTRAL"]
    )


bot.run(DISCORD_TOKEN)
