#!/usr/bin/env python3

import json
from datetime import datetime
from discord.ext import commands
import discord
from get_file import rdm
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

COMMAND_CHAR = ENV['command_char']  # Command used to activate bot on discord


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
    description="Roll a random dices, normal, with advantages or disavantages"
)


def parse_dices(data):
    parsed = {}
    pre_parse = data.upper().replace(" ", "").split("D")
    if pre_parse[0] is None:
        pre_parse[0] = 1
        parsed['number_of_dices'] = pre_parse[0]
        parsed['dice'] = pre_parse[1]
    if pre_parse[1].find('+') > 0:
        parsed['effect'] = '+'
        parsed['value'] = pre_parse[1].split('+')[1]
        parsed['dice'] = pre_parse[1].split('+')[0]
    if pre_parse[1].find('-') > 0:
        parsed['effect'] = '-'
        parsed['value'] = pre_parse[1].split('-')[1]
        parsed['dice'] = pre_parse[1].split('-')[0]
    return parsed


def roll_dice(dice, times):
    return [random.randint(1, dice) for i in range(times)]


def process(dices_data):
    parsed = parse_dices(dices_data)
    result = roll_dice(parsed['number_of_dices'], parsed['dice'])})
    effect = parsed.get('effect'):
    if effect and effect == "+":
        total = result + parsed['value']
    if effect and effect == "-":
        total = result - parsed['value']
    return result


# COMMANDS ================
@bot.command(
    name=COMMAND_CHAR,
    description="!"
)
async def command_roll_dices(context, dex="", name_arg=""):
    try:
        dex = int(dex)
        name = name_arg if name_arg else context.message.author.display_name

        init_items.add(name, random.randint(1, 20), dex)
        await init_items.show(context)

    except Exception as e:
        await context.send(f"Digite um numero (normalmente sua destreza). {dex} não é válido... ")
        await context.send(f"Exception {e}")
                

@bot.event
async def on_ready():
    print(
        COLORS["YELLOW"] +
        "I'm logged in as {name} !\n".format(name=bot.user.name) +
        COLORS["NEUTRAL"]
    )


bot.run(DISCORD_TOKEN)
