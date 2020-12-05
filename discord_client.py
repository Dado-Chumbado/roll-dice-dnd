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
COMMAND_ROLL_ADVANTAGE = ENV["command_roll_advantage"]
COMMAND_ROLL_DISADVANTAGE = ENV["command_roll_disavantage"]


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


# read our discord acces token
with open("secrets.json", "r") as secrets:
    DISCORD_TOKEN = json.load(secrets)["discord"]

bot = commands.Bot(
    command_prefix=COMMAND_CHAR,
    description="Roll a random dices, normal, with advantages or disadvantages"
)


def parse_dices(data):
    import re
    return re.findall('(\d+)?d(\d+)?', data)
    # ([+-]\d)?[^0-9d][+-]?[^0-9d]?


def parse_additional(data):
    parsed_minus = data.split('-')
    minus = []
    for i in parsed_minus:
        item = try_convert_to_int_or_pass(i)
        if item:
            minus.append(item)

    parsed_plus = data.split('+')
    plus = []
    for i in parsed_plus:
        item = try_convert_to_int_or_pass(i)
        if item:
            plus.append(item)
    return {"minus": minus, "plus": plus}


def try_convert_to_int_or_pass(data):
    try:
        return int(data)
    except:
        return None


def roll_dice(times, dice):
    return [random.randint(1, int(dice)) for _ in range(int(times))]


def process(dices_data):
    dices = parse_dices(dices_data)
    aditional = parse_additional(dices_data)
    result_dices_verbose = []
    result_dices = 0
    for number, dice in dices:
        results = roll_dice(number, dice)
        result_dices += sum(results)
        result_dices_verbose.append(f"{number}d{dice} = {results}")

    for i in aditional['plus']:
        result_dices += i
    for i in aditional['minus']:
        result_dices -= i
    return result_dices_verbose, result_dices


# COMMANDS ================
@bot.command(
    name=COMMAND_CHAR,
    description="!"
)
async def command_roll_dices(context, data):
    try:
        '''
            process("1d10+1d4-1")
            (['1d10 = [3]', '1d4 = [2]'], 4)
        '''
        result = process(data) #  Parse and roll dices
        text = ""
        for dice in result[0]:
            text += f"{dice}\n"
        text += f"**{result[1]}**"
        context.send(text)

    except Exception as e:
        await context.send(f"Comando nao reconhecido, use: 1d20+2 por exemplo")
        await context.send(f"Exception {e}")


@bot.event
async def on_ready():
    print(
        COLORS["YELLOW"] +
        "I'm logged in as {name} !\n".format(name=bot.user.name) +
        COLORS["NEUTRAL"]
    )


bot.run(DISCORD_TOKEN)
