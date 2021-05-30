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
COMMAND_HELPER = ENV['command_helper']

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
    parsed_negative = re.findall('-(\d+)?d(\d+)?', data)
    parsed_positive = re.findall('(\d+)?d(\d+)?', data)
    for pn in parsed_negative:
        if pn in parsed_positive:
            parsed_positive.remove(pn)
    return  parsed_positive, parsed_negative


async def parse_repeat(data):
    import re
    return re.findall('(\d+)?x', data)


async def parse_additional(data, positive_dies, negative_dies):
    for item in positive_dies:
        dice = f"{item[0]}d{item[1]}"
        data = data.replace(f"+{dice}", "")
        if dice in data:
            data = data.replace(dice, "")

    for item in negative_dies:
        dice = f"{item[0]}d{item[1]}"
        data = data.replace(f"-{dice}", "")
        if dice in data:
            data = data.replace(dice, "")

    return data



async def roll_dice(times, dice):
    if int(times) > 20:
        times = 20

    return [random.randint(1, int(dice)) for _ in range(int(times))]


async def process(dices_data):
    repeat = await parse_repeat(dices_data)
    if repeat:
        repeat = int(repeat[0])
        dices_data = dices_data.split("x(")[1].replace(")", "")
    else:
        repeat = 1

    dices_positive, dices_negative = await parse_dices(dices_data)
    additional = await parse_additional(dices_data, dices_positive, dices_negative)
    dices_list = []
    for _ in range(0, repeat):
        dices_list.append(await calculate_dices(dices_positive, dices_negative, additional))
    return dices_list


async def calculate_dices(dices_positive, dices_negative, additional):
    result_sum_dies = []
    result_minus_dies = []
    only_dices = 0

    for number, dice in dices_positive:
        number = number if number else 1
        results = await roll_dice(number, dice)
        only_dices += sum(results)
        result_sum_dies.append({"verbose": f"{number}d{dice}",
                                "list_of_result": results,
                                "dice_base": dice,
                                "result": sum(results),
                               })

    for number, dice in dices_negative:
        number = number if number else 1
        results = await roll_dice(number, dice)
        only_dices -= sum(results)
        result_minus_dies.append({"verbose": f"{number}d{dice}",
                                  "list_of_result": results,
                                  "dice_base": dice,
                                  "result": sum(results),
                                  })

    additional_eval = 0
    if additional:
        additional_eval = eval(additional)

    dies_verbose = "".join([f"+{die['verbose']}" for die in result_sum_dies])
    dies_verbose += "".join([f"-{die['verbose']}" for die in result_minus_dies])

    return {"result_sum_dies": result_sum_dies,
            "result_minus_dies": result_minus_dies,
            "result_final": only_dices+additional_eval,
            "only_dices": only_dices,
            "additional": additional,
            "additional_eval": additional_eval,
            "dies_verbose": dies_verbose}


async def reroll_and_send_text(context, dices_data=None, adv=True):
    dice_result = await roll_dice(2, 20)

    try:
        text = f"{context.message.author.display_name}: 1d20 => "
    except:
        text = f" 1d20 => "

    dice_1 = dice_2 = ""
    if dice_result[0] == 20 or dice_result[0] == 1:
        dice_1 = "!"
    if dice_result[1] == 20 or dice_result[1] == 1:
        dice_2 = "!"

    if adv:
        if dice_result[0] >= dice_result[1]:
            text += f"[ {dice_result[0]}{dice_1},  ~~{dice_result[1]}{dice_2}~~ ]"
            result = dice_result[0]
        else:
            text += f"[ ~~{dice_result[0]}{dice_1}~~, {dice_result[1]}{dice_2} ]"
            result = dice_result[1]
    else:
        if dice_result[0] <= dice_result[1]:
            text += f"[ {dice_result[0]}{dice_1}, ~~{dice_result[1]}{dice_2}~~ ]"
            result = dice_result[0]
        else:
            text += f"[ ~~{dice_result[0]}{dice_1}~~, {dice_result[1]}{dice_2} ]"
            result = dice_result[1]

    if dice_result[0] == 1 and dice_result[1] == 1 or dice_result[0] == 20 and dice_result[1] == 20:
        text += f" ¯\_(ツ)_/¯ \n"

    extra_signal = "+" if dices_data and not "+" in dices_data and not "-" in dices_data else ""
    final_text = f"{result}{extra_signal}{dices_data}="
    result_final = result+eval(dices_data) if dices_data else result

    print(f"{text} \n{final_text} **{result_final}**")
    await context.send(f"{text} \n{final_text} **{result_final}**")


async def send_text(context, result, first=True):
    text = ""
    if first:
        text = f"{context.message.author.display_name}: "

    for dices in result['result_minus_dies'] + result['result_sum_dies']:

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

    if result['only_dices'] == 0:
        result['only_dices'] = ""

    print(f"{text} \n {result['only_dices']}{result['additional']}= **{result['result_final']}**")
    await context.send(f"{text} \n {result['only_dices']}{result['additional']}= **{result['result_final']}**")

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

        for index, dice in enumerate(await process(data)):   # Parse and roll dices
            await send_text(context, dice, True if index == 0 else False)

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
    print(
        COLORS["YELLOW"] +
        "I'm logged in as {name} !\n".format(name=bot.user.name) +
        COLORS["NEUTRAL"]
    )


bot.run(DISCORD_TOKEN)
