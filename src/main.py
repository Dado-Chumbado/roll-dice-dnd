#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
STATS_ENABLE = os.getenv("save_stats_db")
COMMAND_CHAR = os.getenv("command_char")


intents = discord.Intents.default()
intents.message_content = True

# Create a bot instance
bot = commands.Bot(command_prefix=COMMAND_CHAR, intents=intents)

from commands import commands_setup
commands_setup(bot)


@bot.event
async def on_ready():
    print(f"I'm logged in as {bot.user.display_name} !\n Statistics enable: {STATS_ENABLE}.")


bot.run(os.getenv("discord_token"))
